import asyncio
import logging
import re
import threading
from urllib.parse import quote

from diff_match_patch import diff_match_patch
from liquid.ast import ChildNode, ParseTree
from liquid.expression import (
    AssignmentExpression,
    Blank,
    BooleanExpression,
    Continue,
    Empty,
    FilteredExpression,
    Identifier,
    InfixExpression,
    LoopExpression,
    Nil,
)

from llmstack.common.utils.liquid import env as liquid_env

logger = logging.getLogger(__name__)


def extract_nodes(node):
    nodes = []
    if isinstance(node, ParseTree):
        for stmt in node.statements:
            nodes.extend(extract_nodes(stmt) or [])
    elif isinstance(node, ChildNode):
        nodes.append(node)
        if node.node:
            nodes.extend(extract_nodes(node.node) or [])
    elif hasattr(node, "children"):
        for child in node.children():
            nodes.extend(extract_nodes(child) or [])
    return nodes


def extract_variables(expression):
    variables = []
    if expression is None:
        return []
    if isinstance(expression, Identifier):
        result = []
        for element in expression.path:
            if isinstance(element, Identifier):
                result.extend(extract_variables(element))
            else:
                result.append(element.value)
        return result
    if (
        isinstance(expression, Nil)
        or isinstance(expression, Empty)
        or isinstance(expression, Blank)
        or isinstance(expression, Continue)
    ):
        return []
    elif isinstance(expression, FilteredExpression):
        variables.extend(extract_variables(expression.expression))
    elif isinstance(expression, AssignmentExpression):
        variables.extend(extract_variables(expression.expression))
    elif isinstance(expression, LoopExpression):
        variables.extend(extract_variables(expression.iterable))
    elif isinstance(expression, BooleanExpression):
        variables.extend(extract_variables(expression.expression))
    elif isinstance(expression, InfixExpression):
        variables.extend([extract_variables(expression.left)])
        variables.extend([extract_variables(expression.right)])
    else:
        raise NotImplementedError(f"Unsupported expression: {expression} {type(expression)}")
    return variables


def run_coro_in_new_loop(coro):
    def start_loop(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_loop, args=(loop,))
    t.start()
    coro_future = asyncio.run_coroutine_threadsafe(coro, loop)

    coro_future.add_done_callback(lambda f: loop.stop())

    return coro_future


class ResettableTimer(threading.Thread):
    def __init__(self, interval, function, *args, **kwargs):
        super().__init__()
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.condition = threading.Condition()
        self.reset_flag = False
        self.stop_flag = False

    def run(self):
        with self.condition:
            while not self.stop_flag:
                self.condition.wait(self.interval)
                if self.stop_flag:
                    break
                if not self.reset_flag:
                    self.function(*self.args, **self.kwargs)
                    break
                self.reset_flag = False

    def reset(self):
        with self.condition:
            self.reset_flag = True
            self.condition.notify_all()

    def stop(self):
        with self.condition:
            self.stop_flag = True
            self.condition.notify_all()


def extract_variables_from_liquid_template(liquid_template):
    variables = []

    template = liquid_env.from_string(liquid_template)

    nodes = extract_nodes(template.tree)
    for node in nodes:
        extracted_variables = extract_variables(node.expression)
        if extracted_variables:
            if isinstance(extracted_variables[0], list):
                variables.extend(extracted_variables)
            else:
                variables.append(extracted_variables)

    return variables


# A utility function to recursively convert template vars of type
# _inputs[0].xyz to _inputs0.xyz for backward compatibility in a
# dictionary with nested string values
def convert_template_vars_from_legacy_format(d):
    if isinstance(d, dict):
        for key, value in d.items():
            if isinstance(value, dict):
                convert_template_vars_from_legacy_format(value)
            elif isinstance(value, list):
                for item in value:
                    convert_template_vars_from_legacy_format(item)
            elif isinstance(value, str):
                d[key] = re.sub(r"_inputs\[(\d+)\]", r"_inputs\1", value)
    elif isinstance(d, list):
        for item in d:
            convert_template_vars_from_legacy_format(item)
    elif isinstance(d, str):
        d = re.sub(r"_inputs\[(\d+)\]", r"_inputs\1", d)
    return d


class DiffMatchPatch:
    """
    A wrapper around diff_match_patch with fixes for handling unicode characters
    """

    def __init__(self):
        self._diff_match_patch = diff_match_patch()

    def diff_toDelta(self, diffs):
        """Crush the diff into an encoded string which describes the operations
        required to transform text1 into text2.
        E.g. =3\t-2\t+ing  -> Keep 3 chars, delete 2 chars, insert 'ing'.
        Operations are tab-separated.  Inserted text is escaped using %xx notation.
        Args:
        diffs: Array of diff tuples.
        Returns:
        Delta text.

        https://github.com/google/diff-match-patch/pull/80
        """
        text = []
        for op, data in diffs:
            if 0 == len(data):
                continue

            if op == self._diff_match_patch.DIFF_INSERT:
                # High ascii will raise UnicodeDecodeError.  Use Unicode instead.
                data = data.encode("utf-8")
                text.append("+" + quote(data, "!~*'();/?:@&=+$,# "))
            elif op == self._diff_match_patch.DIFF_DELETE:
                text.append("-%d" % (len(data.encode("utf-16-be")) // 2))
            elif op == self._diff_match_patch.DIFF_EQUAL:
                text.append("=%d" % (len(data.encode("utf-16-be")) // 2))
        return "\t".join(text)

    def to_delta(self, text1, text2):
        diffs = self._diff_match_patch.diff_main(text1, text2)
        return self.diff_toDelta(diffs)

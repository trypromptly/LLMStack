import asyncio
import re
import threading

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
from pydantic import BaseModel


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


def extract_jinja2_variables(input_data):
    def extract_from_string(s):
        # Define regular expression patterns to match Jinja2 elements, including
        # - variables: {{ variable_name }} or {{ variable_name | filter }}
        # - tags: {% tag_name %}
        variable_pattern = r"{{ *(.*?) *}}"
        tag_pattern = r"{% *(.*?) *%}"

        variables = set()

        # Find all variable matches
        variable_matches = re.findall(variable_pattern, s)
        for match in variable_matches:
            variables.add(match.strip().split("|")[0].strip())

        # Find all tag matches
        tag_matches = re.findall(tag_pattern, s)
        for match in tag_matches:
            # Split the tag content by space to determine its structure,
            # and add the variable depending on the tag
            split_tag = match.strip().split()
            if split_tag[0] in {"if", "elif"}:
                # In {% if x > y %}, {% if x == y %} or {% if x != y %},
                # extract both 'x' and 'y' as variables
                variables.update(re.findall(r"\b\w+\b", split_tag[1]))
            elif split_tag[0] == "for":
                # In {% for item in items %}, extract 'items' as a variable
                if len(split_tag) == 4 and split_tag[2] == "in":
                    variables.add(split_tag[3])

        return variables

    variables = set()

    if isinstance(input_data, str):
        variables.update(extract_from_string(input_data))
    elif isinstance(input_data, dict):
        for key, value in input_data.items():
            if isinstance(value, str):
                variables.update(extract_from_string(value))
            elif isinstance(value, dict):
                variables.update(extract_jinja2_variables(value))
            elif isinstance(value, list):
                variables.update(extract_jinja2_variables(value))
    elif isinstance(input_data, list):
        for item in input_data:
            variables.update(extract_jinja2_variables(item))
    elif isinstance(input_data, BaseModel):
        variables.update(extract_jinja2_variables(input_data.__dict__))

    return variables


def extract_variables_from_liquid_template(liquid_template):
    variables = []

    nodes = extract_nodes(liquid_template.tree)
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

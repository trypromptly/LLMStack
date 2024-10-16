import ast
import json
import logging
from urllib.parse import quote_plus

import lxml.etree as ET
from liquid import Environment
from lxml import html
from pydantic import BaseModel

# Add custom filters
env = Environment()
logger = logging.getLogger(__name__)


def todict(value):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return ast.literal_eval(value)
    except Exception:
        return {}


def to_string(value):
    return str(value)


def escape_unicode(value):
    if isinstance(value, str):
        return value.encode().decode("unicode_escape")
    elif isinstance(value, dict):
        return {k: escape_unicode(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [escape_unicode(v) for v in value]
    return value


def xpath_filter(xml_string, xpath_expr):
    # Parse the XML string
    try:
        root = ET.fromstring(xml_string)
    except ET.XMLSyntaxError as e:
        logger.exception(e)

        return xml_string

    # Apply the XPath expression
    try:
        filtered_elements = root.xpath(xpath_expr)
    except ET.XPathEvalError as e:
        logger.exception(e)
        return xml_string

    if len(filtered_elements) == 0:
        return ""

    if len(filtered_elements) == 1:
        return ET.tostring(filtered_elements[0]).decode("ascii")

    return list(map(lambda x: ET.tostring(x).decode("ascii"), filtered_elements))


def html_xpath_filter(html_string, xpath_expr):
    # Parse the HTML string
    try:
        root = html.fromstring(html_string)
    except ET.ParserError as e:
        logger.exception(f"Failed to parse HTML: {e}")
        return html_string

    # Apply the XPath expression
    try:
        filtered_elements = root.xpath(xpath_expr)
    except ET.XPathEvalError as e:
        logger.exception(f"Invalid XPath expression: {e}")
        return html_string

    if len(filtered_elements) == 0:
        return ""

    if len(filtered_elements) == 1:
        return _serialize_xpath_result(filtered_elements[0])

    return [_serialize_xpath_result(elem) for elem in filtered_elements]


def _serialize_xpath_result(result):
    if isinstance(result, str):
        return result
    elif isinstance(result, (int, float, bool)):
        return str(result)
    elif isinstance(result, ET._Element):
        return html.tostring(result, encoding="unicode")
    elif isinstance(result, ET._ElementUnicodeResult):
        return str(result)
    else:
        return repr(result)


env.add_filter("urlencode", quote_plus)
env.add_filter("tojson", json.dumps)
env.add_filter("to_json", json.dumps)
env.add_filter("todict", todict)
env.add_filter("to_dict", todict)
env.add_filter("escape_unicode", escape_unicode)
env.add_filter("tostring", to_string)
env.add_filter("to_string", to_string)
env.add_filter("xpath", xpath_filter)
env.add_filter("html_xpath", html_xpath_filter)


def render_template(template, data):
    return env.from_string(template).render(**data)


def hydrate_input(input, values):
    def render(value):
        if isinstance(value, str):
            try:
                return render_template(value, values)
            except Exception:
                logger.exception("Error rendering template when hydrating input")

        return value

    def traverse(obj):
        if isinstance(obj, dict):
            return {key: traverse(render(value)) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [traverse(render(item)) for item in obj]
        elif isinstance(obj, BaseModel):
            cls = obj.__class__
            return cls.model_validate(traverse(obj.model_dump()))
        elif isinstance(obj, str):
            return render(obj)
        return obj

    return traverse(input)

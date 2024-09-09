import ast
import json
from urllib.parse import quote_plus

from liquid import Environment

# Add custom filters
env = Environment()


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


env.add_filter("urlencode", quote_plus)
env.add_filter("tojson", json.dumps)
env.add_filter("to_json", json.dumps)
env.add_filter("todict", todict)
env.add_filter("to_dict", todict)
env.add_filter("escape_unicode", escape_unicode)
env.add_filter("tostring", to_string)
env.add_filter("to_string", to_string)


def render_template(template, data):
    return env.from_string(template).render(**data)

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


env.add_filter("urlencode", quote_plus)
env.add_filter("tojson", json.dumps)
env.add_filter("todict", todict)


def render_template(template, data):
    return env.from_string(template).render(**data)

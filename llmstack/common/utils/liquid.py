from urllib.parse import quote_plus

from liquid import Environment

# Add custom filters
env = Environment()

env.add_filter("urlencode", quote_plus)


def render_template(template, data):
    return env.from_string(template).render(**data)

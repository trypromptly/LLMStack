from llmstack.play.utils import extract_variables_from_liquid_template

# Define the Liquid template
liquid_template = """
{{ processor1.key1 }}
{% assign var = processor2.key1 | abs %}
{{var}}
{% for order in processor3.key1 %}
  {% if order.id == processor6.key1 %}
    {{ order.id }}
  {% endif %}
{% endfor %}
{% if processor4.key1 %}
    {{ processor4.key1 }}
{% else %}
    {{ processor5.key2 }}
{% endif %}
{{ processor7.key1[0].foo | default: "default" }}
"""

print(extract_variables_from_liquid_template(liquid_template))

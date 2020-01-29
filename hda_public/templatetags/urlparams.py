# Adds a new template tag to the Django templates for this app,
# as described here: https://stackoverflow.com/a/51377425/5111071
# This gives us a slightly easier way of writing URLs with multiple
# query string parameters in templates

from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag
def urlparams(*_, **kwargs):
    """
    A custom Django template tag for encoding URL query string parameters.
    Sourced from: https://stackoverflow.com/a/51377425/5111071
    Usage:

        {% load urlparams %}
        <a href="{% url 'videos:index'}{% urlparams page='1' tag='sometag' %}">Next</a>

    :return: the given keyword arguments encoded as a URL query string
    :rtype: str
    """
    non_empty = {k: v for k, v in kwargs.items() if v is not None}
    if non_empty:
        return '?{}'.format(urlencode(non_empty))
    return ''

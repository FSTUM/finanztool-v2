from collections import OrderedDict

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

LATEX_ESCAPES = OrderedDict(
    [
        ("\\", "\\textbackslash "),  # \ -> \textbackslash
        ("\n", "\\newline "),
        ("#", "\\# "),
        ("$", "\\$ "),
        ("%", "\\% "),
        ("&", "\\& "),
        ("^", "\\textasciicircum "),
        ("_", "\\textunderscore "),
        ("{", "\\{ "),
        ("}", "\\} "),
        ("~", "\\textasciitilde "),
        ("<", "\\textless "),
        (">", "\\textgreater "),
        ("€", "\\euro"),
    ],
)


@register.filter
@stringfilter
def latex_escape(value: str) -> str:
    """Escapes the text for LaTeX"""

    for string, replacement in LATEX_ESCAPES.items():
        value = value.replace(string, replacement)

    return value

from collections import OrderedDict

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def latexescape(value):
    """Escapes the text for LaTeX"""
    LATEX_ESCAPES = OrderedDict(
        [
            ("\\", "\\textbackslash "),  # \ -> \textbackslash
            ("\n", "\\newline "),
            ("#", "\\# "),
            ("$", "\\$ "),
            ("%", "\\% "),
            ("&", "\\& "),
            ("^", "\\textasciicircum "),
            ("_", "\\_ "),
            ("{", "\\{ "),
            ("}", "\\} "),
            ("~", "\\textasciitilde "),
            ("<", "\\textless "),
            (">", "\\textgreater "),
            ("€", "\\euro"),
        ],
    )

    for string, replacement in LATEX_ESCAPES.items():
        value = value.replace(string, replacement)

    return value

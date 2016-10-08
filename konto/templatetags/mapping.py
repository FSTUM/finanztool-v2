from django import template

register = template.Library()


@register.simple_tag
def checkbox(form, entry):
    key = form._get_key(entry)
    return form[key]

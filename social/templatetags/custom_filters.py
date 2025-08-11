from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def cut(value, arg):
    """Remove all values of arg from the given string"""
    return value.replace(arg, '')
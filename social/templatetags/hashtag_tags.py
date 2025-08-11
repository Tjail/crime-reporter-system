from django import template
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def link_hashtags(value):
    hashtag_pattern = re.compile(r"#(\w+)")
    linked_text = hashtag_pattern.sub(
        r'<a href="/social/explore?query=\1" class="text-decoration-none text-primary">#\1</a>',
        value
    )
    return mark_safe(linked_text)

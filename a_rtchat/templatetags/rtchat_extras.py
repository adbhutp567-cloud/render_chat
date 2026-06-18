from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key, 0)
    except Exception:
        return 0


@register.filter
def file_type(filename):
    """Return a simple file type: 'image', 'pdf', or 'other' based on filename."""
    if not filename:
        return 'other'
    name = filename.lower()
    if name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
        return 'image'
    if name.endswith('.pdf'):
        return 'pdf'
    return 'other'

from django import template
register = template.Library()


from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(key, [])
    return []  # ← None の場合は空リストを返す

# homework/templatetags/homework_extras.py

from django import template
from datetime import datetime, timedelta

register = template.Library()  # ✅ これを1回だけ宣言

@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return []
    return dictionary.get(key, [])

@register.filter
def add(value, days):
    try:
        date_value = datetime.strptime(value, "%Y-%m-%d").date()
        return (date_value + timedelta(days=int(days))).strftime('%Y-%m-%d')
    except:
        return value
    
@register.filter
def subject_color_class(subject_name):
    if not subject_name:
        return "subject-other"
    name = subject_name.lower()
    if "数" in name or "math" in name:
        return "subject-math"
    elif "国" in name or "japanese" in name:
        return "subject-japanese"
    elif "理" in name or "science" in name:
        return "subject-science"
    elif "社" in name or "social" in name:
        return "subject-social"
    elif "英" in name or "english" in name:
        return "subject-english"
    else:
        return "subject-other"

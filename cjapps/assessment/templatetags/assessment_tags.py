from django import template
import json
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def get_statement_rank(rankings, statement):
    """Get the rank for a specific statement from rankings data"""
    if rankings and isinstance(rankings, dict):
        return rankings.get(statement)
    return None

@register.filter
def parse_json(value):
    if value:
        return json.loads(value)
    return {'leftSide': [], 'rightSide': []}

@register.filter
def to_range(value):
    try:
        return range(int(value))
    except (TypeError, ValueError):
        return range(0)

@register.simple_tag
def get_cell_option(grid_options, row, col):
    for option in grid_options:
        if option.row == row and option.col == col:
            return option
    return None



from django.core.serializers.json import DjangoJSONEncoder

class FlashItemEncoder(DjangoJSONEncoder):
    def default(self, obj):
        return {
            'id': obj.id,
            'text': obj.text,
            'image': obj.image.url if obj.image else None
        }
    
@register.filter
def to_list(value):
    return list(value)

@register.filter
def jsonify(value):
    return json.dumps(value, cls=FlashItemEncoder)


@register.filter
def index(list_obj, i):
    """
    Get list item by index
    Usage: {{ list|index:i }}
    """
    try:
        return list_obj[i]
    except (IndexError, TypeError, KeyError):
        return ''
    
@register.filter
def get_range(value):
    return range(value)
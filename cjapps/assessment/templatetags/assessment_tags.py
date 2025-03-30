from django import template
import json
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def get_statement_rank(rankings, statement):
    if not rankings:
        return None
        
    # Handle when statement is directly the ID string
    if isinstance(statement, str):
        return rankings.get(statement)
        
    # Handle when statement is a dictionary object
    statement_id = statement.get('data', {}).get('originalId')
    return rankings.get(str(statement_id))

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

# @register.filter
# def get_item(dictionary, key):
#     return dictionary.get(key, 0)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, {})

@register.filter
def remove_strike(text):
    """Remove <s> and </s> tags from the text."""
    if text:
        return re.sub(r'</?s>', '', text)
    return text

@register.filter
def get_statement_rating(ratings, statement):
    if not ratings:
        return None
    # Handle statement as dictionary since it's coming from JSON data
    statement_id = statement.get('data', {}).get('originalId') or statement.get('originalId')
    return ratings.get(str(statement_id))

@register.filter
def get_statement_choice(choices, statement):
    if not choices:
        return False
    statement_id = statement.get('data', {}).get('originalId')
    return str(statement_id) in choices.values()

@register.filter
def get_group_rating(ratings, group_id):
    if not ratings:
        return None
    return ratings.get(str(group_id))

@register.filter
def get_statement_choice(choices_dict, statement):
    if isinstance(choices_dict, str):
        try:
            choices_dict = json.loads(choices_dict)
        except:
            choices_dict = {}
    
    if not choices_dict or not isinstance(choices_dict, dict):
        return False
        
    statement_id = statement.get('data', {}).get('originalId')
    return str(statement_id) in choices_dict.values()


@register.filter
def json_decode(value):
    if value:
        return json.loads(value)
    return {}

@register.filter
def startswith(text, starts):
    return text.startswith(starts)

@register.filter
def get_hotspot_by_id(hotspot_items, hotspot_id):
    if isinstance(hotspot_items, str):
        hotspot_items = json.loads(hotspot_items)
    return next((item for item in hotspot_items if item['hotspotId'] == hotspot_id), None)

@register.filter
def get_option_text(option_id, options):
    try:
        return options.get(id=option_id).text
    except:
        return "No option selected"

@register.filter
def calculate_percentage(value, total):
    """Calculate percentage of value out of total"""
    if not total or total == 0:
        return 0
    percentage = (float(value) / float(total)) * 100
    return round(percentage, 1)

@register.filter
def get_grid_option_by_id(grid_options, option_id):
    """Get grid option by ID"""
    for option in grid_options:
        if str(option.id) == str(option_id):
            return option
    return None

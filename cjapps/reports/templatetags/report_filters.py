from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter(is_safe=True)
def replace_placeholder(value, arg):
    """
    Replaces a placeholder with provided content.
    Usage: {{ text|replace_placeholder:'placeholder:replacement' }}
    """
    try:
        placeholder, replacement = arg.split('::', 1)
        return mark_safe(value.replace(placeholder, replacement))
    except ValueError:
        return value

@register.simple_tag
def replace_content(text, placeholder, replacement):
    """Replace placeholder with replacement in text"""
    if text and placeholder in text:
        return mark_safe(text.replace(placeholder, replacement))
    return mark_safe(text or '')


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    return dictionary.get(key)


@register.filter
def get_section_score(scores_dict, section_id):
    """Get a section score from the scores dictionary"""
    # Try to get score from section_X format
    section_key = f'section_{section_id}'
    if section_key in scores_dict:
        return round(scores_dict[section_key], 1)
    
    # Try direct section ID lookup
    if section_id in scores_dict:
        return round(scores_dict[section_id], 1)
    
    return 0

@register.filter
def calculate_overall_score(scores_dict):
    """Calculate the overall score as an average of all section scores"""
    if not scores_dict:
        return 0
    
    # Extract all section scores
    section_scores = []
    for key, value in scores_dict.items():
        # Check if key is a string and starts with 'section_', or if it's an integer
        if (isinstance(key, str) and key.startswith('section_')) or isinstance(key, int):
            section_scores.append(value)
    
    # Calculate average
    if section_scores:
        return round(sum(section_scores) / len(section_scores), 1)
    
    return 0


@register.filter
def get_question_options(question):
    """Get options for a question in a structured format"""
    if not question or not hasattr(question, 'question_type'):
        return []
    
    # For MCQ questions
    if question.question_type.startswith('mcq'):
        try:
            return question.options
        except:
            return []
    
    return []

@register.filter
def get_selected_option(answer_data):
    """Extract selected option ID from answer data"""
    if isinstance(answer_data, dict) and 'selected_option' in answer_data:
        return answer_data['selected_option']
    return None

@register.filter
def get_answer_text(answer_data):
    """Extract answer text from answer data for fill-in-the-blank questions"""
    if isinstance(answer_data, dict) and 'answer_text' in answer_data:
        return answer_data['answer_text']
    return ""

@register.filter
def get_selected_rating(answer_data):
    """Extract selected rating from answer data for psychometric questions"""
    if isinstance(answer_data, dict) and 'selected_rating' in answer_data:
        return answer_data['selected_rating']
    return None


@register.filter
def get_by_id(grid_options, option_id):
    """Find a grid option with matching ID"""
    try:
        # Convert to int if the ID is numeric
        option_id = int(option_id) if str(option_id).isdigit() else option_id
        
        for option in grid_options:
            if option.id == option_id:
                return option
        return None
    except (ValueError, AttributeError):
        return None

@register.filter
def get_hotspot_by_id(hotspot_items, hotspot_id):
    """Get hotspot information by ID from JSON field"""
    if not hotspot_items:
        return None
    
    try:
        # Parse JSON if it's a string
        if isinstance(hotspot_items, str):
            hotspot_items = json.loads(hotspot_items)
        
        # Find hotspot with matching ID
        for hotspot in hotspot_items:
            if str(hotspot.get('hotspotId')) == str(hotspot_id) or hotspot.get('hotspotId') == hotspot_id:
                return hotspot
        return None
    except (ValueError, TypeError, AttributeError):
        return None


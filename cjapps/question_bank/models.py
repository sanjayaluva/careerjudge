from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
User = get_user_model()
from django_quill.fields import QuillField
import re

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.name

class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq_text', 'Multiple Choice - Text-based'),
        ('mcq_image', 'Multiple Choice - Image-based'),
        ('mcq_mixed', 'Multiple Choice - Text-image mixed'),
        ('mcq_audio', 'Multiple Choice - Audio-based'),
        ('mcq_video', 'Multiple Choice - Video-based'),
        ('mcq_paragraph', 'Multiple Choice - Paragraph-based'),
        ('cus_hotspot_single', 'Multiple Choice - Hotspot Single Answer'),
        ('cus_hotspot_multiple', 'Multiple Choice - Hotspot Multiple Answers'),
        ('mcq_flash', 'Multiple Choice - Flash-based'),
        ('fib_text', 'Fill in the Blank - Text-based'),
        ('fib_image', 'Fill in the Blank - Image-based'),
        ('fib_audio', 'Fill in the Blank - Audio-based'),
        ('fib_video', 'Fill in the Blank - Video-based'),
        ('fib_paragraph', 'Fill in the Blank - Paragraph-based'),
        ('fib_flash', 'Fill in the Blank - Flash-based'),
        ('cus_grid', 'Grid List Selection Items'),
        ('cus_match', 'Match The Following'),
        ('psy_ranking', 'Psychometric Simple Ranking Scale'),
        ('psy_rank_n_rate', 'Psychometric First Rank-Then Rate Scale'),
        ('psy_rating', 'Psychometric Standard Rating Scale'),
        ('psy_forced_single', 'Psychometric Forced-Choice Scale – Single Level Rating'),
        ('psy_forced_two', 'Psychometric Forced-Choice Scale – Two-Level Rating'),
    ]

    DIFFICULTY_LEVELS = [
        ('veasy', 'Very Easy'),
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('vhard', 'Very Hard'),
    ]

    COGNITIVE_LEVELS = [
        ('knowledge', 'Knowledge'),
        ('comprehension', 'Comprehension'),
        ('application', 'Application'),
        ('analysis', 'Analysis'),
        ('synthesis', 'Synthesis'),
        ('evaluation', 'Evaluation'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('inactive', 'Inactive'),
    ]

    title = models.CharField(max_length=255)
    
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=20, choices=QUESTION_TYPES, null=True, blank=True)
    text = QuillField(null=True, blank=True)
    image = models.ImageField(upload_to='question_media/', null=True, blank=True)
    audio = models.FileField(upload_to='question_media/', null=True, blank=True)
    video = models.FileField(upload_to='question_media/', null=True, blank=True)
    paragraph = QuillField(null=True, blank=True) #models.TextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)
    is_multiple_answer = models.BooleanField(default=False)
    paragraph_interval = models.PositiveIntegerField(default=10, null=True, blank=True, help_text="Interval in seconds")

    flash_items_count = models.IntegerField(null=True, blank=True)
    flash_interval = models.PositiveIntegerField(default=5, null=True, blank=True, help_text="Interval in seconds")
    
    hotspot_items = models.JSONField(null=True, blank=True)
    negative_score = models.BooleanField(null=True, blank=True, default=False)

    grid_cols = models.IntegerField(null=True, blank=True)
    grid_rows = models.IntegerField(null=True, blank=True)
    grid_type = models.CharField(max_length=20, choices=[('text', 'Text'), ('image', 'Image')], default='text', null=True, blank=True)

    objectives = QuillField(null=True, blank=True) #models.TextField(_('Question Objective'), blank=True, null=True) 
    instructions = QuillField(null=True, blank=True) #models.TextField(null=True, blank=True)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, null=True, blank=True)
    case_sensitive = models.BooleanField(null=True, blank=True, default=False)
    cognitive_level = models.CharField(max_length=50, choices=COGNITIVE_LEVELS, default="knowledge", null=True, blank=True)
    exposure_limit = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    correct_score = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    incorrect_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    ranking_structure = models.JSONField(null=True, blank=True)
    
    items = models.JSONField(default=dict)
    scale_start = models.IntegerField(default=1)
    scale_end = models.IntegerField(default=5)

    def save_items(self, items_data):
        self.items = items_data
        self.save()

    def __str__(self):
        return self.title

    #@property
    def get_fib_options(self):
        if self.type.startswith('fib'):
            pattern = r'\{\{(.*?)\}\}'
            matches = re.findall(pattern, self.text.html)
            return matches
        return []

    def get_fib_info(self):
        """Extract FIB answers and prepare display text from curly brace patterns"""
        if not self.type.startswith('fib'):
            return [], ''

        import re
        text = self.text.html
        answers = []

        # Find all matches with curly braces pattern {{answer}}
        pattern = r'\{\{(.*?)\}\}' #r'\{([^}]+)\}'
        matches = re.finditer(pattern, text)
        
        # Extract answers and prepare display text
        display_text = text
        for match in matches:
            full_match = match.group(0)  # The full pattern including braces
            answer = match.group(1)      # Just the answer text inside braces
            answers.append(answer)
            # Replace the full pattern with placeholder
            display_text = display_text.replace(full_match, f'(_____)')

        return answers, display_text

    # def get_fib_info(self):
    #     if not self.type.startswith('fib'):
    #         return [], self.text.html

    #     pattern = r'\{(.*?)\}'
    #     text = self.text.html
    #     answers = []
    #     processed_text = text

    #     # Find all matches and collect answers
    #     matches = re.finditer(pattern, text)
    #     for match in matches:
    #         answer = match.group(1)
    #         answers.append(answer)
    #         # Replace pattern with [blank] for display
    #         processed_text = processed_text.replace(match.group(0), '[blank]')

    #     return answers, processed_text

    @property 
    def left_items(self):
        return self.match_options.all()

    @property
    def right_items(self):
        from random import shuffle
        items = list(self.match_options.all())
        shuffle(items)
        return items

class OptionItem(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='question_options/', null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

class GridOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='grid_options')
    row = models.IntegerField(null=True, blank=True)
    col = models.IntegerField(null=True, blank=True)
    text = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='question_grid/', null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

class FlashItem(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='flash_options')
    text = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to='question_flash/', null=True, blank=True)
    order = models.IntegerField(default=0)

    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

class MatchItem(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='match_options')
    left_item = models.CharField(max_length=255)
    right_item = models.CharField(max_length=255)

    # score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)


class PsyRatingItem(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='rating_options')
    text = models.CharField(max_length=255)
    value = models.IntegerField(default=0)



class PsyCategory(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class PsySubcategory(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(PsyCategory, related_name='subcategories', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class PsyStatement(models.Model):
    text = models.TextField()
    category = models.ForeignKey(PsyCategory, related_name='statements', on_delete=models.CASCADE, null=True, blank=True)
    subcategory = models.ForeignKey(PsySubcategory, related_name='statements', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.text

class PsyRankGroup(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

class PsyRankGroupStatement(models.Model):
    rank_group = models.ForeignKey(PsyRankGroup, related_name='statements', on_delete=models.CASCADE)
    statement = models.ForeignKey(PsyStatement, related_name='rank_groups', on_delete=models.CASCADE)
# forms.py
from django import forms
from .models import Question, OptionItem, FlashItem, MatchItem, GridOption #, RatingItem, RankingItem
import json
from django.utils.translation import gettext_lazy as _
from django_quill.forms import QuillFormField
from django_quill.fields import QuillField
from . import models

class QuestionBasicForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(QuestionBasicForm, self).__init__(*args, **kwargs)
        
        self.fields['title'].required = True
        self.fields['type'].required = True
        
        self.fields['flash_interval'].required = False
        self.fields['paragraph_interval'].required = False
        
        self.fields['forced_choice_subtype'].required = False
        self.fields['forced_choice_subtype'].widget.attrs['class'] = 'forced-choice-one-field'

        # edit mode
        instance = getattr(self, 'instance', None)
        self.is_edit_mode = instance and instance.pk is not None

        if self.is_edit_mode:
            self.fields['type'].disabled = True

            self.fields['grid_cols'].disabled = True
            self.fields['grid_rows'].disabled = True
            self.fields['grid_type'].disabled = True
        else:
            # self.fields['grid_cols'].disabled = False
            # self.fields['grid_rows'].disabled = False
            # self.fields['grid_type'].disabled = False

            self.fields['grid_cols'].initial = 1
            self.fields['grid_rows'].initial = 1
            self.fields['grid_type'].initial = 'text'
        
    class Meta:
        model = Question
        fields = [
            'title', 'type', 'instructions', 'objectives', 'exposure_limit', 'difficulty_level', 'cognitive_level', 'case_sensitive',
            'text', 'paragraph', 'image', 'audio', 'video', 'hotspot_items', 'grid_cols', 'grid_rows', 'grid_type', 'flash_items_count', 'flash_interval',
            'category', 'paragraph_interval', 'right_score', 'wrong_score', 'forced_choice_subtype'
        ]
        widgets = {
            'instructions': QuillFormField(),
            'objectives': QuillFormField(),

            'text': QuillFormField(),
            'paragraph': QuillFormField(),
            'hotspot_items': forms.HiddenInput(),

            'category': forms.HiddenInput(), #attrs={'class': 'rich-text-editor'}
        }
        help_texts = {
            "text": _("Note: Fill in the blank placeholder should be in the following format - {{ placeholder }}. Flash questions doesnot need placeholders."),
            "paragraph_interval": _("Note: specify in seconds."),
            "flash_interval": _("Note: specify in minutes."),
            "flash_items_count": _("How many items (words/images) should display from below list."),
        }

class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = OptionItem
        fields = ['text', 'image', 'is_correct']
        widgets = {
            'is_correct': forms.CheckboxInput(attrs={'class': 'single-checkbox'}),
        }

class FlashCardForm(forms.ModelForm):
    class Meta:
        model = FlashItem
        fields = ['text', 'image']

class MatchingPairForm(forms.ModelForm):
    class Meta:
        model = MatchItem
        fields = ['left_item', 'right_item']

class GridOptionForm(forms.ModelForm):
    class Meta:
        model = GridOption
        fields = ['row', 'col', 'text', 'image', 'is_correct']
        
class QuestionAnswerForm(forms.ModelForm):
    class Meta:
        model = OptionItem
        fields = ['text']
        widgets = {
            # 'answer': forms.Textarea(attrs={'rows': 5}),
        }


AnswerOptionFormSet     = forms.inlineformset_factory(Question, OptionItem, form=QuestionAnswerForm, extra=1, can_delete=False)
QuestionOptionFormSet   = forms.inlineformset_factory(Question, OptionItem, form=QuestionOptionForm, extra=1, can_delete=True)
FlashCardFormSet        = forms.inlineformset_factory(Question, FlashItem, form=FlashCardForm, extra=1, can_delete=True)
MatchingPairFormSet     = forms.inlineformset_factory(Question, MatchItem, form=MatchingPairForm, extra=1, can_delete=True)
GridOptionFormSet       = forms.inlineformset_factory(Question, GridOption, form=GridOptionForm, extra=0, can_delete=False)


class RatingItemForm(forms.ModelForm):
    class Meta:
        model = models.PsyRatingItem
        fields = ['text', 'value']
        widgets = {
            # 'answer': forms.Textarea(attrs={'rows': 5}),
        }


PsyRatingFormSet     = forms.inlineformset_factory(Question, models.PsyRatingItem, form=RatingItemForm, extra=0, can_delete=False)



# class RankingItemForm(forms.Form):
#     item = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
#     rank = forms.IntegerField(widget=forms.HiddenInput())

# class RankRateItemForm(forms.Form):
#     item = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
#     rank = forms.IntegerField(widget=forms.HiddenInput())
#     rating = forms.IntegerField(widget=forms.NumberInput(attrs={'min': 1, 'max': 5}))

# class RatingItemForm(forms.Form):
#     item = forms.CharField(widget=forms.TextInput(attrs={})) #'readonly': 'readonly'
#     rating = forms.IntegerField(widget=forms.NumberInput(attrs={'min': 1, 'max': 5}), initial=1)

# class ForcedChoiceSingleForm(forms.Form):
#     left_option = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
#     right_option = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
#     choice = forms.ChoiceField(choices=[('left', 'Left'), ('right', 'Right')], widget=forms.RadioSelect)

# class ForcedChoiceTwoForm(forms.Form):
#     left_option = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
#     right_option = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))
#     choice = forms.ChoiceField(choices=[('left', 'Left'), ('right', 'Right')], widget=forms.RadioSelect)
#     left_rating = forms.IntegerField(widget=forms.NumberInput(attrs={'min': 1, 'max': 5}))
#     right_rating = forms.IntegerField(widget=forms.NumberInput(attrs={'min': 1, 'max': 5}))

# # RankingFormSet = forms.formset_factory(RankingItemForm, extra=0)
# RankRateFormSet = forms.formset_factory(RankRateItemForm, extra=0)
# RatingFormSet = forms.formset_factory(RatingItemForm, extra=0)
# ForcedChoiceSingleFormSet = forms.formset_factory(ForcedChoiceSingleForm, extra=0)
# ForcedChoiceTwoFormSet = forms.formset_factory(ForcedChoiceTwoForm, extra=0)
from django import forms
from django_quill.forms import QuillFormField
from .models import Assessment#, Variable, Score, QuestionAssignment, DisplayParameters
from question_bank.models import Question, Category

# from crispy_forms.helper import FormHelper
# from crispy_forms.layout import Layout, Div, Fieldset, Submit, ButtonHolder

class AssessmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['objective'].required = False
        self.fields['description'].required = False
        self.fields['instructions'].required = False
        self.fields['description_img'].label = 'Description Image'
        self.fields['instructions_img'].label = 'Instructions Image'
        self.fields['display_order'].required = False
        self.fields['duration_minutes'].required = False

        # edit mode
        instance = getattr(self, 'instance', None)
        self.is_edit_mode = instance and instance.pk is not None

        if self.is_edit_mode:
            self.fields['title'].disabled = True


    class Meta:
        model = Assessment
        fields = ['title', 'objective', 'description', 'instructions', 'description_img', 'instructions_img', 'display_order', 'duration_minutes' ]
        widgets = {
            'objective': QuillFormField(),
            'description': QuillFormField(),
            'instructions': QuillFormField(),
            'display_order': forms.Select(
                choices=Assessment.PRESENTATION_CHOICES,
                attrs={'class': 'form-control form-control-sm mb-2'}
            )
        }


class QuestionSearchForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, empty_label="-- Category --")

    class Meta:
        model = Question
        fields = ['title', 'type', 'category', 'difficulty_level', 'cognitive_level', 'exposure_limit']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False
            self.fields[field].widget.attrs.update({'class': 'form-control form-control-sm mb-2'})
            self.fields[field].widget.attrs.update({'placeholder': self.fields[field].label})
        
        self.fields['type'].choices = [('', '-- Question Type --')] + list(self.fields['type'].choices)[1:]
        self.fields['difficulty_level'].choices = [('', '-- Difficulty Level --')] + list(self.fields['difficulty_level'].choices)[1:]
        self.fields['cognitive_level'].choices = [('', '-- Cognitive Level --')] + list(self.fields['cognitive_level'].choices)[1:]

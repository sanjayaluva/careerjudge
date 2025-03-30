from django import forms
from django.forms import inlineformset_factory
from .models import ReportConfiguration, Cutoff, Band, ContrastVariable, TypeBand, AssessmentBooking
from assessment.models import Assessment, Section
from django.contrib.auth import get_user_model
from django_quill.forms import QuillFormField
from django_quill.widgets import QuillWidget

User = get_user_model()

class ReportConfigurationForm(forms.ModelForm):
    objectives = QuillFormField(required=False)
    description = QuillFormField(required=False)
    
    # Change widget from CheckboxSelectMultiple to Select with select2 class
    score_level = forms.MultipleChoiceField(
        choices=ReportConfiguration.SCORE_LEVELS,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=True,
        help_text="Select which levels of scores to include in the report"
    )
    
    # Change widget from RadioSelect to Select with select2 class
    score_conversion = forms.ChoiceField(
        choices=ReportConfiguration.SCORE_CONVERSION,
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=True,
        help_text="Select the score conversion method"
    )

    type_code_count = forms.IntegerField(
        required=False,  # This makes it optional
        min_value=1,
        max_value=10,
        initial=4,
        help_text="Number of contrast variables to include in type code"
    )
    
    class Meta:
        model = ReportConfiguration
        fields = ['title', 'description', 'description_img', 'assessment', 
                  'report_type', 'score_level', 'score_conversion', 'objectives', 'type_code_count', 'is_default']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': QuillWidget(),
            'description_img': forms.FileInput(attrs={'class': 'form-control'}),
            'assessment': forms.Select(attrs={'class': 'form-control select2'}),
            'report_type': forms.Select(attrs={'class': 'form-control select2'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'type_code_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # Filter assessments created by the user
            self.fields['assessment'].queryset = Assessment.objects.filter(created_by=user)

        # Set default score_conversion to 'percentage' for new forms
        if not self.instance.pk:  # This checks if it's a new form (not editing)
            self.fields['score_conversion'].initial = 'percentage'

        # Set initial values for existing instance
        if self.instance and self.instance.pk:
            if isinstance(self.instance.score_level, list):
                self.initial['score_level'] = self.instance.score_level

        # Add help text
        self.fields['type_code_count'].help_text = "Number of contrast variables to include in personality type code"
        
        # Show/hide fields based on report type
        if self.instance.pk and self.instance.report_type:
            if self.instance.report_type != 'typological':
                self.fields['type_code_count'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        report_type = cleaned_data.get('report_type')
        assessment = cleaned_data.get('assessment')
        
        if assessment and report_type:
            # Validate report type based on assessment type
            if report_type == 'typological' and assessment.type != 'psychometric':
                self.add_error('report_type', 'Typological reports are only available for psychometric assessments.')
            
            elif report_type == 'question_level' and assessment.type != 'normal':
                self.add_error('report_type', 'Question Level reports are only available for normal assessments.')
        
        return cleaned_data

class CutoffForm(forms.ModelForm):
    above_cutoff_description = QuillFormField(required=False)
    below_cutoff_description = QuillFormField(required=False)
    
    class Meta:
        model = Cutoff
        fields = [
            'configuration', 'assessment_section', 'cutoff_score', 'cutoff_label',
            'above_cutoff_description', 'below_cutoff_description'
        ]
        widgets = {
            'configuration': forms.HiddenInput(),
            'assessment_section': forms.HiddenInput(),
            'cutoff_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'cutoff_label': forms.TextInput(attrs={'class': 'form-control'}),
        }

class BandForm(forms.ModelForm):
    description = QuillFormField(required=False)
    
    class Meta:
        model = Band
        fields = [
            'configuration', 'assessment_section', 'name', 'min_range', 'max_range',
            'color', 'label', 'description'
        ]
        widgets = {
            'configuration': forms.HiddenInput(),
            'assessment_section': forms.HiddenInput(),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'min_range': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'max_range': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'color': forms.TextInput(attrs={'class': 'form-control color-picker'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
        }

class TypeBandForm(forms.ModelForm):
    class Meta:
        model = TypeBand
        fields = ['configuration', 'contrast_variable', 'name', 'min_range', 'max_range', 'color', 'label', 'description']
        widgets = {
            'configuration': forms.HiddenInput(),
            'contrast_variable': forms.HiddenInput(),
            
            'description': QuillWidget(),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

class ContrastVariableForm(forms.ModelForm):
    class Meta:
        model = ContrastVariable
        fields = ['configuration', 'subcategory', 'name', 'code', 'color', 'description']
        widgets = {
            'configuration': forms.HiddenInput(),
            'subcategory': forms.HiddenInput(),

            'description': QuillWidget(),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

# Create a separate form for candidate selection
class CandidateSelectionForm(forms.Form):
    candidates = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        assessment = kwargs.pop('assessment', None)
        super().__init__(*args, **kwargs)
        
        if assessment:
            # Filter candidates who have completed the assessment
            from assessment.models import AssessmentSession
            completed_sessions = AssessmentSession.objects.filter(
                assessment=assessment,
                status='completed'
            ).values_list('user_id', flat=True)
            
            self.fields['candidates'].queryset = User.objects.filter(
                id__in=completed_sessions
            ).order_by('last_name', 'first_name')

class AssessmentBookingForm(forms.ModelForm):
    class Meta:
        model = AssessmentBooking
        fields = ['assessment', 'report_count']
        widgets = {
            'assessment': forms.Select(attrs={'class': 'form-control select2'}),
            'report_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(AssessmentBookingForm, self).__init__(*args, **kwargs)
        
        if user:
            # Only show published assessments
            self.fields['assessment'].queryset = Assessment.objects.filter(published=True)


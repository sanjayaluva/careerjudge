from django import forms
from .models import Task
from django.contrib.auth import get_user_model

User = get_user_model()

# class TaskCreationForm(forms.ModelForm):
    
#     # def __init__(self, *args, **kwargs):
#     #     self.from_user = kwargs.pop('from_user', None)
#     #     super().__init__(*args, **kwargs)

#     sme_user = forms.ModelChoiceField(
#         queryset=User.objects.filter(role=User.SME), 
#         label="SME User"
#     )
#     reviewer_user = forms.ModelChoiceField(
#         queryset=User.objects.filter(role=User.REVIEWER), 
#         label="Reviewer User"
#     )
#     psychometrician_user = forms.ModelChoiceField(
#         queryset=User.objects.filter(role=User.PSYCHOMETRICIAN), 
#         label="Psychometrician User"
#     )

#     due_date = forms.DateField(
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         label='Due Date',
#         required=False
#     )

#     description = forms.CharField(
#         widget=forms.Textarea(attrs={'rows': 8}),
#         required=True
#     )


#     class Meta:
#         model = Task
#         exclude = ['from_user', 'status']  # Exclude these fields from form
#         # fields = '__all__' 
#         # [
#         #     'name', 'type', 'description', 
#         #     'sme_user', 'reviewer_user', 'psychometrician_user', 
#         #     'due_date', 'metadata'
#         # ]
#         # widgets = {
#         #     # 'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
#         #     # 'description': forms.Textarea(attrs={'rows': 8}),
#         #     # 'metadata': forms.Textarea(attrs={'rows': 3}),
#         #     # 'dob': forms.DateInput(attrs={'type':'date'}),
#         # }

#       def save(self, commit=True):
#         task = super().save(commit=False)
#         task.from_user = self.initial.get('from_user')
#         task.status = Task.PENDING  # Set default status
#         if commit:
#             task.save()
#         return task

# class TaskCreationForm(forms.ModelForm):
#     class Meta:
#         model = Task
#         fields = ['name', 'assigned_to']

# class ReviewForm(forms.Form):
#     rating = forms.IntegerField(min_value=1, max_value=5, required=True)
#     comments = forms.CharField(widget=forms.Textarea, required=True)

# class RejectForm(forms.Form):
#     comments = forms.CharField(widget=forms.Textarea, required=True)


class TaskCreationForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'description', 'task_type', 'question_type', 'number_of_questions', 
                 'sme_user', 'reviewer_user', 'psychometrician_user']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'number_of_questions': forms.NumberInput(attrs={'min': 1}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sme_user'].queryset = User.objects.filter(role=User.SME)
        self.fields['reviewer_user'].queryset = User.objects.filter(role=User.REVIEWER)
        self.fields['psychometrician_user'].queryset = User.objects.filter(role=User.PSYCHOMETRICIAN)

# class ReviewForm(forms.Form):
#     rating = forms.IntegerField(min_value=1, max_value=5)
#     comments = forms.CharField(widget=forms.Textarea)
#     approve = forms.BooleanField(required=False)    # rejection_reason = forms.CharField(widget=forms.Textarea, required=False)

class ReviewForm(forms.Form):
    DECISION_CHOICES = (
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    )
    
    decision = forms.ChoiceField(choices=DECISION_CHOICES)
    rating = forms.IntegerField(required=False, min_value=1, max_value=5)
    comments = forms.CharField(widget=forms.Textarea, required=False)

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get('decision')
        rating = cleaned_data.get('rating')
        comments = cleaned_data.get('comments')

        if decision == 'approve' and not rating:
            raise forms.ValidationError('Rating is required when approving')
            
        if decision == 'reject' and not comments:
            raise forms.ValidationError('Comments are required when rejecting')

        return cleaned_data

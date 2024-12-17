from django import forms
from . import models
from django.db import models as dbmodels
from django.contrib.auth import get_user_model
User = get_user_model()

import datetime
from django.http import request

from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
# from django.db import transaction
from django.forms import inlineformset_factory
from django.forms import formset_factory

class TrainingContentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TrainingContentForm, self).__init__(*args, **kwargs)

        # self.fields['file'].label = False
        # self.fields['type'].label = False
        # self.fields['delete'].label = False
        self.label_suffix = None

    class Meta:
        model = models.Content
        fields = ['type', 'file', 'session']
        widgets = {
            'type' : forms.HiddenInput(attrs={'value' : ''}), #
            'session' : forms.HiddenInput(attrs={'value' : ''}), #
        }

class TrainingAssignmentForm(forms.ModelForm):
    # def __init__(self, *args, **kwargs):
    #     super(TrainingAssignmentForm, self).__init__(*args, **kwargs)

    #     # self.fields['file'].label = False
    #     # self.fields['type'].label = False
    #     # self.fields['delete'].label = False
    #     self.label_suffix = None

    class Meta:
        model = models.Assignment
        fields = ['title', 'desc', 'submit_report', 'mandatory']
        widgets = {
            'desc' : forms.Textarea(attrs={'rows' : '3'}),
            # 'type' : forms.HiddenInput(attrs={'value' : ''}), #
            # 'session' : forms.HiddenInput(attrs={'value' : ''}), #
        }

class TrainingLiveSessionForm(forms.ModelForm):
    class Meta:
        model = models.Session
        fields = ['name', 'objectives', 'duration', 'duration_type'] #, 'start_time', 'end_time'
        widgets = {
            'objectives' : forms.Textarea(attrs={'rows' : '3'}),
            # 'start_time': forms.DateTimeInput(attrs={'type':'datetime-local'}),
            # 'end_time': forms.DateTimeInput(attrs={'type':'datetime-local'}),
        }

TrainingAssignmentLinkFormset = inlineformset_factory(
    models.Assignment, 
    models.Link, 
    # form=TrainingAssignmentForm, 
    exclude=[],
    extra=1, 
    can_delete=False
)

TrainingContentFormset = inlineformset_factory(
    models.Session, 
    models.Content, 
    form=TrainingContentForm, 
    extra=1, 
    can_delete=True
)

class ScheduleTrainingForm(forms.ModelForm):
    # notification_id = dbmodels.CharField(max_length=100)

    class Meta:
        model = models.TrackLivesession
        fields = ['start_time', 'duration']
        widgets = {
            # 'notification_id' : forms.HiddenInput(), #attrs={'rows' : '3'}
            'start_time': forms.DateTimeInput(attrs={'type':'datetime-local', 'required': 'required'}),
            # 'duration': forms.DateTimeInput(attrs={'type':'datetime-local', 'required': 'required'}),
        }

# class TrainingAssignmentForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super(TrainingAssignmentForm, self).__init__(*args, **kwargs)
#         self.label_suffix = None

#     class Meta:
#         model = models.Assignment
#         fields = ['title', 'submit_report', 'desc']
#         widgets = {
#             'desc' : forms.Textarea(attrs={'rows' : '3'}),
#         }

class TrainingAssignmentFormSetClass(forms.BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.queryset = Author.objects.filter(name__startswith="O")
    
    def add_fields(self, form, index):
        super().add_fields(form, index)
        # form.fields["links"] = forms.Widget()

# class BaseAuthorFormSet(BaseModelFormSet):

# TrainingAssignmentFormset = inlineformset_factory(
#     models.Training, 
#     models.Assignment, 
#     form=TrainingAssignmentForm, 
#     formset=TrainingAssignmentFormSetClass,
#     extra=1, 
#     can_delete=True
# )


class TrainingSessionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TrainingSessionForm, self).__init__(*args, **kwargs)
        self.label_suffix = None

    class Meta:
        model = models.Session
        fields = ['name', 'duration', 'duration_type', 'objectives', 'live'] #'start_time', 'end_time', , 'summary'
        widgets = {
            'objectives' : forms.Textarea(attrs={'rows' : '3'}),
            # 'start_time': forms.DateTimeInput(attrs={'type':'datetime-local'}),
            # 'end_time': forms.DateTimeInput(attrs={'type':'datetime-local'}),
        }

# TrainingSessionFormset = inlineformset_factory(
#     models.Node, 
#     models.Session, 
#     form=TrainingSessionForm, 
#     exclude=[],
#     extra=1, 
#     can_delete=True
# )

class TrainingForm(forms.ModelForm):
    # use_required_attribute = False

    def __init__(self, *args, **kwargs):
        super(TrainingForm, self).__init__(*args, **kwargs)

        # self.fields['duration'].required = True
        # self.fields['duration_type'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        type = cleaned_data.get("type")
        duration = cleaned_data.get("duration")
        duration_type = cleaned_data.get("duration_type")

        if type == self.instance.TYPE_SCHEDULED:
            if not duration and duration_type:
                raise ValidationError("Duration field is required for scheduled trainings.")
        
        # return cleaned_data

    # def clean_duration(self):
    #     i = 0
    #     pass
        
    class Meta:
        model = models.Training
        # fields = '__all__'
        fields = ['title', 'type', 'duration', 'duration_type', 'objectives', 'desc_text', 'desc_img', 'category', 'amount']
        widgets = {
            'objectives': forms.Textarea(attrs={'rows' : '4'}),
            'desc_text': forms.Textarea(attrs={'rows' : '4'}),
        }

class StructureForm(forms.Form):
    pass
    # class Meta:
    #     model = models.Training
    #     # fields = '__all__'
    #     fields = ['title', 'type', 'duration', 'duration_type', 'objectives', 'desc_text', 'desc_img', 'category', 'amount']
    #     widgets = {
    #         'objectives': forms.Textarea(attrs={'rows' : '3'}),
    #         'desc_text': forms.Textarea(attrs={'rows' : '3'}),
    #     }

class ContentForm(forms.ModelForm):
    class Meta:
        model = models.Content
        fields = '__all__'

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = models.Assignment
        fields = '__all__'
        # widgets = {
        #     'size': forms.TextInput(
        #         attrs={
        #             'class': 'form-control'
        #             }
        #         ),
        #     'quantity': forms.NumberInput(
        #         attrs={
        #             'class': 'form-control'
        #             }
        #         ),
        #     'price': forms.NumberInput(
        #         attrs={
        #             'class': 'form-control'
        #             }
        #         ),
        # }

class LinkForm(forms.ModelForm):
    class Meta:
        model = models.Link
        fields = '__all__'

class BookingForm(forms.ModelForm):
    class Meta:
        model = models.Booking
        fields = ['category', 'training', 'start_date']
        widgets = {
            'start_date': forms.DateInput(), #attrs={'type':'date'} attrs={'required':'required'}
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(BookingForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        # self.fields['training'].queryset = User.objects.none()
        # self.fields['counselee'].queryset = User.objects.filter(pk=self.user.id)
        # self.fields['counsellor'].empty_label = None
        # self.fields['counselee'].empty_label = None
        # self.fields['counselee'].readonly = True
        # self.fields['user'].queryset = User.objects.filter(pk=self.user.id)
        # self.fields['timeslot'].choices =  []
        # self.timeslots = models.TIME_SLOTS
        

    def clean_booked(self, *args, **kwargs):
        return datetime.datetime.now()

    # def clean_date(self, *args, **kwargs):
    #     availId = self.cleaned_data['date']
    #     # avail, slot = timeslot_data.split('-')
    #     date = models.Availability.objects.get(pk=availId).date
    #     return date

    # def clean_timeslot(self, *args, **kwargs):
    #     timeslot_data = self.cleaned_data['timeslot']
    #     # avail, slot = timeslot_data.split('-')
    #     # date = models.Availability.objects.get(pk=avail).date
    #     return timeslot_data

    # def clean_counselee(self, *args, **kwargs):
    #     uid = self.cleaned_data['counselee']
    #     # u = User.objects.get(pk=uid)
    #     return uid

    # def clean_counsellor(self, *args, **kwargs):
    #     uid = self.cleaned_data['counsellor']
    #     u = User.objects.get(pk=uid)
    #     return u

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean()
        i=0

        # if len(password1) < 8:
        #     raise ValidationError("Password should be minimum 8 characters long.")

        # return super(BookingForm, self).clean(*args, **kwargs)

    # @transaction.atomic()
    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.status = models.Booking.STATUS_BOOKED
        booking.user = self.user
        
        if commit:
            booking.save()

        return booking



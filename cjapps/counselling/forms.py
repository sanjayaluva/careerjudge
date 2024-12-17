from django import forms
from . import models
# from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

import datetime
from django.http import request

from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
# from django.db import transaction


User = get_user_model()

class CounsellingCancelForm(forms.ModelForm):
    class Meta:
        model = models.Booking
        fields = ['reason']
        widgets = {
            'reason' : forms.Textarea(attrs={'rows' : '5'}),
        }

class BookingForm(forms.ModelForm):
    # counselee = forms.ModelChoiceField(queryset=None
    #     # max_length=3,
    #     # widget=forms.Select(choices=None),
    # )
    counsellor = forms.CharField(widget=forms.Select(choices=[]))
    timeslot = forms.CharField(widget=forms.Select(choices=[]))
    date = forms.CharField(widget=forms.Select(choices=[]))
    booked = forms.CharField(required=False)

    class Meta:
        model = models.Booking
        fields = ['counselee', 'category', 'counsellor', 'timeslot', 'topic', 'date', 'booked'] #
        # [
        #     'first_name',
        #     # 'middle_name',
        #     'last_name',
        #     'email',
        #     # 'password',
        # ]
        widgets = {
            'topic' : forms.Textarea(attrs={'rows':'3'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(BookingForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['counsellor'].queryset = User.objects.none()
        self.fields['counselee'].queryset = User.objects.filter(pk=self.user.id)
        self.fields['counsellor'].empty_label = None
        self.fields['counselee'].empty_label = None
        # self.fields['counselee'].readonly = True
        
        self.fields['timeslot'].choices =  []
        self.timeslots = models.TIME_SLOTS
        

    def clean_booked(self, *args, **kwargs):
        return datetime.datetime.now()

    def clean_date(self, *args, **kwargs):
        availId = self.cleaned_data['date']
        # avail, slot = timeslot_data.split('-')
        date = models.Availability.objects.get(pk=availId).date
        return date

    def clean_timeslot(self, *args, **kwargs):
        timeslot_data = self.cleaned_data['timeslot']
        # avail, slot = timeslot_data.split('-')
        # date = models.Availability.objects.get(pk=avail).date
        return timeslot_data

    def clean_counselee(self, *args, **kwargs):
        uid = self.cleaned_data['counselee']
        # u = User.objects.get(pk=uid)
        return uid

    def clean_counsellor(self, *args, **kwargs):
        uid = self.cleaned_data['counsellor']
        u = User.objects.get(pk=uid)
        return u

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
        
        # # user.is_student = True
        # user.role = User.INDIVIDUAL
        # user.first_name = self.cleaned_data.get("first_name")
        # user.last_name = self.cleaned_data.get("last_name")
        # # user.gender = self.cleaned_data.get("gender")
        # # user.address = self.cleaned_data.get("address")
        # # user.phone = self.cleaned_data.get("phone")
        # # user.contact_address = self.cleaned_data.get("address")
        # user.email = self.cleaned_data.get("email")
        # user.email_is_verified = False

        # # Generate a username based on first and last name and registration date
        # # registration_date = datetime.now().strftime("%Y")
        # # total_students_count = User.objects.count()
        # # generated_username = self.cleaned_data.get("email") 
        # #(
        # #    f"std-{registration_date}-{total_students_count}" # settings.STUDENT_ID_PREFIX
        # #)
        # # Generate a password
        # password = self.cleaned_data.get("password1") # User.objects.make_random_password()

        # # user.username = generated_username
        # user.set_password(password)
        # user.is_active = False

        if commit:
            booking.save()

        return booking

class AvailabilityForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # i = self.instance
        self.user = kwargs.pop('user', None)
        # self.instance = kwargs.pop('instance', None)
        # self.instance = kwargs['instance']
        if ('instance' in kwargs):
            kwargs['instance'].timeslots = eval(kwargs['instance'].timeslots)
        super(AvailabilityForm, self).__init__(*args, **kwargs)
        # self.fields['counsellor'].queryset = User.objects.filter(pk=self.user.id)
        # t = eval(self.instance.timeslots)
        # a = "ds,ds".strip().split()
        # self.fields['timeslots'].initial = ['2', '3'] #t #User.objects.filter(pk=self.user.id)
    
    def save(self, commit=True):
        availability = super().save(commit=False)
        availability.counsellor = self.user
        # availability.updated =  datetime.date.today()

        
        if commit:
            availability.save()

        return availability

    class Meta:
        model = models.Availability
        fields = ['date', 'timeslots'] #, 'counsellor', 'updated'
        widgets = {
            'date': forms.DateInput(attrs={'type':'date'}),
            'timeslots': forms.widgets.CheckboxSelectMultiple(choices=models.TIME_SLOTS),
        }

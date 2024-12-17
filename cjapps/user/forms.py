# from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group

from datetime import datetime
from django.http import request

from django.conf import settings
from django.core.mail import send_mail
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
)

from counselling.models import Category

User = get_user_model()

class UserRegisterForm(forms.ModelForm):
    # password = forms.CharField(label='Password')

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control form-control-sm",
            }
        ),
        label="First name",
    )

    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control form-control-sm",
            }
        ),
        label="Last name",
    )

    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "class": "form-control form-control-sm",
            }
        ),
        label="Email Address",
        required=True
    )

    password1 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control form-control-sm",
                "autocomplete": "new-password"
            }
        ),
        label="Password",
        required=True,
    )

    password2 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control form-control-sm",
            }
        ),
        label="Password Confirmation",
        required=True,
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            # 'middle_name',
            'last_name',
            'email',
            # 'password',
        ]

    def clean(self, *args, **kwargs):
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")
        email = cleaned_data.get("email")
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if not email and password1 and password2:
            raise ValidationError("Required Fields Missing.")

        email_check = User.objects.filter(email=email)
        if email_check.exists():
            raise forms.ValidationError('This Email already exists')

        if password1 != password2:
            raise ValidationError("Passwords does not match.")

        if len(password1) < 8:
            raise ValidationError("Password should be minimum 8 characters long.")

        return super(UserRegisterForm, self).clean(*args, **kwargs)

    # @transaction.atomic()
    def save(self, commit=True):
        user = super().save(commit=False)
        # user.is_student = True
        user.role = User.INDIVIDUAL
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        # user.gender = self.cleaned_data.get("gender")
        # user.address = self.cleaned_data.get("address")
        # user.phone = self.cleaned_data.get("phone")
        # user.contact_address = self.cleaned_data.get("address")
        user.email = self.cleaned_data.get("email")
        user.email_is_verified = False

        # Generate a username based on first and last name and registration date
        # registration_date = datetime.now().strftime("%Y")
        # total_students_count = User.objects.count()
        # generated_username = self.cleaned_data.get("email") 
        #(
        #    f"std-{registration_date}-{total_students_count}" # settings.STUDENT_ID_PREFIX
        #)
        # Generate a password
        password = self.cleaned_data.get("password1") # User.objects.make_random_password()

        # user.username = generated_username
        user.set_password(password)
        user.is_active = False

        if commit:
            user.save()

            # Send email with the generated credentials
            # send_mail(
            #     "Your Career Judge account credentials",
            #     f"Your ID: {generated_username}\nYour password: {generated_password}",
            #     settings.EMAIL_FROM_ADDRESS,
            #     [user.email],
            #     fail_silently=False,
            # )

        return user


class UserAddForm(forms.ModelForm):#UserCreationForm
    # class Media:
    #     js = ['role-manage.js']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

        super(UserAddForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        
        if self.user.is_channelpartner:
            self.fields['role'].disabled = True
    
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")
        email = cleaned_data.get("email")
        # password1 = cleaned_data.get("password1")
        # password2 = cleaned_data.get("password2")

        # if not email and password1 and password2:
        #     raise ValidationError("Required Fields Missing.")

        email_check = User.objects.filter(email=email)
        if email_check.exists():
            raise forms.ValidationError('This Email already exists')

        # if password1 != password2:
        #     raise ValidationError("Passwords does not match.")

        # if len(password1) < 8:
        #     raise ValidationError("Password should be minimum 8 characters long.")

        return super(UserAddForm, self).clean(*args, **kwargs)


    class Meta:#(UserCreationForm.Meta)
        model = User
        fields = ["role", "first_name", "middle_name", "last_name",
            "gender", "dob", "phone", "email", "occupation", "cur_position", "work_exp",
            "picture", 
            "high_education", "domain_exp", "edu_level", "institution_name", "institution_place",
            "country", "state", "location", "assess_pack_alloc",
            "pan", "bank_ac", "bank_name", "bank_branch", "bank_ifsc",
            "contact_address", "perm_address", "off_address",
            "user_bio", "group_name", "org_name", "manager_name", "pan_tan",
            "emp_id", "div_region", "ga_permissions",
            "chp_agency_name", "chp_region", "chp_agrmt_id", "chp_contr_period", "category", "rate"] #'__all__'
        widgets = {
            'dob': forms.DateInput(attrs={'type':'date'}),
            'contact_address': forms.Textarea(attrs={'rows': '3'}),
            'perm_address': forms.Textarea(attrs={'rows': '3'}),
            'off_address': forms.Textarea(attrs={'rows': '3'}),
            'user_bio': forms.Textarea(attrs={'rows': '3'}),
            'category': forms.Select(choices=Category.objects.all().values_list('id', 'name')),
            'rate': forms.TextInput(),
        }

    @transaction.atomic()
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False

        # user.role = self.cleaned_data.get("role")
        # user.first_name = self.cleaned_data.get("first_name")
        # user.last_name = self.cleaned_data.get("last_name")
        # user.gender = self.cleaned_data.get("gender")
        # user.address = self.cleaned_data.get("address")
        # user.phone = self.cleaned_data.get("phone")
        # user.contact_address = self.cleaned_data.get("address")
        # user.email = self.cleaned_data.get("email")

        # # Generate a username based on first and last name and registration date
        # registration_date = datetime.now().strftime("%Y")
        # total_students_count = User.objects.count()
        # generated_username = (
        #     f"std-{registration_date}-{total_students_count}" # settings.STUDENT_ID_PREFIX
        # )
        # # Generate a password
        generated_password = User.objects.make_random_password()

        # user.username = generated_username
        user.set_password(generated_password)

        if commit:
            user.save()

        return user


class UserEditForm(forms.ModelForm): #UserChangeForm
    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        # print(instance)
        self.fields['first_name'].disabled = True
        self.fields['middle_name'].disabled = True
        self.fields['last_name'].disabled = True
        self.fields['gender'].disabled = True
        self.fields['dob'].disabled = True
        self.fields['country'].disabled = True
        self.fields['state'].disabled = True
        
        self.fields['email'].disabled = True

        self.fields['pan_tan'].disabled = True
        self.fields['org_name'].disabled = True
        self.fields['chp_agency_name'].disabled = True



    class Meta:
        model = User
        fields = ["first_name", "middle_name", "last_name",
            "gender", "dob", "phone", "email", "occupation", "cur_position", "work_exp",
            "picture", 
            "high_education", "domain_exp", "edu_level", "institution_name", "institution_place",
            "country", "state", "location", "assess_pack_alloc",
            "pan", "bank_ac", "bank_name", "bank_branch", "bank_ifsc",
            "contact_address", "perm_address", "off_address",
            "user_bio", "group_name", "org_name", "manager_name", "pan_tan",
            "emp_id", "div_region", "ga_permissions",
            "chp_agency_name", "chp_region", "chp_agrmt_id", "chp_contr_period"]        
        widgets = {
            'dob': forms.DateInput(attrs={'type':'date'}),
            'contact_address': forms.Textarea(attrs={'rows': '3'}),
            'perm_address': forms.Textarea(attrs={'rows': '3'}),
            'off_address': forms.Textarea(attrs={'rows': '3'}),
            'user_bio': forms.Textarea(attrs={'rows': '3'}),
        }

class ProfileEditForm(forms.ModelForm): #UserChangeForm
    
    class Meta:
        model = User
        fields = ["first_name", "middle_name", "last_name",
            "gender", "dob", "phone", "email", "occupation", "cur_position", "work_exp",
            "picture", 
            "high_education", "domain_exp", "edu_level", "institution_name", "institution_place",
            "country", "state", "location", "assess_pack_alloc",
            "pan", "bank_ac", "bank_name", "bank_branch", "bank_ifsc",
            "contact_address", "perm_address", "off_address",
            "user_bio", "group_name", "org_name", "manager_name", "pan_tan",
            "emp_id", "div_region", "ga_permissions",
            "chp_agency_name", "chp_region", "chp_agrmt_id", "chp_contr_period"]        
        widgets = {
            'dob': forms.DateInput(attrs={'type':'date'}),
            'contact_address': forms.Textarea(attrs={'rows': '3'}),
            'perm_address': forms.Textarea(attrs={'rows': '3'}),
            'off_address': forms.Textarea(attrs={'rows': '3'}),
            'user_bio': forms.Textarea(attrs={'rows': '3'}),
        }

class UserImportForm(forms.Form):
    
    import_file = forms.FileField(
        # max_length=30,
        # widget=forms.TextInput(
        #     attrs={
        #         "type": "text",
        #         "class": "form-control form-control-sm",
        #     }
        # ),
        label="Import CSV file",
    )

class GroupEditForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'desc']
        widgets = {
            # 'name': forms.CharField(attrs={'type': 'text'}), #
            'desc': forms.Textarea(attrs={'rows': '3'}),
            # 'perms': forms.Textarea(attrs={'rows': '3'}),
        }

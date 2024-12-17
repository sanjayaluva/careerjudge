# from django.contrib.auth.models import AbstractUser
# from django.utils.translation import gettext_lazy as _
# from django.contrib.auth.base_user import BaseUserManager

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.urls import reverse
from django.conf import settings
from PIL import Image
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import Group
# from django_group_model.models import AbstractGroup


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.CJ_ADMIN)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)
    
    def search(self, query=None):
        queryset = self.get_queryset()
        if query is not None:
            or_lookup = (
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
            )
            queryset = queryset.filter(
                or_lookup
            ).distinct()  # distinct() is often necessary with Q lookups
        return queryset
    
    # def get_student_count(self):
    #     return self.model.objects.filter(is_student=True).count()
    # def get_lecturer_count(self):
    #     return self.model.objects.filter(is_lecturer=True).count()
    # def get_superuser_count(self):
    #     return self.model.objects.filter(is_superuser=True).count()

class User(AbstractUser):

    GENDERS = (("M", "Male"), ("F", "Female"), ("O", "Others"))
    OCCUPATION = (("employed", "Employed"), 
        ("self-employed", "Self Employed"), 
        ("job-seek-fresher", "Job seeking-Fresher"),
        ("job-seek-nonfresher", "Job seeking-nonFresher"),
        ("college-student", "College Student"), 
        ("school-student", "School Student"))
    EDUCATION_LEVEL = (("below-plus2", "5-12"),
        ("under-grad", "Undergraduate"), 
        ("post-grad", "Post Graduate"),
        ("mphil", "M-Phil"),
        ("phd", "PhD"))
    OCCUPATION_MAJOR = ((1, "Employed"), (2, "Self Employed"), (3, "Retired"))

    # SUPER_ADMIN = '0'         # Super Admin
    CJ_ADMIN = '1'              # CJ Admin
    CORPORATE_ADMIN = '2'       # Corporate Admin
    CORPORATE_EXCLUSIVE = '3'   # Corporate Exclusive
    PSYCHOMETRICIAN = '4'       # Psychometrician
    SME = '5'                   # SME
    REVIEWER = '6'              # Reviewer
    TRAINER = '7'               # Trainer
    GROUP_ADMIN = '8'           # Group admins
    COUNSELLOR = '9'            # Counsellor
    INDIVIDUAL = '10'           # Individuals
    CHANNEL_PARTNER = '11'      # Channel Partner
    CORPORATE_INDIVIDUAL = '12' # Corporate Individual
    CJ_MANGER = '13'            # CJ Manager
    HELPDESK = '14'             # Helpdesk


    DEFAULT_USER = '9'
    
    ROLES = { 
        # SUPER_ADMIN: 'Super User', 
        CJ_ADMIN: 'CareerJudge Admin', 
        CORPORATE_ADMIN: 'Corporate Admin', 
        CORPORATE_EXCLUSIVE: 'Corporate Exclusive',
        PSYCHOMETRICIAN: 'Psychometrician',
        SME: 'SME',
        REVIEWER: 'Reviewer',
        TRAINER: 'Trainer',
        GROUP_ADMIN: 'Group Admin',
        COUNSELLOR: 'Counsellor',
        INDIVIDUAL: 'Individual',
        CHANNEL_PARTNER: 'Channel Partner',
        CORPORATE_INDIVIDUAL: 'Corporate Individual',
        CJ_MANGER: 'CJ Manager',
        HELPDESK: 'Helpdesk',
    }

    # use email instead of username 
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    username = None
    email = models.EmailField(_('Email Address'), max_length=50, unique=True)
    email_is_verified = models.BooleanField(_('Email Verified'), default=False)
    #------------------------------

    role = models.CharField(_('User Role'), default=DEFAULT_USER, choices=ROLES, max_length=10) 
    
    # groups = models.ManyToManyField(
    #     settings.AUTH_GROUP_MODEL,
    #     verbose_name=_("groups"),
    #     blank=True,
    #     help_text=_(
    #         "The groups this user belongs to. A user will get all permissions "
    #         "granted to each of their groups."
    #     ),
    #     related_name="user_set",
    #     related_query_name="user",

    # )

    # individual profile fields 
    first_name = models.CharField(_('First Name'), max_length=100, blank=True, null=True)
    middle_name = models.CharField(_('Middle Name'), max_length=100, blank=True, null=True)
    last_name = models.CharField(_('Last Name'), max_length=100, blank=True, null=True)

    gender = models.CharField(_('Gender'), max_length=1, choices=GENDERS, blank=True, null=True)
    dob = models.DateField(_('Date of Birth'), blank=True, null=True)
    phone = models.CharField(_('Phone'), max_length=60, blank=True, null=True)
    
    occupation = models.CharField(_('Occupation'), max_length=100, choices=OCCUPATION, blank=True, null=True)
    cur_position = models.CharField(_('Current Position'), max_length=50, blank=True, null=True)
    work_exp = models.IntegerField(_('Work Experience'), blank=True, null=True)
    
    high_education = models.CharField(_('Highest Education'), max_length=50, blank=True, null=True)
    edu_level = models.CharField(_('Education Level'), max_length=50, choices=EDUCATION_LEVEL, blank=True, null=True)
    institution_name = models.CharField(_('Institution Name'), max_length=50, blank=True, null=True)
    institution_place = models.CharField(_('Place of Institution'), max_length=50, blank=True, null=True)
    
    country = models.CharField(_('Country of Origin'), max_length=50, blank=True, null=True)
    state = models.CharField(_('State/Province'), max_length=50, blank=True, null=True)
    location = models.CharField(_('Location'), max_length=50, blank=True, null=True)
    
    assess_pack_alloc = models.CharField(_('Assessment Package allocated'), max_length=100, blank=True, null=True)
  
    picture = models.ImageField(
        upload_to="profile_pictures/%y/%m/%d/", default="default.png", blank=True, null=True
    )

    # corporate profile fields
    org_name = models.CharField(_('Organization Name'), max_length=100, blank=True, null=True)
    manager_name = models.CharField(_('Manager Name'), max_length=100, blank=True, null=True)
    # phone = models.CharField(max_length=60, blank=True, null=True)
    group_name = models.CharField(_('Group Name'), max_length=100, blank=True, null=True)
    pan_tan = models.CharField(_('PAN/TAN'), max_length=60, blank=True, null=True)
    off_address = models.CharField(_('Office Address'), max_length=100, blank=True, null=True)

    # group admins
    emp_id = models.CharField(_('Employee ID'), max_length=100, blank=True, null=True)
    div_region = models.CharField(_('Division/Region'), max_length=100, blank=True, null=True)
    ga_permissions = models.CharField(_('Permissions Allotted'), max_length=100, blank=True, null=True)

    # reviewer / trainer / councellor profile fields

    pan = models.CharField(_('PAN Number'), max_length=50, blank=True, null=True)
    bank_ac = models.CharField(_('Bank Account Number'), max_length=50, blank=True, null=True)
    bank_name = models.CharField(_('Bank Name'), max_length=50, blank=True, null=True)
    bank_branch = models.CharField(_('Bank Branch'), max_length=50, blank=True, null=True)
    bank_ifsc = models.CharField(_('Bank IFSC'), max_length=50, blank=True, null=True)

    contact_address = models.CharField(_('Contact Address'), max_length=255, blank=True, null=True)
    perm_address = models.CharField(_('Permanent Address'), max_length=255, blank=True, null=True)
    
    domain_exp = models.IntegerField(_('Domain Experience'), blank=True, null=True)
    user_bio = models.CharField(_('User Biodata'), max_length=500, blank=True, null=True)

    # channel partner profile fields 
    chp_agency_name = models.CharField(_('Agency Name'), max_length=100, blank=True, null=True)
    chp_agrmt_id = models.CharField(_('Channel Partner Agreement ID'), max_length=100, blank=True, null=True)
    chp_contr_period = models.CharField(_('Contract Period'), max_length=100, blank=True, null=True)
    chp_region = models.CharField(_('Region Allocated'), max_length=100, blank=True, null=True)
    
    # ----------------------------------

    createdby = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True
    )

    rate = models.TextField(blank=True, null=True)
    category = models.TextField(blank=True, null=True)

    @property
    def get_full_name(self):
        full_name = self.email
        if self.first_name and self.last_name and self.middle_name:
            full_name = self.first_name + " " + self.middle_name + " " + self.last_name
        elif self.first_name and self.last_name:
            full_name = self.first_name + " " + self.last_name
        return full_name
    
    # def __str__(self):
    #     return "{} ({})".format(self.get_full_name, self.email)

    @property
    def is_cjadmin(self):
        return True if self.role == '1' else False
    @property
    def is_corpadmin(self):
        return True if self.role == '2' else False
    @property
    def is_corpexclusive(self):
        return True if self.role == '3' else False
    @property
    def is_psychometrician(self):
        return True if self.role == '4' else False
    @property
    def is_sme(self):
        return True if self.role == '5' else False
    @property
    def is_reviewer(self):
        return True if self.role == '6' else False
    @property
    def is_trainer(self):
        return True if self.role == '7' else False
    @property
    def is_groupadmin(self):
        return True if self.role == '8' else False
    @property
    def is_counsellor(self):
        return True if self.role == '9' else False
    @property
    def is_individual(self):
        return True if self.role == '10' else False
    @property
    def is_channelpartner(self):
        return True if self.role == '11' else False
    @property
    def is_corpindividual(self):
        return True if self.role == '12' else False
    @property
    def is_cjmanager(self):
        return True if self.role == '13' else False
    @property
    def is_helpdesk(self):
        return True if self.role == '14' else False
    
    @property
    def get_user_role(self):
        # if self.role == '0':
        #     role = "Super Admin"
        if self.role == '1':
            role = "CJ Admin"
        elif self.role == '2':
            role = "Corporate Admin"
        elif self.role == '3':
            role = "Corporate Exclusive"
        elif self.role == '4':
            role = "Psychometrician"
        elif self.role == '5':
            role = "SME"
        elif self.role == '6':
            role = "Reviewer"
        elif self.role == '7':
            role = "Trainer"
        elif self.role == '8':
            role = "Group Admin"
        elif self.role == '9':
            role = "Counsellor"
        elif self.role == '10':
            role = "Individual"
        elif self.role == '11':
            role = "Channel Partner"
        elif self.role == '12':
            role = "Corporate Individual"
        elif self.role == '13':
            role = "Career Judge Manager"
        elif self.role == '14':
            role = "Helpdesk"
        else:
            role = "Unknown"
        return role

    def get_picture(self):
        try:
            return self.picture.url
        except:
            no_picture = settings.MEDIA_URL + "default.png"
            return no_picture

    def get_absolute_url(self):
        return reverse("profile_single", kwargs={"id": self.id})
        # pass

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            img = Image.open(self.picture.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.picture.path)
        except:
            pass

    def delete(self, *args, **kwargs):
        if self.picture.url != settings.MEDIA_URL + "default.png":
            self.picture.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.email

    class Meta():
        permissions = (
            ("import_user", "Can Import User"),
        )
    


Group.add_to_class('desc', models.CharField(_('Description'), max_length=500, blank=True, null=True))

# class Group(AbstractGroup):
#     # name = models.CharField(_('Name'), max_length=100, blank=True, null=True)
#     desc = models.CharField(_('Description'), max_length=500, blank=True, null=True)
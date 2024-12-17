from django.db import models
# from django.utils import timezone
from django.db.models import Q
# from multiselectfield import MultiSelectField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
User = get_user_model()

TIME_SLOTS = {
    "1": "9-10 (Morning)",
    "2": "10-11 (Morning)",
    "3": "11-12 (Morning)",
    "4": "12-13 (Afternoon)",
    "5": "13-14 (Afternoon)",
    "6": "14-15 (Afternoon)",
    "7": "15-16 (Evening)",
    "8": "16-17 (Evening)",
    "9": "17-18 (Evening)",
    "10": "18-19 (Evening)",
}

class Category(models.Model):
    name = models.CharField(max_length=200, blank=False)
    desc = models.CharField(max_length=500, null=True)

    def __str__(self):
        return self.name

    class Meta():
        permissions = (
            ("counselling_category_add", "Can add Counselling category"),
            ("counselling_category_change", "Can change Counselling category"),
            ("counselling_category_view", "Can view Counselling category"),
            ("counselling_category_delete", "Can delete Counselling category"),
        )
        default_permissions = ()

class Booking(models.Model):
    STATUS_BOOKED = 0
    STATUS_COMPLETED = 1
    STATUS_CANCELLED = 2
    STATUS_CHOICES = (
        (STATUS_BOOKED, 'Booked'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    )

    counselee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='counselee')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    counsellor = models.ForeignKey(User, 
        on_delete=models.CASCADE, 
        related_name='counsellor'#, 
        # limit_choices_to=Q(role=User.COUNSELLOR)
    )
    date = models.DateField(_('Booking Date'), null=True) #''', choices=TIME_SLOTS'''
    timeslot = models.TextField(_('Timeslot'), choices=TIME_SLOTS, null=True) #''''''
    # MultiSelectField(choices=TIME_SLOTS, max_choices=10, max_length=10)
    topic = models.CharField(_('Topic/Issue'), max_length=500, help_text=_('Describe the topic or issue'))
    booked = models.DateTimeField(_('Booked on'), null=True)
    paid = models.BooleanField(_('Paid'), default=False)
    # payment_info = models.JSONField(default=dict, null=True)
    rzp_payment_id = models.TextField(blank=True, null=True)
    rzp_order_id = models.TextField(blank=True, null=True)
    rzp_signature = models.TextField(blank=True, null=True)
    
    status = models.IntegerField(_('Status'), choices=STATUS_CHOICES, default=STATUS_BOOKED, null=True)
    reason = models.TextField(max_length=500, help_text=_('Reason for Cancellation'), blank=True, null=True)


    def __str__(self):
        return f"Session: {self.category} by {self.counsellor.get_full_name} on {self.booked}"

    def save(self, *args, **kwargs):
        # do_something()
        super().save(*args, **kwargs)  # Call the "real" save() method.
        # do_something_else()

    class Meta():
        # permissions = (
        #     ("counselling_booking", "Can book Counselling"),
        #     ("counselling_list", "Can view booked Counselling"),
        #     ("cancel_booking", "Can cancel booked Counselling"),
        #     ("counselling_timeslots", "Can update Counselling timeslots"),
        # )
        default_permissions = ('view_counselling', 'add_counselling', 'cancel_counselling')


class Availability(models.Model):
    counsellor = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(_('Date'))
    timeslots = models.CharField(_('Timeslots'), max_length=100, help_text=_('timeslots are in 24 hours format')) #MultiSelectField(_('Tileslots'), choices=TIME_SLOTS, max_choices=10, max_length=10)
    created = models.DateTimeField(_('Created on'), auto_now_add=True, null=True)
    updated = models.DateTimeField(_('Updated on'), auto_now=True, null=True)

    def __str__(self):
        # return self.date
        return f"{self.date} - {self.timeslots}"

    class Meta():
        default_permissions = ('update_counselling',)

    
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
# from django.contrib.auth.models import User
from django.urls import reverse
from .models import Notification
from counselling.models import Booking, TIME_SLOTS

from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils import formats

from cjapp.services import NotificationService

@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, **kwargs):
    """Notify counsellor upon successful payment for counselling booking."""
    if instance.paid:
        counsellor = instance.counsellor
        counselee = instance.counselee
        booked_at = formats.date_format(instance.booked, 'Y-m-d H:i')
        booking_date = instance.date
        timeslot = TIME_SLOTS[instance.timeslot]
        category = instance.category.name
        
        message = (
            f'Booking Received on {booked_at}, '
            f'from: {counselee.get_full_name}, '
            f'to {counsellor.get_full_name}, '
            f'for: {category} '
            f'on {booking_date} at {timeslot}'
        )

        NotificationService.send_notification(
            sender=counselee,
            receiver=counsellor,
            message=message,
            notification_type=Notification.COUNSELLING_BOOKING,
            related_object=instance
        )

@receiver(post_migrate)
def user_group_setup(sender, stdout=None, **kwargs):
    """Setup user groups upon user application migration."""
    if sender.name == 'user':
        created = False
        roles = User.ROLES
        for role in roles:
            try:
                group = Group.objects.get(name=roles[role])
            except Group.DoesNotExist:
                created = True
                group = Group.objects.create(name=roles[role])

        if created and stdout:
            stdout.write('Successfully synced User Groups. (created)')
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

from cjapp.notifications import send_notification

@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, **kwargs):
    """Notify User upon successfull payment for counselling booking."""
    if instance.paid:
        counsellor = instance.counsellor
        counsellor_name = instance.counsellor.get_full_name
        counselee = instance.counselee
        counselee_name = instance.counselee.get_full_name
        category = instance.category.name
        booked_at = formats.date_format(instance.booked, 'Y-m-d H:i')
        booking_date = instance.date
        timeslot = TIME_SLOTS[instance.timeslot]
        
        message = f'Booking Received on {booked_at}, from : {counselee_name} to {counsellor_name}, on topic {category} at {booking_date} : {timeslot}'
        # link = reverse('counselling_booking_detail', args=[str(instance.pk)])
        # notification = Notification(type=sender=counselee, reciever=counsellor, message=message) #, link=link
        # notification.metadata = f'{sender.__name__}:{instance.pk}'
        # # notification.link = link
        # notification.save()
        
        metadata = f'{sender.__name__}:{instance.pk}'

        send_notification(counselee, counsellor, message, Notification.COUSELLING_BOOKING, metadata)

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
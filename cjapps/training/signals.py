from django.db.models.signals import post_delete
from django.dispatch import receiver
# from django.contrib.auth.models import User
from django.urls import reverse
from .models import Assignment, Content, Node
# from counselling.models import Booking, TIME_SLOTS

# from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils import formats

from django.conf import settings
import os

@receiver(post_delete, sender=Assignment)
def assignment_post_delete(sender, instance, **kwargs):
    if bool(instance.file) != False and os.path.exists(os.path.join(settings.MEDIA_ROOT, instance.file.name)): 
        os.remove(os.path.join(settings.MEDIA_ROOT, instance.file.name))    

@receiver(post_delete, sender=Content)
def content_post_delete(sender, instance, **kwargs):
    if bool(instance.file) != False and os.path.exists(os.path.join(settings.MEDIA_ROOT, instance.file.name)): 
        os.remove(os.path.join(settings.MEDIA_ROOT, instance.file.name)) 

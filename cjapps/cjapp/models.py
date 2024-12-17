from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.

class Notification(models.Model):
    COUSELLING_BOOKING = 'counselling_booking'
    LIVESESSOIN_REQUEST = 'livesession_request'
    NOTIFICATION_TYPES = {
        COUSELLING_BOOKING: 'Counselling Booking Request',
        LIVESESSOIN_REQUEST: 'Live Session Request',
    }
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sent_notifications")
    reciever = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="recieved_notifications")
    message = models.TextField()
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.TextField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, blank=True, null=True)

    def unread_count(self):
        return self.filter(read=False).count()
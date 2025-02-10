from django.contrib.contenttypes.models import ContentType
# from django.db import models
from .notification_models import Notification 
from django.contrib.auth import get_user_model
User = get_user_model()


class NotificationService:
    @staticmethod
    def send_notification(sender, receiver, message, notification_type, related_object=None):
        notification = Notification.objects.create(
            sender=sender,
            receiver=receiver,
            message=message,
            notification_type=notification_type
        )
        
        if related_object:
            notification.content_type = ContentType.objects.get_for_model(related_object)
            notification.object_id = related_object.id
            notification.save()
        
        return notification

    @staticmethod
    def get_user_notifications(user, unread_only=False):
        queryset = Notification.objects.filter(receiver=user)
        if unread_only:
            queryset = queryset.filter(read=False)
        return queryset

    @staticmethod
    def mark_as_read(notification_id):
        Notification.objects.filter(id=notification_id).update(read=True)

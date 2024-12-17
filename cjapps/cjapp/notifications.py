from cjapp.models import Notification
# from django.http import HttpRequest

def send_notification(sender, reciever, message, type=None, metadata=None, link=None):
    notification = Notification(sender=sender, reciever=reciever, message=message, type=type) #, link=link
    if link is not None:
        notification.link = link
    if metadata is not None:
        notification.metadata = metadata #f'{sender.__name__}:{instance.pk}'
    # notification.link = link
    notification.save()
    return notification

def get_notification(notification_id=None):
    notification = Notification.objects.get(pk=notification_id)
    return notification

def get_notifications(reciever=None):
    notifications = Notification.objects.get(reciever=reciever).order_by('-timestamp').all()
    return notifications

def read_notification(notification_id=None, read=True):
    notification = Notification.objects.get(pk=notification_id)
    notification.read = read
    notification.save()
    return notification

def get_user_notifications(user=None):
    if user.is_authenticated:
        notifications = Notification.objects.filter(reciever=user, read=False).all()
    else:
        notifications = []

    return {
        'notifications': notifications,
        'notifications_count': len(notifications),
    }
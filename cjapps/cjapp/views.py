from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from .models import Notification
from .notifications import send_notification, get_notifications

from django.forms.models import model_to_dict
from django.http import JsonResponse

from django.contrib.auth import get_user_model
User = get_user_model()

@login_required
def get_notifications_view(request):
    notifications = get_notifications(reciever=request.user)
    return render(request, 'notifications.html', {'notifications': notifications})

def send_notification_view(request):
    message = request.POST['message']
    sender = request.user
    reciever = User.objects.get(pk=request.POST['reciever'])
    type = request.POST['type']
    metadata = request.POST['metadata'] if 'metadata' in request.POST else None

    # if type == Notification.LIVESESSOIN_REQUEST:
    #     metadata = f'{sender.__name__}:{instance.pk}'

    notification = send_notification(sender, reciever, message, type, metadata)
    # senddata = serializers.serialize('json', [training])
    notification = model_to_dict(notification)
    return JsonResponse({ 'status': True, 'data': notification }, safe=False)
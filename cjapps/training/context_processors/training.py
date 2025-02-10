from training.forms import ScheduleTrainingForm
from cjapp.services import NotificationService

def schedule_form(request):
    if request.user.is_authenticated:
        context_dict = {
            "schedule_training_form": ScheduleTrainingForm(),
            "notifications": NotificationService.get_user_notifications(request.user)[:10],
            "unread_notifications_count": NotificationService.get_user_notifications(request.user, unread_only=True).count()
        }
    else :
        context_dict = {
            "schedule_training_form": None,
            "notifications": None,
            "unread_notifications_count": 0
        }
    
    return context_dict

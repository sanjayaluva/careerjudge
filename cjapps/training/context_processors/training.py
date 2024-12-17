from training.forms import ScheduleTrainingForm
from cjapp.notifications import get_user_notifications



def schedule_form(request):

    context_dict = {
        "schedule_training_form": ScheduleTrainingForm(),
    }
    notifications_data = get_user_notifications(request.user)

    context_dict.update(notifications_data)
    
    return context_dict

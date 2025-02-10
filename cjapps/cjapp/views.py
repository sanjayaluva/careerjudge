from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse

from django.contrib.auth import get_user_model
User = get_user_model()

from question_bank.models import Question
from training.models import TrackLivesession as LiveSession
from counselling.models import Booking

from .models import Task
from .forms import TaskCreationForm, ReviewForm
from .services import NotificationService
from .models import Notification

@login_required
def get_notifications_view(request):
    """Get user notifications for display"""
    notifications = NotificationService.get_user_notifications(request.user)
    return render(request, 'notifications.html', {'notifications': notifications})

def send_notification_view(request):
    """API endpoint to send notifications"""
    message = request.POST['message']
    receiver = User.objects.get(pk=request.POST['receiver'])
    notification_type = request.POST['type']
    
    # Get related object based on notification type
    related_object = None
    if notification_type == Notification.LIVE_SESSION_REQUEST:
        session_id = request.POST.get('metadata')
        related_object = LiveSession.objects.get(id=session_id)
    elif notification_type == Notification.COUNSELLING_BOOKING:
        booking_id = request.POST.get('metadata')
        related_object = Booking.objects.get(id=booking_id)

    # Create notification using service
    notification = NotificationService.send_notification(
        sender=request.user,
        receiver=receiver,
        message=message,
        notification_type=notification_type,
        related_object=related_object
    )

    return JsonResponse({
        'status': True, 
        'data': {
            'id': notification.id,
            'message': notification.message,
            'type': notification.notification_type,
            'created_at': notification.created_at.isoformat()
        }
    }, safe=False)


@login_required
def task_list(request):
    tasks = Task.objects.filter(
        Q(sme_user=request.user) |
        Q(reviewer_user=request.user) |
        Q(psychometrician_user=request.user) |
        Q(created_by=request.user)
    ).distinct()
    return render(request, 'cjapp/task_list.html', {'tasks': tasks})

@login_required
@user_passes_test(lambda u: u.is_cjadmin)
def create_task(request):
    if request.method == 'POST':
        form = TaskCreationForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            
            # Get first step from TASK_STEPS
            first_step = Task.TASK_STEPS[form.cleaned_data['task_type']][0][0]
            task.step = first_step

            step_display = dict(Task.TASK_STEPS[form.cleaned_data['task_type']])[first_step]
            # task.name = f"{task.name} - {step_display}"
            task.save()

            task.notify_assignee()
            
            # NotificationService.send_notification(
            #     sender=request.user,
            #     receiver=task.get_current_assignee(),
            #     message=f"New task assigned: {task.name}",
            #     notification_type=Notification.QUESTION_CREATION
            # )
            
            messages.success(request, 'Task created successfully')
            return redirect('cjapp:task_list')
    else:
        form = TaskCreationForm()
    return render(request, 'cjapp/create_task.html', {'form': form})

@login_required
def review_task(request, task_id, question_id=None):
    task = get_object_or_404(Task, id=task_id)

    if task.get_current_assignee() != request.user:
        messages.error(request, 'You are not authorized to review this task')
        return redirect('cjapp:task_list')
    
    if request.method == 'POST':
        if task.step == 'question_creation':
            if task.questions_created == task.number_of_questions:
                task.status = 'completed'
                task.completed_at = timezone.now()
                task.save()
                task.create_next_step_task()
                messages.success(request, 'All required questions added and sent for review')
                return redirect('cjapp:task_list')
                
        elif task.step in ['content_review', 'psychometric_review']:
            form = ReviewForm(request.POST)
            if form.is_valid():
                task.review_rating = form.cleaned_data['rating']
                task.review_comments = form.cleaned_data['comments']
                task.status = 'completed' if form.cleaned_data['decision'] == 'approve' else 'rejected'
                task.completed_at = timezone.now()
                task.save()
                
                if task.status == 'completed':
                    task.create_next_step_task()
                    messages.success(request, 'Review completed')
                else:
                    Task.objects.create(
                        name=f"Revision: {task.parent_task.name}",
                        description=f"Revise question based on review comments: {task.review_comments}",
                        task_type=task.task_type,
                        step='question_creation',
                        sme_user=task.sme_user,
                        reviewer_user=task.reviewer_user,
                        psychometrician_user=task.psychometrician_user,
                        created_by=request.user,
                        parent_task=task.parent_task,
                        question=task.question
                    )
                    messages.warning(request, 'Question returned for revision')
                return redirect('cjapp:task_list')
        
        elif task.step == 'final_approval':
            action = request.POST.get('action')
            if action == 'approve':
                task.status = 'completed'
                task.completed_at = timezone.now()
                task.questions.update(status='active')
                task.save()
                messages.success(request, 'Task completed and questions approved')
                return redirect('cjapp:task_list')
    else:
        if task.step == 'question_creation' and question_id:
            question = get_object_or_404(Question, id=question_id)

            if not task.questions.filter(id=question_id).exists():
                if task.questions.count() < task.number_of_questions:
                    task.questions.add(question)
                    task.questions_created = task.questions.count()
                    task.save()
                    
                    messages.success(request, f'Question {task.questions_created} of {task.number_of_questions} added')
                else:
                    messages.error(request, 'Maximum number of questions already added')
            # else:
                # messages.error(request, 'This question is already linked to the task')

    context = {
        'task': task,
        'form': ReviewForm() if task.step in ['content_review', 'psychometric_review'] else None,
        'linked_questions': task.questions.all()
    }

    return render(request, 'cjapp/review_task.html', context)
def get_notification_context(request):
    if request.user.is_authenticated:
        return {
            'notifications': NotificationService.get_user_notifications(request.user)[:10],
            'unread_notifications_count': NotificationService.get_user_notifications(request.user, unread_only=True).count()
        }
    return {'notifications': [], 'unread_notifications_count': 0}

@login_required
def mark_notification_read(request):
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        NotificationService.mark_as_read(notification_id)
        return JsonResponse({'status': True})
    return JsonResponse({'status': False})

@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        notifications = NotificationService.get_user_notifications(request.user, unread_only=True)
        notifications.update(read=True)
        return JsonResponse({'status': True})
    return JsonResponse({'status': False})

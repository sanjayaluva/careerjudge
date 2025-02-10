from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json

from .services import NotificationService
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from .notification_models import Notification 

from question_bank.models import Question

# class Notification(models.Model):
#     # Notification Types
#     QUESTION_CREATION = 'question_creation'
#     COUNSELLING_BOOKING = 'counselling_booking'
#     LIVE_SESSION_REQUEST = 'livesession_request'
#     TASK_CREATED = 'task_created'
#     TASK_UPDATED = 'task_updated'
#     REVIEW_REQUIRED = 'review_required'
#     REVIEW_COMPLETED = 'review_completed'
    
#     NOTIFICATION_TYPES = {
#         COUNSELLING_BOOKING: 'Counselling Booking Request',
#         LIVE_SESSION_REQUEST: 'Live Session Request',
#         QUESTION_CREATION: 'Question Creation',
#         TASK_CREATED: 'Task Created',
#         TASK_UPDATED: 'Task Updated',
#         REVIEW_REQUIRED: 'Review Required',
#         REVIEW_COMPLETED: 'Review Completed'
#     }
    
#     sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications")
#     receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_notifications")
#     message = models.TextField()
#     notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES.items())
#     read = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     # For linking to any model (Task, Booking, etc.)
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
#     object_id = models.PositiveIntegerField(null=True)
#     content_object = GenericForeignKey('content_type', 'object_id')

#     class Meta:
#         ordering = ['-created_at']

class Task(models.Model):
    TASK_TYPES = (
        ('question_creation', 'Question Creation'),
    )
    
    TASK_STEPS = {
        'question_creation': [
            ('question_creation', 'Question Creation'),
            ('content_review', 'Content Review'),
            ('psychometric_review', 'Psychometric Review'),
            ('final_approval', 'Final Approval')
        ]
    }
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'), 
        ('completed', 'Completed'),
        ('rejected', 'Rejected')
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=50, choices=TASK_TYPES)
    step = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    sme_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sme_tasks')
    reviewer_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviewer_tasks')
    psychometrician_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psychometrician_tasks')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    parent_task = models.ForeignKey('self', null=True, on_delete=models.CASCADE, related_name='subtasks')
    questions = models.ManyToManyField('question_bank.Question', related_name='tasks', blank=True, default=None)
    question_type = models.CharField(max_length=50, choices=Question.QUESTION_TYPES, null=True, blank=True)
    number_of_questions = models.PositiveIntegerField(default=1)
    questions_created = models.PositiveIntegerField(default=0)
    
    review_rating = models.IntegerField(null=True)
    review_comments = models.TextField(null=True)
    
    def get_step_display(self):
        """Returns the display value for current step"""
        return dict(self.TASK_STEPS[self.task_type])[self.step]
    
    def get_current_assignee(self):
        if self.step == 'question_creation':
            return self.sme_user
        elif self.step == 'content_review':
            return self.reviewer_user
        elif self.step == 'psychometric_review':
            return self.psychometrician_user
        elif self.step == 'final_approval':
            return self.created_by
        return None

    def create_next_step_task(self):
        steps = self.TASK_STEPS[self.task_type]
        current_index = next(i for i, s in enumerate(steps) if s[0] == self.step)
        
        if current_index + 1 < len(steps):
            next_step = steps[current_index + 1][0]
            next_task = Task.objects.create(
                name=self.name,
                description=self.description,
                task_type=self.task_type,
                step=next_step,
                sme_user=self.sme_user,
                reviewer_user=self.reviewer_user,
                psychometrician_user=self.psychometrician_user,
                created_by=self.created_by,
                parent_task=self.parent_task or self,
                question_type=self.question_type,
                number_of_questions=self.number_of_questions,
                questions_created=self.questions_created
            )
            
            # Copy linked questions to new task
            next_task.questions.set(self.questions.all())
            next_task.notify_assignee()
            
            return next_task
        return None
    
    def notify_assignee(self):
        assignee = self.get_current_assignee()
        if not assignee:
            return
            
        # notification_type = Notification.TASK_CREATED
        # if self.step == 'question_creation':
        #     notification_type = Notification.QUESTION_CREATION
        # elif self.step in ['content_review', 'psychometric_review']:
        #     notification_type = Notification.REVIEW_REQUIRED
            
        # Use the step directly from TASK_STEPS dictionary
        # step_display = dict(self.TASK_STEPS[self.task_type])[self.step]
        
        NotificationService.send_notification(
            sender=self.created_by,
            receiver=assignee,
            message=f"New task assigned: {self.name} - {self.get_step_display()}",
            notification_type=self.step,
            related_object=self
        )

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    # Notification Types
    COUNSELLING_BOOKING = 'counselling_booking'
    LIVE_SESSION_REQUEST = 'livesession_request'
    
    # TASK_CREATED = 'task_created'
    # TASK_UPDATED = 'task_updated'
    # REVIEW_REQUIRED = 'review_required'
    # REVIEW_COMPLETED = 'review_completed'
    
    QUESTION_CREATION = 'question_creation'
    CONTENT_REVIEW = 'content_review'
    PSYCHOMETRIC_REVIEW = 'psychometric_review'
    FINAL_APPROVAL = 'final_approval'

    DELETION_REQUEST = 'deletion_request'
    DELETION_APPROVED = 'deletion_approved'
    DELETION_REJECTED = 'deletion_rejected'

    NOTIFICATION_TYPES = {
        COUNSELLING_BOOKING: 'Counselling Booking Request',
        LIVE_SESSION_REQUEST: 'Live Session Request',
        
        QUESTION_CREATION: 'Question Creation',
        CONTENT_REVIEW: 'Content Review',
        PSYCHOMETRIC_REVIEW: 'Psychometric Review',
        FINAL_APPROVAL: 'Final Approval',
        
        # TASK_CREATED: 'Task Created',
        # TASK_UPDATED: 'Task Updated',
        # REVIEW_REQUIRED: 'Review Required',
        # REVIEW_COMPLETED: 'Review Completed',

        DELETION_REQUEST: 'Deletion Request',
        DELETION_APPROVED: 'Deletion Approved',
        DELETION_REJECTED: 'Deletion Rejected',
    }
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_notifications")
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES.items())
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']

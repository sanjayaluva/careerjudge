from django.db import models
from django_quill.fields import QuillField

from django.contrib.auth import get_user_model
User = get_user_model()

from question_bank.models import Question

class Assessment(models.Model):
    PRESENTATION_CHOICES = [
        ('sequential', 'Sequential'),
        ('random', 'Random')
    ]
    display_order = models.CharField(
        max_length=10,
        choices=PRESENTATION_CHOICES,
        default='random'
    )

    title = models.CharField(max_length=200)
    objective = QuillField()
    description = QuillField()
    description_img = models.ImageField(upload_to='assessment_images/', blank=True, null=True)
    instructions = QuillField()
    instructions_img = models.ImageField(upload_to='assessment_images/', blank=True, null=True)
    
    published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    # structure = models.JSONField(default=dict)

    level_counts = models.JSONField(default=dict)
    # delivery_count = models.JSONField(default=dict)

    display_interval = models.PositiveIntegerField(default=0)
    
    duration_minutes = models.IntegerField(default=60)  # Default 60 minutes

    def get_total_questions(self):
        # Recursively count all questions in sections and subsections
        def count_questions(section):
            total = 1 if section.question else 0
            for child in section.children.all():
                total += count_questions(child)
            return total
            
        root_sections = self.sections.filter(parent=None)
        return sum(count_questions(section) for section in root_sections)
    
class Section(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    question = models.ForeignKey(Question, null=True, blank=True, on_delete=models.SET_NULL)
    is_section = models.BooleanField(default=True)

    right_score = models.PositiveIntegerField(default=1)
    wrong_score = models.PositiveIntegerField(default=0)


    class Meta:
        ordering = ['order']
        
    
class AssessmentSession(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('suspended', 'Suspended'),
        ('completed', 'Completed')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    is_completed = models.BooleanField(default=False)
    current_section = models.ForeignKey(Section, null=True, on_delete=models.SET_NULL)
    current_question = models.ForeignKey(Question, null=True, on_delete=models.SET_NULL)
    time_remaining = models.IntegerField(help_text="Remaining time in seconds", null=True)

    def save_state(self):
        self.time_remaining = self.calculate_remaining_time()
        self.save()

    def calculate_remaining_time(self):
        elapsed = timezone.now() - self.start_time
        return max(0, self.assessment.duration_minutes * 60 - elapsed.seconds)

    def resume(self):
        if self.status == 'suspended':
            self.start_time = timezone.now()
            self.status = 'in_progress'
            self.save()
    
    @property
    def remaining_time_seconds(self):
        from django.utils import timezone
        
        if not self.start_time:
            return self.assessment.duration_minutes * 60
            
        elapsed = timezone.now() - self.start_time
        remaining = (self.assessment.duration_minutes * 60) - elapsed.total_seconds()
        return max(0, int(remaining))

class QuestionResponse(models.Model):
    session = models.ForeignKey(AssessmentSession, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_data = models.JSONField()
    is_bookmarked = models.BooleanField(default=False)
    response_time = models.DateTimeField(auto_now=True)
    is_correct = models.BooleanField(null=True)

    class Meta:
        unique_together = ['session', 'question']
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django_quill.fields import QuillField
from assessment.models import Assessment, Section, AssessmentSession
from question_bank.models import Question

User = get_user_model()

class ReportConfiguration(models.Model):
    REPORT_TYPES = [
        ('descriptive', 'Descriptive'),
        ('interpretative', 'Interpretative'),
        ('group', 'Group'),
        ('typological', 'Typological'),
        ('question_level', 'Question Level'),
    ]
    
    SCORE_CONVERSION = [
        ('percentage', 'Percentage'),
        ('percentile', 'Percentile'),
        ('sten', 'STEN'),
        ('stenine', 'STENINE'),
        ('raw', 'Raw Score'),
    ]
    
    SCORE_LEVELS = [
        ('level_0', 'Level 0'),
        ('level_1', 'Level 1'),
        ('level_2', 'Level 2'),
        ('question_level', 'Question Level'),
    ]
    
    # General Information
    title = models.CharField(max_length=255)
    objectives = QuillField(null=True, blank=True)
    description = QuillField(null=True, blank=True)
    description_img = models.ImageField(upload_to='report_images/', blank=True, null=True)
    
    # Report Configuration
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='report_configurations')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    score_level = models.JSONField(default=list, help_text="Selected score levels")
    score_conversion = models.CharField(max_length=20, choices=SCORE_CONVERSION, default='percentage')
    
    # For group reports
    # candidate_list = models.JSONField(default=list, blank=True, null=True)
    candidates = models.ManyToManyField(User, blank=True, related_name='report_configurations')
    
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add this field for typological reports
    type_code_count = models.PositiveIntegerField(default=4, help_text="Number of contrast variables to include in type code")

    def __str__(self):
        return f"{self.title} - {self.get_report_type_display()} ({self.assessment.title})"
    
    def save(self, *args, **kwargs):
        # If this is the first configuration for this assessment, make it default
        if not ReportConfiguration.objects.filter(assessment=self.assessment).exists():
            self.is_default = True
        # Ensure only one default configuration per assessment
        elif self.is_default:
            ReportConfiguration.objects.filter(
                assessment=self.assessment, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    @property
    def has_cutoffs(self):
        return self.report_type == 'descriptive'
    
    @property
    def has_bands(self):
        return self.report_type == 'interpretative'
    
    @property
    def has_contrast_variables(self):
        return self.report_type == 'typological'
    
    @property
    def is_group_report(self):
        return self.report_type == 'group'
    
    @property
    def is_question_level_report(self):
        return self.report_type == 'question_level'

class Cutoff(models.Model):
    configuration = models.ForeignKey(ReportConfiguration, on_delete=models.CASCADE, related_name='cutoffs')
    assessment_section = models.ForeignKey(Section, on_delete=models.CASCADE)
    cutoff_score = models.DecimalField(max_digits=5, decimal_places=2)
    cutoff_label = models.CharField(max_length=100)
    above_cutoff_description = QuillField(null=True, blank=True)
    below_cutoff_description = QuillField(null=True, blank=True)
    
    class Meta:
        unique_together = ['configuration', 'assessment_section']
    
    def __str__(self):
        return f"{self.assessment_section.title} - {self.cutoff_score}"

class Band(models.Model):
    configuration = models.ForeignKey(ReportConfiguration, on_delete=models.CASCADE, related_name='bands')
    assessment_section = models.ForeignKey(Section, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    min_range = models.DecimalField(max_digits=5, decimal_places=2)
    max_range = models.DecimalField(max_digits=5, decimal_places=2)
    color = models.CharField(max_length=20, default="#007bff")
    label = models.CharField(max_length=100)
    description = QuillField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.assessment_section.title} - {self.name} ({self.min_range}-{self.max_range})"
    
    def is_in_range(self, score):
        return self.min_range <= score <= self.max_range
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Check if the range overlaps with existing bands for the same section
        overlapping_bands = Band.objects.filter(
            configuration=self.configuration,
            assessment_section=self.assessment_section,
            min_range__lte=self.max_range,
            max_range__gte=self.min_range
        ).exclude(id=self.id)
        
        if overlapping_bands.exists():
            raise ValidationError(f"Band range overlaps with existing range: {overlapping_bands.first()}")


class ContrastVariable(models.Model):
    configuration = models.ForeignKey(ReportConfiguration, on_delete=models.CASCADE, related_name='contrast_variables')
    
    # Reference to the subcategory instead of assessment section
    subcategory = models.CharField(max_length=255, blank=True, null=True, help_text="Reference to question subcategory")
    
    # Name (can be custom or default to subcategory name)
    name = models.CharField(max_length=100)
    
    # Code for type generation
    code = models.CharField(max_length=10)
    
    # Color for display
    color = models.CharField(max_length=20, default="#007bff")
    
    # Description for reporting
    description = QuillField(null=True, blank=True)
    
    class Meta:
        unique_together = ['configuration', 'subcategory']
    
    def __str__(self):
        return f"{self.configuration.title} - {self.name} ({self.code})"

class TypeBand(models.Model):
    configuration = models.ForeignKey(ReportConfiguration, on_delete=models.CASCADE, related_name='type_bands')
    contrast_variable = models.ForeignKey(ContrastVariable, on_delete=models.CASCADE, related_name='bands')
    name = models.CharField(max_length=100)
    min_range = models.DecimalField(max_digits=5, decimal_places=2)
    max_range = models.DecimalField(max_digits=5, decimal_places=2)
    color = models.CharField(max_length=20, default="#007bff")
    label = models.CharField(max_length=100)
    description = QuillField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.contrast_variable.name} - {self.name} ({self.min_range}-{self.max_range})"
    
    def is_in_range(self, score):
        return self.min_range <= score <= self.max_range
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Check if the range overlaps with existing bands for the same contrast variable
        overlapping_bands = TypeBand.objects.filter(
            configuration=self.configuration,
            contrast_variable=self.contrast_variable,
            min_range__lte=self.max_range,
            max_range__gte=self.min_range
        ).exclude(id=self.id)
        
        if overlapping_bands.exists():
            raise ValidationError(f"Band range overlaps with existing range: {overlapping_bands.first()}")


class AssessmentBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)
    report_count = models.PositiveIntegerField(default=1)
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment details
    rzp_payment_id = models.CharField(max_length=100, blank=True, null=True)
    rzp_order_id = models.CharField(max_length=100, blank=True, null=True)
    rzp_signature = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.user.email} - {self.assessment.title}"


class GeneratedReport(models.Model):
    configuration = models.ForeignKey(ReportConfiguration, on_delete=models.CASCADE)
    assessment_session = models.ForeignKey(AssessmentSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    report_file = models.FileField(upload_to='generated_reports/%Y/%m/%d/', null=True, blank=True)
    
    class Meta:
        unique_together = ['configuration', 'assessment_session']
    
    def __str__(self):
        return f"{self.configuration.title} - {self.user.email} - {self.generated_at}"

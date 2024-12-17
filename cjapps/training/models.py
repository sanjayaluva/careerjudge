from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.
from django.core.validators import FileExtensionValidator

from tree_queries.models import TreeNode
from tree_queries.query import TreeQuerySet


class Category(models.Model):
    name = models.CharField(max_length=255, blank=False)
    desc = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name
        
    class Meta():
        permissions = (
            ("training_category_add", "Can Add Training category"),
            ("training_category_change", "Can Change Training category"),
            ("training_category_view", "Can View Training category"),
            ("training_category_delete", "Can Delete Training category"),
        )
        default_permissions = ()


class Training(models.Model):
    TYPE_SCHEDULED = 1
    TYPE_NONSCHEDULED = 0
    TYPE_CHOICES = (
        (TYPE_SCHEDULED, 'Scheduled'),
        (TYPE_NONSCHEDULED, 'Non Scheduled'),
    )
    DURATION_HOURS = 1
    DURATION_DAYS = 2
    DURATION_WEEKS = 3
    DURATION_MONTHS = 4
    DURATION_TYPE_CHOICES = {
        DURATION_HOURS: 'Hours',
        DURATION_DAYS: 'Days',
        DURATION_WEEKS: 'Weeks',
        DURATION_MONTHS: 'Months',
    }
    title = models.CharField(_('Training Title'), max_length=255, blank=False, null=True)
    type = models.IntegerField(_('Training Type'), choices=TYPE_CHOICES, null=True, default=TYPE_SCHEDULED)
    duration = models.IntegerField(_('Course Duration'), blank=True, null=True)
    duration_type = models.IntegerField(_('Duration Type'), choices=DURATION_TYPE_CHOICES, blank=True, null=True, default=DURATION_DAYS)
    objectives = models.TextField(_('Training Objectives'), max_length=500, blank=True, null=True)
    desc_text = models.TextField(_('Description Text'), max_length=500, blank=True, null=True)
    desc_img = models.ImageField(_('Description Image'), upload_to='training/', blank=True, null=True)
    frequency = models.TextField(_('Training Frequency'), blank=True, null=True)
    # status = models.FileField(_('Training Link'), null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="training")
    amount = models.CharField(_('Training Amount'), max_length=255, null=True)
    # question = models.TextField(_('Add Questions'), null=True, blank=True)
    # answer = models.TextField(_('Answer Options'), null=True, blank=True)
    # answer_desc = models.TextField(_('Answer Description'), null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    setup_complete = models.BooleanField(default=False)
    active = models.BooleanField(default=False)

    def duration_str(self):
        post_str = self.DURATION_TYPE_CHOICES[self.duration_type]
        return f"{self.duration} {post_str}" if self.type == self.TYPE_SCHEDULED else 'Nil'

    def __str__(self):
        return self.title

    class Meta():
        # permissions = (
        #     ("counselling_category_list", "Can view Counselling category"),
        # )
        default_permissions = ('view', 'add', 'change', 'delete')


class NodeQuerySet(TreeQuerySet):
    def active(self):
        return self.filter(active=True)

    def training_structure(self, training=None):
        return self.filter(training=training)

class Node(TreeNode):
    MODULE = 'module'
    LESSON = 'lesson'
    TOPIC = 'topic'
    SUBTOPIC = 'subtopic'
    SESSION = 'session'
    CONTENT = 'content'
    ASSIGNMENT = 'assignment'
    ASSESSMENT = 'assessment'
    LIVESESSION = 'livesession'
    TYPE_CHOICES = (
        (MODULE, 'Module'),
        (LESSON, 'Lesson'),
        (TOPIC, 'Topic'),
        (SUBTOPIC, 'Subtopic'),
        (SESSION, 'Session'),
        (CONTENT, 'Content'),
        (ASSIGNMENT, 'Assignment'),
        (ASSESSMENT, 'Assessment'),
        (LIVESESSION, 'Live Session'),
    )

    STATUS_CREATED = 0
    STATUS_STARTED = 1
    STATUS_COMPLETED = 2
    STATUS_CHOICES = (
        (STATUS_CREATED, 'Created'),
        (STATUS_STARTED, 'Started'),
        (STATUS_COMPLETED, 'Completed'),
    )
    text = models.CharField(max_length=255, blank=False)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES, default=MODULE, null=True, blank=True)
    order = models.PositiveIntegerField(default=0, null=True, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_CREATED, blank=True, null=True)
    active = models.BooleanField(default=False)
    training = models.ForeignKey(Training, on_delete=models.CASCADE, default=None, null=True, blank=True, related_name="modules") #
    ref_id = models.BigIntegerField(null=True, blank=True)

    objects = NodeQuerySet.as_manager()

    def get_id(self):
        return self.type + '-' + str(self.id)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text

class Session(models.Model):
    STATUS_CREATED = 0
    STATUS_STARTED = 1
    STATUS_COMPLETED = 2
    STATUS_CHOICES = (
        (STATUS_CREATED, 'Created'),
        (STATUS_STARTED, 'Started'),
        (STATUS_COMPLETED, 'Completed'),
    )

    DURATION_HOURS = 1
    DURATION_DAYS = 2
    DURATION_WEEKS = 3
    DURATION_MONTHS = 4
    DURATION_TYPE_CHOICES = {
        DURATION_HOURS: 'Hours',
        DURATION_DAYS: 'Days',
        DURATION_WEEKS: 'Weeks',
        DURATION_MONTHS: 'Months',
    }
    name = models.CharField(max_length=255, blank=False)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_CREATED, blank=True, null=True)
    training = models.ForeignKey(Training, on_delete=models.CASCADE, null=True, related_name="sessions")
    node = models.ForeignKey(Node, on_delete=models.CASCADE, null=True, related_name="session")
    duration = models.IntegerField(blank=True, null=True)
    duration_type = models.IntegerField(_('Type'), choices=DURATION_TYPE_CHOICES, default=DURATION_HOURS)
    # start_time = models.DateTimeField(blank=True, null=True)
    # end_time = models.DateTimeField(blank=True, null=True)
    objectives = models.TextField(_('Objectives of Session'), max_length=500, blank=True, null=True)
    live = models.BooleanField(default=False)
    # main = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    mandatory = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta():
        default_permissions = ()
        # permissions = ()

# class Module(TreeNode):
#     STATUS_CREATED = 0
#     STATUS_STARTED = 1
#     STATUS_COMPLETED = 2
#     STATUS_CHOICES = (
#         (STATUS_CREATED, 'Created'),
#         (STATUS_STARTED, 'Started'),
#         (STATUS_COMPLETED, 'Completed'),
#     )
#     name = models.CharField(_('Name'), max_length=255)
#     status = models.IntegerField(_('Status'), choices=STATUS_CHOICES, default=STATUS_CREATED, blank=True, null=True)
#     # training = models.ForeignKey(Training, on_delete=models.CASCADE, null=True, related_name="modules")

#     def __str__(self):
#         return self.name

#     class Meta():
#         default_permissions = ()
#         # permissions = ()

# class Lesson(TreeNode):
#     STATUS_CREATED = 0
#     STATUS_STARTED = 1
#     STATUS_COMPLETED = 2
#     STATUS_CHOICES = (
#         (STATUS_CREATED, 'Created'),
#         (STATUS_STARTED, 'Started'),
#         (STATUS_COMPLETED, 'Completed'),
#     )
#     name = models.CharField(_('Name'), max_length=255)
#     status = models.IntegerField(_('Status'), choices=STATUS_CHOICES, default=STATUS_CREATED, blank=True, null=True)
#     # parent = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, related_name="lessons")

#     def __str__(self):
#         return self.name

#     class Meta():
#         default_permissions = ()
#         # permissions = ()

# class Topic(TreeNode):
#     STATUS_CREATED = 0
#     STATUS_STARTED = 1
#     STATUS_COMPLETED = 2
#     STATUS_CHOICES = (
#         (STATUS_CREATED, 'Created'),
#         (STATUS_STARTED, 'Started'),
#         (STATUS_COMPLETED, 'Completed'),
#     )
#     name = models.CharField(_('Name'), max_length=255)
#     status = models.IntegerField(_('Status'), choices=STATUS_CHOICES, default=STATUS_CREATED, blank=True, null=True)
#     # parent = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, related_name="topics")

#     def __str__(self):
#         return self.name

#     class Meta():
#         default_permissions = ()
#         # permissions = ()

# class SubTopic(TreeNode):
    STATUS_CREATED = 0
    STATUS_STARTED = 1
    STATUS_COMPLETED = 2
    STATUS_CHOICES = (
        (STATUS_CREATED, 'Created'),
        (STATUS_STARTED, 'Started'),
        (STATUS_COMPLETED, 'Completed'),
    )
    name = models.CharField(_('Name'), max_length=255)
    status = models.IntegerField(_('Status'), choices=STATUS_CHOICES, default=STATUS_CREATED, blank=True, null=True)
    # parent = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, related_name="subtopics")

    def __str__(self):
        return self.name

    class Meta():
        default_permissions = ()
        # permissions = ()

class Content(models.Model):
    FORMAT_VIDEO = 'video'
    FORMAT_AUDIO = 'audio'
    FORMAT_TEXT = 'text'
    FORMAT_CHOICES = (
        (FORMAT_VIDEO, 'Video'),
        (FORMAT_AUDIO, 'Audio'),
        (FORMAT_TEXT, 'Text'),
    )
    name = models.CharField(max_length=255, blank=True, null=True)
    file = models.FileField(_('Training Content'), upload_to='training/content', null=True, help_text=_('Supported file formats (Audio, Video & Text) : mp3, wav, ogg, mp4, webm, pdf, doc, docx')) #validators=[FileExtensionValidator(allowed_extensions=['mp3','wav','ogg','mp4','webm', 'pdf', 'doc', 'docx'])], 
    type = models.CharField(_('Content format'), max_length=50, choices=FORMAT_CHOICES, blank=True, null=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, blank=True, null=True, related_name='contents')
    node = models.ForeignKey(Node, on_delete=models.CASCADE, null=True, related_name="content")
    mime = models.CharField(max_length=255, blank=True, null=True)

class Assignment(models.Model):
    STATUS_CREATED = 0
    STATUS_STARTED = 1
    STATUS_COMPLETED = 2
    STATUS_CHOICES = (
        (STATUS_CREATED, 'Created'),
        (STATUS_STARTED, 'Started'),
        (STATUS_COMPLETED, 'Completed'),
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    desc = models.TextField(_('Description'), max_length=500, blank=True, null=True, help_text=_('Add Description and Instruction for Report Submission'))
    submit_report = models.BooleanField(_('Enable Report Submission'), default=False)
    # file = models.FileField(_('Report File'), upload_to='training/assignment', null=True, blank=True, help_text=_('Supported file formats (Text) : doc, docx, pdf')) 
    # feedback = models.TextField(_('Feedback'), max_length=500, blank=True, null=True)
    # score = models.CharField(_('Score'), max_length=100, blank=True, null=True)
    status = models.IntegerField(_('Status'), choices=STATUS_CHOICES, default=STATUS_CREATED, blank=True, null=True)
    mandatory = models.BooleanField(default=False)
    node = models.ForeignKey(Node, on_delete=models.CASCADE, blank=True, null=True, related_name="assignment")
    training = models.ForeignKey(Training, on_delete=models.CASCADE, blank=True, null=True, related_name="assignments")

class Link(models.Model):
    link = models.URLField(_('Link'))
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="links")

# class AssignmentUpload(models.Model):
#     file = models.FileField(_('Report File'), upload_to='training/assignment', null=True, blank=True, help_text=_('Supported file formats (Text) : doc, docx, pdf')) 
#     assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)

# class SummaryLiveSession(models.Model):
#     no_sessions = models.IntegerField(_('No of Live Sessions'), blank=True, null=True)
#     objectives = models.TextField(_('Objectives of Sessions'), max_length=500, blank=True, null=True)
#     schedules = models.

class Booking(models.Model):
    STATUS_BOOKED = 0
    STATUS_COMPLETED = 1
    STATUS_CANCELLED = 2
    STATUS_DELETED = 3
    STATUS_CONFIRMED = 4
    STATUS_SCHEDULED = 5
    STATUS_RESCHEDULED = 6
    STATUS_CHOICES = (
        (STATUS_BOOKED, 'Booked'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_DELETED, 'Deleted'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_RESCHEDULED, 'Rescheduled'),
    )

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="bookings")
    training = models.ForeignKey(Training, on_delete=models.SET_NULL, null=True, related_name="bookings")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="bookings")
    booked = models.DateTimeField(_('Booked on'), auto_now_add=True)
    start_date = models.DateField(_('Training Start Date'), null=True, help_text='Note: Please specify a date within one week time.')

    paid = models.BooleanField(_('Paid'), default=False)
    rzp_payment_id = models.TextField(_('Razorpay Payment ID'), blank=True, null=True)
    rzp_order_id = models.TextField(_('Razorpay Order ID'), blank=True, null=True)
    rzp_signature = models.TextField(_('Razorpay Signature'), blank=True, null=True)
    
    status = models.IntegerField(_('Status'), choices=STATUS_CHOICES, default=STATUS_BOOKED, null=True)
    reason = models.TextField(max_length=500, help_text=_('Reason for Cancellation'), blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta():
        default_permissions = ('add_training', 'cancel_training')

class Tracker(models.Model):
    """ User Training Sessions """

    # user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="trackers")
    booking = models.OneToOneField(Booking, on_delete=models.SET_NULL, null=True, related_name="tracker")
    started = models.BooleanField(_('Training started'), default=False)
    started_on = models.DateTimeField(_('Started on'), auto_now_add=True)
    # node_status = models.JSONField(null=True, blank=True)
    active_node = models.ForeignKey(Node, on_delete=models.SET_NULL, null=True, blank=True, related_name="active_node")
    completed = models.BooleanField(_('Completed'), default=False)


class TrackAssignment(models.Model):
    tracker = models.OneToOneField(Tracker, on_delete=models.SET_NULL, null=True, related_name="tracker_assignment")
    assignment = models.OneToOneField(Assignment, on_delete=models.SET_NULL, null=True, related_name="tracker_assignment")

    file = models.FileField(_('Report File'), upload_to='training/assignment', null=True, blank=True, help_text=_('Supported file formats (Text) : doc, docx, pdf')) 
    feedback = models.TextField(_('Feedback'), max_length=500, blank=True, null=True)
    score = models.CharField(_('Score'), max_length=100, blank=True, null=True)
    completed = models.BooleanField(_('Completed'), default=False)

class TrackLivesession(models.Model):
    tracker = models.OneToOneField(Tracker, on_delete=models.SET_NULL, null=True, related_name="tracker_livesession")
    session = models.OneToOneField(Session, on_delete=models.SET_NULL, blank=True, null=True, related_name='tracker_livesession')
    
    init_schedule = models.BooleanField(_('Initiated Live Session'), default=False)
    trainer_scheduled = models.BooleanField(_('Scheduled Live Session'), default=False)
    start_time = models.DateTimeField(blank=True, null=True)
    duration = models.IntegerField(_('Duration (in minutes)'), blank=True, null=True)
    completed = models.BooleanField(_('Completed'), default=False)
    zoom_response = models.JSONField(_('Zoom Response'), null=True, blank=True)

    # @property
    # def notification_id(self):
    #     # "Returns the person's full name."
    #     return None
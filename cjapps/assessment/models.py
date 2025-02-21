from django.db import models
from django_quill.fields import QuillField

from django.contrib.auth import get_user_model
User = get_user_model()

from question_bank.models import Question
from django.utils import timezone
import json
from collections import defaultdict

class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ('normal', 'Normal Assessment'),
        ('psychometric', 'Psychometric Assessment')
    ]

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
    type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES, default='normal')
    objective = QuillField()
    description = QuillField()
    description_img = models.ImageField(upload_to='assessment_images/', blank=True, null=True)
    instructions = QuillField()
    instructions_img = models.ImageField(upload_to='assessment_images/', blank=True, null=True)
    
    published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    # structure = models.JSONField(default=dict)

    # level_counts = models.JSONField(default=dict)
    # delivery_count = models.JSONField(default=dict)

    display_interval = models.PositiveIntegerField(default=0)
    duration_minutes = models.IntegerField(default=60)  # Default 60 minutes

    def get_total_questions(self):
        def count_questions(section):
            if section is None:
                return 0
            total = 1 if section.question else 0
            for child in section.children.all():
                total += count_questions(child)
            return total
            
        root_sections = self.sections.filter(parent=None)
        return sum(count_questions(section) for section in root_sections)

    def validate_question_types(self, question_ids):
        """Validate questions match assessment type"""
        questions = Question.objects.filter(id__in=question_ids)
        is_psychometric = self.type == 'psychometric'
        
        for question in questions:
            if is_psychometric != question.type.startswith('psy_'):
                return False
        return True
    
class Section(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    is_section = models.BooleanField(default=True)

    question = models.ForeignKey(Question, null=True, blank=True, on_delete=models.SET_NULL)
    right_score = models.PositiveIntegerField(default=1)
    wrong_score = models.PositiveIntegerField(default=0)

    delivery_count = models.PositiveIntegerField(null=True, blank=True)
    timer_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    def get_total_delivery_count(self):
        # Only leaf sections (containing questions) can have delivery counts
        if self.is_section and self.children.exists():
            # Check if any child is a question node
            has_question_children = any(not child.is_section for child in self.children.all())
            if has_question_children:
                return self.delivery_count or 0
            
            # For sections with subsections, sum up children's counts
            return sum(child.get_total_delivery_count() for child in self.children.all())
            
        return 0
    
    def has_parent_timer(self):
        """Check if any parent has timer set"""
        current = self.parent
        while current:
            if current.timer_minutes:
                return True
            current = current.parent
        return False
    
    def get_level(self):
        """Get section level in tree"""
        level = 1
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level
    
    def get_total_timer(self):
        # If this section has timer set, return it
        if self.timer_minutes:
            return self.timer_minutes
            
        # Otherwise sum up children's timers
        return sum(child.get_total_timer() for child in self.children.all())
    
    class Meta:
        ordering = ['order']   

    def get_total_score(self):
        total = 0
        if self.question:
            response = self.question.questionresponse_set.filter(
                session__assessment=self.assessment
            ).first()
            if response:
                total += response.score
                
        for child in self.children.all():
            total += child.get_total_score()
            
        return total 

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

    scores = models.JSONField(default=dict)

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
      
    def calculate_scores(self):
        def calculate_section_scores(section):
            total = 0
            if section.is_section:
                # Calculate scores for child sections
                for child in section.children.all():
                    child_score = calculate_section_scores(child)
                    total += child_score
                    self.scores[f'section_{child.id}'] = child_score
            else:
                # Calculate score for question node
                response = QuestionResponse.objects.filter(
                    session=self,
                    question=section.question
                ).first()
                if response:
                    response.validate_answer()
                    response.calculate_score()
                    total = response.score

            return total

        # Start calculation from root sections
        root_sections = Section.objects.filter(
            assessment=self.assessment,
            parent=None,
            is_section=True
        )

        total_score = 0
        for section in root_sections:
            section_score = calculate_section_scores(section)
            total_score += section_score
            self.scores[f'section_{section.id}'] = section_score

        self.scores['total'] = total_score
        self.save()
        
    def complete_assessment(self):
        self.status = 'completed'
        self.is_completed = True
        self.end_time = timezone.now()
        
        # Calculate scores for all root sections
        self.calculate_scores()
            
        self.save()

class QuestionResponse(models.Model):
    STATUS_CHOICES = [
        ('answered', 'Answered'),
        ('skipped', 'Skipped')  # Covers both empty and explicitly skipped
    ]
    
    session = models.ForeignKey(AssessmentSession, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='skipped')
    answer_data = models.JSONField(default=dict)
    response_time = models.DateTimeField(auto_now=True)
    is_bookmarked = models.BooleanField(default=False)
    is_correct = models.BooleanField(null=True)
    
    score = models.IntegerField(default=0)  # Add this field to store individual question scores
    psy_score = models.JSONField(default=dict)

    class Meta:
        unique_together = ['session', 'question']
    
    def calculate_score(self):
        if self.question.type.startswith('psy'):
            self.psy_score = self.calculate_psy_score()
        else:
            self.score = self.calculate_normal_score()
        self.save()

    def calculate_normal_score(self):
        if self.is_correct:
            section = Section.objects.filter(question=self.question).first()
            return section.right_score or self.question.right_score or 1
        else:
            section = Section.objects.filter(question=self.question).first()
            return -(section.wrong_score or self.question.wrong_score or 0)
    
    def calculate_psy_score(self):
        if self.question.type == 'psy_rating':
            return self.calculate_rating_score()
        elif self.question.type == 'psy_ranking':
            return self.calculate_ranking_score()
        elif self.question.type == 'psy_rank_rate':
            return self.calculate_rank_rate_score()
        elif self.question.type == 'psy_forced_one':
            return self.calculate_forced_choice_score()
        elif self.question.type == 'psy_forced_two':
            return self.calculate_forced_choice_score(with_rating=True)
        

    def calculate_rating_score(self):
        return {'rating': self.answer_data.get('rating', 0)}
    
    def calculate_ranking_score(self):
        structure = json.loads(self.question.ranking_structure)
        rankings = self.answer_data.get('rankings', {})

        # Initialize score containers
        scores = {
            'categories': defaultdict(int),
            'subcategories': defaultdict(int),
            'statements': defaultdict(int)
        }

        # Build node lookup maps
        statement_map = {}
        category_map = {}
        subcategory_map = {}

        # Map all nodes by ID and store their text
        for category in structure['leftTree']:
            if category['type'] == 'category':
                category_map[category['id']] = {'text': category['text']}
                for child in category['children']:
                    if child['type'] == 'subcategory':
                        subcategory_map[child['id']] = {
                            'node': child,
                            'category_id': category['id'],
                            'text': child['text']
                        }
                        for stmt in child['children']:
                            statement_map[stmt['id']] = {
                                'node': stmt,
                                'category_id': category['id'],
                                'subcategory_id': child['id'],
                                'text': stmt['text']
                            }
                    elif child['type'] == 'statement':
                        statement_map[child['id']] = {
                            'node': child,
                            'category_id': category['id'],
                            'text': child['text']
                        }

        # Calculate reverse scoring slab
        total_categories = len(category_map)
        score_slab = {rank: total_categories - rank + 1 for rank in range(1, total_categories + 1)}

        # Calculate scores using node references
        for stmt_id, rank in rankings.items():
            score = score_slab[rank]
            stmt_info = statement_map.get(stmt_id)

            if stmt_info:
                scores['statements'][stmt_id] = score
                scores['categories'][stmt_info['category_id']] += score

                if 'subcategory_id' in stmt_info:
                    scores['subcategories'][stmt_info['subcategory_id']] += score

        # Store detailed scoring information in a single structure
        ranking_details = {
            'score_slab': score_slab,
            'scores': {
                'category_scores': dict(scores['categories']),
                'subcategory_scores': dict(scores['subcategories']),
                'statement_scores': dict(scores['statements']),
            },
            'maps': {
                'statement_map': statement_map,
                'subcategory_map': subcategory_map,
                'category_map': category_map
            }
        }

        return ranking_details
    
    def calculate_rank_rate_score(self):
        structure = json.loads(self.question.ranking_structure)
        rankings = self.answer_data.get('rankings', {})
        ratings = self.answer_data.get('ratings', {})

        # Initialize score containers
        scores = {
            'categories': defaultdict(int),
            'subcategories': defaultdict(int),
            'statements': defaultdict(int)
        }

        # Build node lookup maps
        statement_map = {}
        category_map = {}
        subcategory_map = {}

        # Map all nodes by ID and store their text
        for category in structure['leftTree']:
            if category['type'] == 'category':
                category_map[category['id']] = {'text': category['text']}
                for child in category['children']:
                    if child['type'] == 'subcategory':
                        subcategory_map[child['id']] = {
                            'node': child,
                            'category_id': category['id'],
                            'text': child['text']
                        }
                        for stmt in child['children']:
                            statement_map[stmt['id']] = {
                                'node': stmt,
                                'category_id': category['id'],
                                'subcategory_id': child['id'],
                                'text': stmt['text']
                            }
                    elif child['type'] == 'statement':
                        statement_map[child['id']] = {
                            'node': child,
                            'category_id': category['id'],
                            'text': child['text']
                        }

        # Calculate reverse scoring slab
        total_categories = len(category_map)
        score_slab = {rank: total_categories - rank + 1 for rank in range(1, total_categories + 1)}

        # Calculate scores using node references
        for stmt_id, rank in rankings.items():
            rating = ratings.get(stmt_id, 0)
            rank_score = score_slab[rank]
            score = rank_score * rating
            stmt_info = statement_map.get(stmt_id)

            if stmt_info:
                scores['statements'][stmt_id] = score
                scores['categories'][stmt_info['category_id']] += score

                if 'subcategory_id' in stmt_info:
                    scores['subcategories'][stmt_info['subcategory_id']] += score

        # Store detailed scoring information in a single structure
        ranking_details = {
            'score_slab': score_slab,
            'scores': {
                'category_scores': dict(scores['categories']),
                'subcategory_scores': dict(scores['subcategories']),
                'statement_scores': dict(scores['statements']),
            },
            'maps': {
                'statement_map': statement_map,
                'subcategory_map': subcategory_map,
                'category_map': category_map
            }
        }

        return ranking_details

    def calculate_forced_choice_score(self, with_rating=False):
        structure = json.loads(self.question.ranking_structure)
        choices = self.answer_data.get('choices', {})
        ratings = self.answer_data.get('ratings', {}) if with_rating else {}
        statements = self.answer_data.get('statements', {})

        scores = {
            'categories': defaultdict(int),
            'subcategories': defaultdict(int),
            'statements': defaultdict(int)
        }

        # Build node maps
        statement_map = {}
        category_map = {}
        subcategory_map = {}

        # Map nodes
        for category in structure['leftTree']:
            category_map[category['id']] = {'text': category['text']}
            for child in category['children']:
                if child['type'] == 'subcategory':
                    subcategory_map[child['id']] = {
                        'category_id': category['id'],
                        'text': child['text']
                    }
                    for stmt in child['children']:
                        statement_map[stmt['id']] = {
                            'category_id': category['id'],
                            'subcategory_id': child['id'],
                            'text': stmt['text']
                        }
                elif child['type'] == 'statement':
                    statement_map[child['id']] = {
                        'category_id': category['id'],
                        'text': child['text']
                    }

        # Calculate scores
        for stmt_id, stmt_data in statements.items():
            stmt_info = statement_map.get(stmt_id)
            if stmt_info:
                score = stmt_data['score']
                scores['statements'][stmt_id] = score
                scores['categories'][stmt_info['category_id']] += score
                if 'subcategory_id' in stmt_info:
                    scores['subcategories'][stmt_info['subcategory_id']] += score

        return {
            'scores': {
                'category_scores': dict(scores['categories']),
                'subcategory_scores': dict(scores['subcategories']),
                'statement_scores': dict(scores['statements']),
            },
            'maps': {
                'statement_map': statement_map,
                'subcategory_map': subcategory_map,
                'category_map': category_map
            }
        }
    
    def validate_answer(self):
        # If no meaningful answer data, treat as skipped
        if not self.answer_data or self.status == 'skipped':
            self.is_correct = False
            self.score = 0
            self.save()
            return

        # Proceed with normal validation for answered questions
        if self.question.type.startswith('mcq'):
            self.is_correct = self._validate_mcq()
        elif self.question.type.startswith('fib'):
            self.is_correct = self._validate_fib()
        elif self.question.type.startswith('cus'):
            self.is_correct = self._validate_custom()
        elif self.question.type.startswith('psy'):
            self.is_correct = self._validate_psy()
        self.save()

    def _validate_mcq(self):
        selected = self.answer_data.get('selected_option')
        correct = self.question.options.filter(is_correct=True).first()
        return selected == str(correct.id) if correct else False

    def _validate_fib(self):
        user_answers = self.answer_data.get('answers', [])
        correct_answers, _ = self.question.get_fib_info()
        # return all(
        #     user_answer.lower().strip() == correct_answer.lower().strip()
        #     for user_answer, correct_answer in zip(user_answers, correct_answers)
        # )
        if self.question.case_sensitive:
            return all(
                user_answer.strip() == correct_answer.strip()
                for user_answer, correct_answer in zip(user_answers, correct_answers)
            )
        else:
            return all(
                user_answer.lower().strip() == correct_answer.lower().strip()
                for user_answer, correct_answer in zip(user_answers, correct_answers)
            )

    def _validate_custom(self):
        if self.question.type == 'cus_hotspot_single':
            selected = self.answer_data.get('selected_hotspots', [])
            correct_hotspots = self.question.hotspot_items
            return len(selected) == 1 and any(
                spot['hotspotId'] == selected[0]['hotspotId'] 
                for spot in correct_hotspots if spot.get('correct')
            )
        elif self.question.type == 'cus_hotspot_multiple':
            selected = self.answer_data.get('selected_hotspots', [])
            correct_hotspots = self.question.hotspot_items
            selected_ids = {spot['hotspotId'] for spot in selected}
            correct_ids = {spot['hotspotId'] for spot in correct_hotspots if spot.get('correct')}
            return selected_ids == correct_ids
        elif self.question.type == 'cus_grid':
            selected_cells = self.answer_data.get('selected_cells', [])
            correct_cells = [opt.id for opt in self.question.grid_options.filter(is_correct=True)]
            return set(selected_cells) == set(correct_cells)
        elif self.question.type == 'cus_match':
            user_matches = self.answer_data.get('matches', {})
            correct_matches = {str(item.id): item.right_item for item in self.question.match_options.all()}
            return user_matches == correct_matches
        return False
    
    def _validate_psy(self):
        if self.question.type == 'psy_rating':
            return True if self.answer_data.get('rating') is not None else False
        elif self.question.type == 'psy_ranking':
            structure = json.loads(self.question.ranking_structure)
            
            # Get all statement IDs from rankgroups
            required_statements = set()
            for rankgroup in structure['rightTree']:
                if rankgroup['type'] == 'rankgroup':
                    for stmt in rankgroup['children']:
                        if stmt['type'] == 'statement':
                            required_statements.add(stmt['data']['originalId'])
            
            # Validate user rankings
            rankings = self.answer_data.get('rankings', {})
            ranked_statements = set(rankings.keys())
            
            # Check if all required statements are ranked with unique values
            # rank_values = list(rankings.values())
            return ranked_statements == required_statements #and len(rank_values) == len(set(rank_values))

        return False
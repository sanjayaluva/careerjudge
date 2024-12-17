from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Assessment, AssessmentSession, StudentAnswer, Section
from .forms import AssessmentForm#, VariableForm, QuestionAssignmentForm, ScoreSettingForm, DisplayParametersForm
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from .forms import QuestionSearchForm
from question_bank.models import Question
from . import models
from django.db import transaction

def assessment_list(request):
    assessments = Assessment.objects.filter(created_by=request.user).all()
    paginator = Paginator(assessments, 10)  # Show 10 assessments per page
    page = request.GET.get('page')
    try:
        assessments = paginator.page(page)
    except PageNotAnInteger:
        assessments = paginator.page(1)
    except EmptyPage:
        assessments = paginator.page(paginator.num_pages)
    return render(request, 'assessment/assessment_list.html', {'assessments': assessments})

def assessment_create(request):
    if request.method == 'POST':
        form = AssessmentForm(request.POST, request.FILES)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.created_by = request.user
            assessment.save()
            return redirect('assessment_update', pk=assessment.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = AssessmentForm()
    return render(request, 'assessment/assessment_form.html', { 'form': form })

def assessment_update(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    if request.method == 'POST':
        form = AssessmentForm(request.POST, request.FILES, instance=assessment)
        if form.is_valid():
            form.save()
            return redirect('assessment_list')
    else:
        form = AssessmentForm(instance=assessment)
        search_form = QuestionSearchForm()
    return render(request, 'assessment/assessment_form.html', { 'form': form, 'assessment': assessment, 'search_form': search_form })

def assessment_delete(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    if request.method == 'POST':
        assessment.delete()
        return redirect('assessment_list')
    return redirect('assessment_list')

@csrf_exempt
def assessment_structure(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'create':
            return create_node(assessment, data)
        elif action == 'edit':
            return edit_node(assessment, data)
        elif action == 'delete':
            return delete_node(assessment, data)
        elif action == 'move':
            return move_node(assessment, data)
        elif action == 'level':
            return set_level_count(assessment, data)
    
    structure = build_structure(assessment)
    return JsonResponse({'structure': structure, 'level_counts': assessment.level_counts}, safe=False)

def build_structure(assessment):
    def recursive_build(node):
        children = []
        for child in node.children.all():
            children.append(recursive_build(child))
        
        return {
            'id': str(node.id),
            'text': node.title if node.is_section else node.question.title,
            'type': 'section' if node.is_section else 'question',
            'children': children,
            'data': {'questionId': node.question.id} if not node.is_section else {},
            'li_attr': { 'class': 'question-node' } if not node.is_section else {}
        }
    
    return [recursive_build(section) for section in assessment.sections.filter(parent=None)]

def set_level_count(assessment, data):
    assessment.level_counts = data['level_counts']
    assessment.save()
    return JsonResponse({'status': 'success'}, safe=False)

def create_node(assessment, data):
    parent = models.Section.objects.get(id=data['parent_id']) if data['parent_id'] else None
    node = models.Section.objects.create(
        assessment=assessment,
        title=data['text'],
        order=data['order'],
        parent=parent,
        is_section=data['type'] == 'section',
        question_id=data['question_id'] if data['type'] == 'question' else None
    )
    return JsonResponse({'id': str(node.id)}, safe=False)

def edit_node(assessment, data):
    node = models.Section.objects.get(id=data['id'])
    node.title = data['text']
    node.save()
    return JsonResponse({'status': 'success'}, safe=False)

def delete_node(assessment, data):
    models.Section.objects.get(id=data['id']).delete()
    return JsonResponse({'status': 'success'}, safe=False)

def move_node(assessment, data):
    node = models.Section.objects.get(id=data['id'])
    new_parent_id = data['parent'] if data['parent'] != '#' else None
    node.parent_id = new_parent_id
    node.order = data['position']
    node.save()
    return JsonResponse({'status': 'success'}, safe=False)


def search_questions(request):
    form = QuestionSearchForm(request.GET)
    questions = Question.objects.all()

    if form.is_valid():
        if form.cleaned_data['title']:
            questions = questions.filter(title__icontains=form.cleaned_data['title'])
        if form.cleaned_data['type']:
            questions = questions.filter(type=form.cleaned_data['type'])
        if form.cleaned_data['category']:
            questions = questions.filter(category=form.cleaned_data['category'])
        if form.cleaned_data['difficulty_level']:
            questions = questions.filter(difficulty_level=form.cleaned_data['difficulty_level'])
        if form.cleaned_data['cognitive_level']:
            questions = questions.filter(cognitive_level=form.cleaned_data['cognitive_level'])
        if form.cleaned_data['exposure_limit']:
            questions = questions.filter(exposure_limit__lte=form.cleaned_data['exposure_limit'])

    #questions_data = list(questions.values('id', 'title', 'type', 'difficulty_level'))
    questions_data = [
        {
            'id': q.id,
            'title': q.title,
            'type': q.get_type_display() or '-',
            'difficulty_level': q.get_difficulty_level_display() or '-'
        }
        for q in questions
    ]
    return JsonResponse(questions_data, safe=False)

def get_question_options(request, pk):
    section = models.Section.objects.get(id=pk)
    data = {
        'id': section.id,
        # 'title': section.title,
        # 'question_id': section.question_id,
        # 'question_title': question.title,
        'right_score': section.right_score,
        'wrong_score': section.wrong_score,
    }
    

    return JsonResponse(data, safe=False)

def set_question_scores(request, pk):
    section = models.Section.objects.get(id=pk)
    data = json.loads(request.body)
    # question = Question.objects.get(id=section.question_id)
    
    section.right_score = data['right_score']
    section.wrong_score = data['wrong_score']
    section.save()

    return JsonResponse({'status': 'success'})


def start_assessment(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)
    session = AssessmentSession.objects.create(
        student=request.user,
        assessment=assessment,
        remaining_time=assessment.duration_minutes * 60  # Convert minutes to seconds
    )
    return redirect('take_assessment', session_id=session.id)

def take_assessment(request, session_id):
    session = get_object_or_404(AssessmentSession, id=session_id)
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        answer = request.POST.get('answer')
        question = get_object_or_404(Question, id=question_id)
        StudentAnswer.objects.create(
            session=session,
            question=question,
            answer=answer,
            question_type=question.question_type
        )
        # Handle navigation logic here (e.g., next question)
    # Render the assessment-taking page
    return render(request, 'assessment/take_assessment.html', {'session': session})

def submit_assessment(request, session_id):
    session = get_object_or_404(AssessmentSession, id=session_id)
    session.is_completed = True
    session.end_time = timezone.now()
    session.save()
    return redirect('assessment_result', session_id=session.id)

# from django.shortcuts import render, get_object_or_404, redirect
# from django.http import JsonResponse
from django.utils import timezone
# import json
from django.db.models.functions import Concat
from django.db.models import F, Value, CharField, Case, When

def start_assessment(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)
    
    # Check if there's an existing incomplete session
    existing_session = AssessmentSession.objects.filter(
        student=request.user,
        assessment=assessment,
        is_completed=False
    ).first()
    
    if (existing_session):
        return redirect('take_assessment', session_id=existing_session.id)
    
    # Create new session
    session = AssessmentSession.objects.create(
        student=request.user,
        assessment=assessment,
        current_section=assessment.sections.filter(parent=None).first()
    )
    
    return redirect('take_assessment', session_id=session.id)

def get_section_questions(section):
    """Recursively get questions from section and its children"""
    questions = []
    
    # If this section has questions (leaf section)
    if section.question:
        questions.append(section.question)
        
    # Get questions from child sections
    for child_section in section.children.all():
        questions.extend(get_section_questions(child_section))
        
    return questions

# In views.py
# def take_assessment(request, session_id):
#     global_index = 0

#     def build_section_hierarchy(section):
#         nonlocal global_index
#         section_data = {
#             'id': section.id,
#             'title': section.title,
#             'is_section': section.is_section,
#             'children': [],
#             'questions': []
#         }
        
#         # Add questions if this is a leaf section
#         if section.question:
#             section_data['questions'].append({
#                 'question_id': section.question.id,
#                 'title': section.question.title,
#                 'type': section.question.type,
#                 'text': section.question.text.html if section.question.text else '',
#                 'instructions': section.question.instructions.html if section.question.instructions else '',
#                 'flash_interval': section.question.flash_interval,
#                 'category_id': section.question.category.id if section.question.category else None,
#                 'category_name': section.question.category.name if section.question.category else '',
#                 'difficulty_level': section.question.difficulty_level,
#                 'cognitive_level': section.question.cognitive_level,
#                 'objectives': section.question.objectives.html if section.question.objectives else '',
#                 'exposure_limit': section.question.exposure_limit,
#                 'status': section.question.status,
#                 'global_index': global_index

#             })
#             global_index += 1

#         # Add child sections recursively
#         for child in section.children.all():
#             section_data['children'].append(build_section_hierarchy(child))
        
#         return section_data

#     session = AssessmentSession.objects.get(id=session_id)
#     assessment = session.assessment
    
#     assessment_data = {
#         'id': assessment.id,
#         'title': assessment.title,
#         'objective': assessment.objective.html if assessment.objective else '',
#         'description': assessment.description.html if assessment.description else '',
#         'description_img': assessment.description_img.url if assessment.description_img else None,
#         'instructions': assessment.instructions.html if assessment.instructions else '',
#         'instructions_img': assessment.instructions_img.url if assessment.instructions_img else None,
#         'published': assessment.published,
#         'display_interval': assessment.display_interval,
#         'duration_minutes': assessment.duration_minutes,
#         'sections': [],
#         'session': {
#             'id': session.id,
#             'start_time': session.start_time.isoformat(),
#             'end_time': session.end_time.isoformat() if session.end_time else None,
#             # 'status': session.status
#             'is_completed': session.is_completed
#         }
#     }

#     # Build hierarchical section structure
#     for section in assessment.sections.filter(parent=None):
#         section_data = build_section_hierarchy(section)
#         assessment_data['sections'].append(section_data)

#     context = {
#         'assessment_data': assessment_data,
#         'time_remaining': calculate_time_remaining(session)
#     }
    
#     return render(request, 'assessment/assessment_take.html', context)

def take_assessment(request, session_id):
    session = get_object_or_404(AssessmentSession, id=session_id)
    assessment = session.assessment

    assessment_data = {
        'assessment': {
            'id': assessment.id,
            'title': assessment.title,
            'duration_minutes': assessment.duration_minutes,
            'display_interval': assessment.display_interval,
            'instructions': assessment.instructions.html if assessment.instructions else '',
            'description': assessment.description.html if assessment.description else ''
        },
        'session': {
            'id': session.id,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'time_remaining': calculate_time_remaining(session)
        },
        'sections': get_assessment_sections(assessment)
    }

    return render(request, 'assessment/assessment_take.html', {'assessment_data': assessment_data})


def get_assessment_sections(assessment):
    sections = []
    for section in assessment.sections.filter(parent__isnull=True).order_by('order'):
        sections.append(get_section_data(section))
    return sections

def get_section_data(section):
    section_data = {
        'id': section.id,
        'title': section.title,
        'questions': [],
        'subsections': []
    }
    if section.question:
        question = section.question
        section_data['questions'].append({
            'id': question.id,
            'title': question.title,
            'type': question.type,
            'text': question.text.html if question.text else '',
            'instructions': question.instructions.html if question.instructions else '',
            'options': list(question.options.values('id', 'text', 'image', 'is_correct')),
            'flash_items': list(question.flash_options.values()),
            'grid_items': list(question.grid_options.values('id', 'text', 'image', 'row', 'col', 'is_correct')),
            'ranking_options': question.ranking_structure
        })
    for child_section in section.children.all().order_by('order'):
        section_data['subsections'].append(get_section_data(child_section))
    return section_data
    
# def get_assessment_sections(assessment):
#     sections = []
#     for section in assessment.sections.filter(is_section=True):
#         section_data = {
#             'id': section.id,
#             'title': section.title,
#             'questions': []
#         }
#         question_sections = section.get_descendants().filter(question__isnull=False)
#         for q_section in question_sections:
#             question = q_section.question
#             section_data['questions'].append({
#                 'id': question.id,
#                 'title': question.title,
#                 'type': question.type,
#                 'text': question.text.html if question.text else '',
#                 'instructions': question.instructions.html if question.instructions else '',
#                 'options': list(question.options.values('id', 'text', 'image', 'is_correct')),
#                 'flash_items': list(question.flash_options.values()),
#                 'grid_items': list(question.grid_options.values('id', 'text', 'image', 'row', 'col', 'is_correct')),
#                 'ranking_options': question.ranking_structure
#             })
#         sections.append(section_data)
#     return sections

def calculate_time_remaining(session):
    elapsed_time = timezone.now() - session.start_time
    total_time = session.assessment.duration_minutes * 60
    remaining_seconds = total_time - elapsed_time.total_seconds()
    return max(0, int(remaining_seconds))

def save_answer(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
        
    session = get_object_or_404(AssessmentSession, id=session_id)
    data = json.loads(request.body)
    
    StudentAnswer.objects.update_or_create(
        session=session,
        question_id=data['question_id'],
        defaults={'answer': data['answer_data']}
    )
    
    return JsonResponse({'status': 'success'})

def submit_assessment(request, session_id):
    session = get_object_or_404(AssessmentSession, id=session_id)
    session.is_completed = True
    session.end_time = timezone.now()
    session.save()
    
    return redirect('assessment_results', session_id=session.id)

def assessment_results(request, session_id):
    session = get_object_or_404(AssessmentSession, id=session_id)
    answers = StudentAnswer.objects.filter(session=session)
    context = {
        'session': session,
        'answers': answers,
    }
    return render(request, 'assessment/assessment_results.html', context)

# def take_assessment(request, session_id):
#     session = AssessmentSession.objects.get(id=session_id)
#     assessment = session.assessment

#     assessment_data = {
#         'assessment': {
#             'id': assessment.id,
#             'title': assessment.title,
#             'duration_minutes': assessment.duration_minutes,
#             'display_interval': assessment.display_interval,
#             'instructions': assessment.instructions.html if assessment.instructions else '',
#             'description': assessment.description.html if assessment.description else ''
#         },
#         'session': {
#             'id': session.id,
#             'start_time': session.start_time.isoformat(),
#             'end_time': session.end_time.isoformat() if session.end_time else None,
#             'time_remaining': calculate_time_remaining(session)
#         },
#         'sections': get_assessment_sections(assessment)
#     }

#     return render(request, 'assessment/assessment_take.html', {'assessment_data': assessment_data})

# def get_assessment_sections(assessment):
#     sections = []
#     global_index = 0
    
#     for section in assessment.sections.filter(is_section=True):
#         section_data = {
#             'id': section.id,
#             'title': section.title,
#             'questions': []
#         }
        
#         # Get all questions under this section including descendants
#         question_sections = section.get_descendants().filter(question__isnull=False)
#         for q_section in question_sections:
#             question = q_section.question
#             section_data['questions'].append({
#                 'id': question.id,
#                 'title': question.title,
#                 'type': question.type,
#                 'text': question.text.html if question.text else '',
#                 'instructions': question.instructions.html if question.instructions else '',
#                 'timer_interval': question.timer_interval,
#                 'paragraph': question.paragraph.html if question.paragraph else '',
#                 'options': list(question.options.values('id', 'text', 'image', 'is_correct')),
#                 'flash_items': list(question.flash_options.values()),
#                 'grid_items': list(question.grid_options.values('id', 'text', 'image', 'row', 'col', 'is_correct')),
#                 'ranking_options': question.ranking_structure,
#                 'global_index': global_index
#             })
#             global_index += 1
            
#         sections.append(section_data)
    
#     return sections


# def calculate_time_remaining(session):
#     elapsed_time = timezone.now() - session.start_time
#     time_remaining = max(0, session.assessment.duration_minutes * 60 - elapsed_time.seconds)
#     return time_remaining


# def take_assessment(request, session_id):
#     session = AssessmentSession.objects.get(id=session_id)
#     assessment = session.assessment
    
#     # Get assessment structure with required fields
#     assessment_structure = []
#     for section in assessment.sections.filter(parent=None):  # Get root sections
#         questions = get_section_questions(section)
        
#         section_data = {
#             'title': section.title,
#             'questions': [{
#                 'question_id': q.id,
#                 'title': q.title,
#                 'type': q.type, 
#                 'category_id': q.category.id,
#                 'category_name': q.category.name,
#                 'difficulty_level': q.difficulty_level,
#                 'cognitive_level': q.cognitive_level,
#                 'text': q.text.html if q.text else '',
#                 'objectives': q.objectives.html if q.objectives else '',
#                 'instructions': q.instructions.html if q.instructions else '',
#                 'exposure_limit': q.exposure_limit,
#                 'status': q.status,
#                 'global_index': idx
#             } for idx, q in enumerate(questions)]
#         }
#         assessment_structure.append(section_data)

#     # Calculate time remaining
#     elapsed_time = timezone.now() - session.start_time
#     time_remaining = max(0, assessment.duration_minutes * 60 - elapsed_time.seconds)

#     context = {
#         'session': session,
#         'assessment': {
#             'title': assessment.title,
#             'objective': assessment.objective.html if assessment.objective else '',
#             'description': assessment.description.html if assessment.description else '',
#             'description_img': assessment.description_img.url if assessment.description_img else None,
#             'instructions': assessment.instructions.html if assessment.instructions else '',
#             'instructions_img': assessment.instructions_img.url if assessment.instructions_img else None,
#             'published': assessment.published,
#             'display_interval': assessment.display_interval,
#             'duration_minutes': assessment.duration_minutes
#         },
#         'assessment_structure': assessment_structure,
#         'time_remaining': time_remaining,
#         'progress': calculate_progress(session)
#     }
    
#     return render(request, 'assessment/assessment_take.html', context)


# def take_assessment(request, session_id):
#     session = get_object_or_404(AssessmentSession, id=session_id)
#     assessment = session.assessment

#     if session.is_completed:
#         return redirect('assessment_results', session_id=session.id)
    
#     def serialize_section(section):
#         # Get all questions from this section and its subsections
#         questions_list = []
#         sections_to_check = [section]
        
#         while sections_to_check:
#             current_section = sections_to_check.pop()
#             if current_section.question:
#                 questions_list.append({
#                     'id': current_section.id,
#                     'question_id': current_section.question_id,
#                     'title': current_section.question.title,
#                     'type': current_section.question.get_type_display(),
#                     'section_id': current_section.id  # Keep section reference if needed
#                 })
#             sections_to_check.extend(current_section.children.all())
        
#         # Apply random order if specified
#         if session.assessment.display_order == 'random':
#             shuffle(questions_list)

#         return {
#             'id': section.id,
#             'title': section.title,
#             'questions': questions_list
#         }

#     # Get all main sections
#     assessment_structure = []
#     for section in session.assessment.sections.filter(parent=None):
#         assessment_structure.append(serialize_section(section))

#     all_questions = []
#     global_index = 0
    
#     for section in assessment_structure:
#         for question in section['questions']:
#             question['global_index'] = global_index
#             all_questions.append(question)
#             global_index += 1

#     context = {
#         'session': session,
#         # 'section': current_section,
#         'all_questions': all_questions,
#         'assessment_structure': assessment_structure,
#         'time_remaining': calculate_remaining_time(session),
#         'progress': calculate_progress(session)
#     }
#     return render(request, 'assessment/assessment_take.html', context)

# def question_detail_api(request, pk):
#     question = get_object_or_404(Question, pk=pk)
    
#     # Get question options based on type
#     options = []
#     if question.type.startswith('mcq'):
#         options = list(question.options.values('id', 'text', 'is_correct'))
    
#     data = {
#         'id': question.id,
#         'title': question.title,
#         'type': question.type,
#         'category': question.category.name if question.category else None,
#         'difficulty_level': question.get_difficulty_level_display(),
#         'cognitive_level': question.get_cognitive_level_display(),
#         'options': options
#     }
    
#     return JsonResponse(data)

def question_detail_api(request, pk):
    question = get_object_or_404(Question, pk=pk)
    
    # Base question data
    # data = {
    #     'id': question.id,
    #     'title': question.title,
    #     'type': question.type,
    #     'category': question.category.name if question.category else None,
    #     'difficulty_level': question.get_difficulty_level_display(),
    #     'cognitive_level': question.get_cognitive_level_display(),
    #     'display_time': question.display_time if hasattr(question, 'display_time') else None,
    # }
    data = {
        'question_id': question.id,
        'title': question.title,
        'type': question.type,
        'category_id': question.category.id,
        'category_name': question.category.name if question.category else None,
        'difficulty_level': question.difficulty_level,
        'cognitive_level': question.cognitive_level,
        'text': question.text.html if question.text else '',
        'objectives': question.objectives.html if question.objectives else '',
        'instructions': question.instructions.html if question.instructions else '',
        'exposure_limit': question.exposure_limit,
        'status': question.status,
    }
    
    # Add type-specific data
    if question.type.startswith('mcq'):
        data['options'] = list(question.options.annotate(
            image_url=Case(
                When(image='', then=Value('')),
                default=Concat(Value('/media/'), F('image'), output_field=CharField()),
            )
        ).values('id', 'text', 'image_url', 'is_correct'))
    if question.type.startswith('fib'):
        data['blanks'] = question.get_fib_options()
    if question.type.endswith('image') or question.type.endswith('mixed'):
        data['image_url'] = question.image.url
    elif question.type.endswith('audio'):
        data['audio_url'] = question.audio.url
    elif question.type.endswith('video'):
        data['video_url'] = question.video.url
    if question.type.endswith('paragraph'):
        data['paragraph'] = question.paragraph.html if question.paragraph else ''
        data['display_time'] = question.paragraph_interval or 60
    elif question.type.endswith('flash'):
        data['flash_items'] = list(question.flash_options.annotate(
            image_url=Case(
                When(image='', then=Value('')),
                default=Concat(Value('/media/'), F('image'), output_field=CharField()),
            )
        ).values('id', 'text', 'image_url'))
        data['flash_time'] = question.flash_interval or 60 #flash_display_time
        data['flash_items_count'] = question.flash_items_count or 0
    
    elif question.type.startswith('cus_hotspot'):
        data['image_url'] = question.image.url
        data['hotspots'] = question.hotspot_items
        data['multiple_selection'] = question.type == 'cus_hotspot_multiple'
    
    elif question.type == 'cus_grid':
        data['grid_items'] = list(question.grid_options.annotate(
            image_url=Case(
                When(image='', then=Value('')),
                default=Concat(Value('/media/'), F('image'), output_field=CharField()),
            )
        ).values('id', 'text', 'image_url', 'row', 'col', 'is_correct'))
        data['grid_size'] = {'rows': question.grid_rows, 'cols': question.grid_cols}
        data['grid_type'] = question.grid_type
    
    elif question.type == 'cus_match':
        data['pairs'] = list(question.match_options.values('id', 'left_item', 'right_item'))
    
    elif question.type.startswith('psy'):
        # data['items'] = list(question.items.values())
        if question.type == 'psy_rating':
            data['rating_options'] = list(question.rating_options.values('id', 'text', 'value'))
        elif question.type == 'psy_ranking':
            data['ranking_options'] = json.loads(question.ranking_structure) if question.ranking_structure else None
        elif question.type == 'psy_rank_n_rate':
            data['rating_options'] = list(question.rating_options.values('id', 'text', 'value'))
            data['ranking_options'] = json.loads(question.ranking_structure) if question.ranking_structure else None
    
    return JsonResponse(data, safe=False)


# def save_answer(request, session_id):
#     if request.method != 'POST':
#         return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
        
#     session = get_object_or_404(AssessmentSession, id=session_id)
#     data = json.loads(request.body)
    
#     StudentAnswer.objects.update_or_create(
#         session=session,
#         question_id=data['question_id'],
#         defaults={'answer': data['answer_data']}
#     )
    
#     return JsonResponse({'status': 'success'})

# def submit_assessment(request, session_id):
#     session = get_object_or_404(AssessmentSession, id=session_id)
#     session.is_completed = True
#     session.end_time = timezone.now()
#     session.save()
    
#     return redirect('assessment_results', session_id=session.id)

# def assessment_results(request, session_id):
#     session = get_object_or_404(AssessmentSession, id=session_id)
#     answers = StudentAnswer.objects.filter(session=session)
    
#     context = {
#         'session': session,
#         'answers': answers,
#     }
#     return render(request, 'assessment/assessment_results.html', context)


# def calculate_remaining_time(session):
#     elapsed_time = timezone.now() - session.start_time
#     total_time = session.assessment.duration_minutes * 60
#     remaining_seconds = total_time - elapsed_time.total_seconds()
#     return max(0, int(remaining_seconds))

# def calculate_progress(session):
#     total_questions = session.assessment.get_total_questions()
#     answered_questions = StudentAnswer.objects.filter(session=session).count()
#     return (answered_questions / total_questions) * 100 if total_questions > 0 else 0

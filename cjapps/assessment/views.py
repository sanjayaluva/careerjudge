import re
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Assessment, Section, AssessmentSession, QuestionResponse
from .forms import AssessmentForm#, VariableForm, QuestionAssignmentForm, ScoreSettingForm, DisplayParametersForm
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from .forms import QuestionSearchForm
from question_bank.models import Question
from . import models
from django.db import transaction

import random
from random import sample

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
# from django.db.models import Prefetch

def assessment_list(request):
    assessment_list = Assessment.objects.filter(created_by=request.user).all()
    paginator = Paginator(assessment_list, 10)  # Show 10 assessments per page
    page = request.GET.get('page')
    
    try:
        assessments = paginator.page(page)
    except PageNotAnInteger:
        assessments = paginator.page(1)
    except EmptyPage:
        assessments = paginator.page(paginator.num_pages)
        
    context = {
        'assessments': assessments,
        'is_paginated': True if paginator.num_pages > 1 else False,
        'page_obj': assessments
    }
    
    return render(request, 'assessment/assessment_list.html', context)

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

@csrf_exempt
def assessment_delete(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    if request.method == 'GET':
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
        elif action == 'delivery_count':
            return set_delivery_count(assessment, data)
        elif action == 'timer':
            return set_timer(assessment, data)
        
    structure = build_structure(assessment)
    return JsonResponse({'structure': structure}, safe=False)

def build_structure(assessment):
    def recursive_build(node):
        if not node:
            return None
        
        level = node.get_level()
        has_parent_timer = node.has_parent_timer()
        timer_disabled = has_parent_timer
    
        children = []
        for child in node.children.all():
            children.append(recursive_build(child))
        
        tooltip = f"Delivery Count: {node.get_total_delivery_count()}, Timer: {node.get_total_timer()} min"
        if timer_disabled:
            tooltip = f"Delivery Count: {node.get_total_delivery_count()}, Timer: disabled."

        return {
            'id': str(node.id),
            'text': node.title if node.is_section else node.question.title,
            'type': 'section' if node.is_section else 'question',
            'children': children,
            'data': {
                'questionId': node.question.id,
            } if not node.is_section else {
                'delivery_count': node.delivery_count or 0,
                'timer_minutes': node.timer_minutes or 0,
                'level': level,
                'timer_disabled': timer_disabled,
            },
            'li_attr': { 
                'class': 'question-node' 
            } if not node.is_section else { 
                'class': 'section-node', 
                'data-toggle': 'tooltip', 
                'title': tooltip,
            }
        }
    
    return [recursive_build(section) for section in assessment.sections.filter(parent=None)]

def set_timer(assessment, data):
    section = get_object_or_404(Section, id=data['node_id'])
    section.timer_minutes = int(data['minutes'])
    section.save()
    return JsonResponse({'status': 'success'})

def set_delivery_count(assessment, data):
    section = get_object_or_404(Section, id=data['node_id'])
    section.delivery_count = int(data['count'])
    section.save()
    return JsonResponse({'status': 'success'})


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

    assessment_type = request.GET.get('assessment_type')

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

        # Filter by assessment type
        if assessment_type == 'psychometric':
            questions = questions.filter(type__startswith='psy_')
        elif assessment_type == 'normal':
            questions = questions.exclude(type__startswith='psy_')


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
    if request.method == 'POST':
        section = models.Section.objects.get(id=pk)
        data = json.loads(request.body)
        # question = Question.objects.get(id=section.question_id)
        
        section.right_score = data['right_score']
        section.wrong_score = data['wrong_score']
        section.save()

        return JsonResponse({'status': 'success'})


def get_assessment_summary(session):
    """Get assessment summary statistics"""
    sections_data = get_sections_with_progress(session)
    
    total_questions = sum(section['total_questions'] for section in sections_data)
    total_attempted = sum(section['answered_count'] for section in sections_data)
    total_bookmarked = QuestionResponse.objects.filter(
        session=session,
        is_bookmarked=True
    ).count()
    
    return {
        'total_questions': total_questions,
        'attempted': total_attempted,
        'not_attempted': total_questions - total_attempted,
        'bookmarked': total_bookmarked,
        'completion_percentage': round((total_attempted / total_questions * 100), 1) if total_questions > 0 else 0
    }

def get_sections_with_progress(session):
    """Get sections with questions and their progress for assessment session"""
    sections_data = []
    responses = QuestionResponse.objects.filter(session=session)
    answered_questions = {r.question_id: r for r in responses}
    
    # Track global question number
    global_question_number = 1

    # Get main sections
    main_sections = Section.objects.filter(
        assessment=session.assessment,
        is_section=True,
        parent=None
    )
    
    for main_section in main_sections:
        questions_data = []
        
        def collect_section_questions(section):
            nonlocal global_question_number
            child_sections = Section.objects.filter(parent=section)
            
            for child in child_sections:
                if child.question_id:
                    response = answered_questions.get(child.question_id)
                    questions_data.append({
                        'id': child.question_id,
                        'number': global_question_number, #len(questions_data) + 1,
                        'is_answered': response.status == 'answered' if response else False,
                        'is_bookmarked': response.is_bookmarked if response else False,
                        'section_id': main_section.id
                    })
                    global_question_number += 1
                else:
                    collect_section_questions(child)
        
        collect_section_questions(main_section)
        
        # Calculate section progress
        total_questions = len(questions_data)
        answered_count = len([q for q in questions_data if q['is_answered']])
        progress = (answered_count / total_questions * 100) if total_questions > 0 else 0
        
        sections_data.append({
            'id': main_section.id,
            'title': main_section.title,
            'questions': questions_data,
            'progress': round(progress, 1),
            'total_questions': total_questions,
            'answered_count': answered_count
        })
    
    return sections_data

def get_assessment_sections(assessment):
    """Get flat structure of main sections and their questions"""
    sections_data = []
    
    # Get main sections (is_section=True)
    main_sections = Section.objects.filter(
        assessment=assessment,
        is_section=True,
        parent=None  # Root level sections
    )
    
    for main_section in main_sections:
        questions_data = []
        
        def get_questions_recursive(section):
            # Get direct child sections
            child_sections = Section.objects.filter(parent=section)
            
            for child in child_sections:
                if child.question_id:
                    questions_data.append({
                        'id': child.question_id,
                        'number': len(questions_data) + 1,
                        'is_answered': False,
                        'is_bookmarked': False
                    })
                else:
                    get_questions_recursive(child)
        
        # Start recursive collection from main section
        get_questions_recursive(main_section)
        
        sections_data.append({
            'id': main_section.id,
            'title': main_section.title,
            'questions': questions_data
        })
    
    return sections_data



@login_required
def resume_session(request, session_id):
    session = get_object_or_404(AssessmentSession, id=session_id, user=request.user)
    if session.status == 'suspended':
        session.resume()
        return JsonResponse({'status': 'success', 'redirect_url': f'/assessment/take/{session.id}/'})
    return JsonResponse({'status': 'error', 'message': 'Session cannot be resumed'})

@login_required
def assessment_take(request, assessment_id):
    session = get_or_create_session(request.user, assessment_id)
    
    if session.status == 'completed':
        return redirect('assessment_complete', session_id=session.id)

    context = prepare_question_context(session.current_question, session)
    context.update({
        # 'sections': get_sections_with_progress(session),
        'summary': get_assessment_summary(session),
    })
    
    return render(request, 'assessment/assessment_take.html', context)

def prepare_question_context(question, session):
    """Helper function to prepare question context for both direct and AJAX loads"""

    # Get existing response if any
    response = QuestionResponse.objects.filter(
        session=session,
        question=question
    ).first()

    sections_data = get_sections_with_progress(session)
    # Find current question number from sections data
    question_number = None
    for section in sections_data:
        for q in section['questions']:
            if q['id'] == question.id:
                question_number = q['number']
                break
        if question_number:
            break

    context = {
        'id': question.id,
        'title': question.title,
        'text': question.text.html if question.text else '',
        'objectives': question.objectives.html if question.objectives else '',
        'type': question.type,
        'question': question,
        'session': session,
        'assessment': session.assessment,
        'sections': sections_data,
        'question_template': get_question_template(question),
        'question_number': question_number,
        'total_questions': sum(len(section['questions']) for section in sections_data),
        'response': response
    }

    if question.type == 'mcq_flash':
        all_items = list(question.flash_options.all())
        presentation_items = sample(all_items, question.flash_items_count)
        remaining_items = [item for item in all_items if item not in presentation_items]
        answer_options = sample(remaining_items, min(4, len(remaining_items)))
        correct_answer = sample(presentation_items, 1)[0]
        answer_options.append(correct_answer)
        random.shuffle(answer_options)

        context.update({
            'presentation_items': presentation_items,
            'answer_options': answer_options,
            'correct_answer': correct_answer.id
        })
    elif question.type == 'fib_text':
        answers, processed_text = question.get_fib_info()
        previous_answers = response.answer_data.get('answers', []) if response else []
        context.update({
            'answers': answers,
            'processed_text': question.text.html,
            'text_parts': process_text_parts(processed_text, answers, previous_answers)
        })
    elif question.type == 'fib_image':
        answers, processed_text = question.get_fib_info()
        previous_answers = response.answer_data.get('answers', []) if response else []
        context.update({
            'answers': answers,
            'processed_text': processed_text,
            'text_parts': process_text_parts(processed_text, answers, previous_answers),
            'image_url': question.image.url
        })
    elif question.type == 'fib_audio':
        answers, processed_text = question.get_fib_info()
        previous_answers = response.answer_data.get('answers', []) if response else []
        context.update({
            'answers': answers,
            'processed_text': question.text.html,
            'text_parts': process_text_parts(processed_text, answers, previous_answers),
            'audio_url': question.audio.url
        })
    elif question.type == 'fib_video':
        answers, processed_text = question.get_fib_info()
        previous_answers = response.answer_data.get('answers', []) if response else []
        context.update({
            'answers': answers,
            'processed_text': question.text.html,
            'text_parts': process_text_parts(processed_text, answers, previous_answers),
            'video_url': question.video.url
        })
    elif question.type == 'fib_paragraph':
        answers, processed_text = question.get_fib_info()
        previous_answers = response.answer_data.get('answers', []) if response else []
        context.update({
            'answers': answers,
            'processed_text': question.text.html,
            'text_parts': process_text_parts(processed_text, answers, previous_answers),
            'paragraph_interval': question.paragraph_interval or 60
        })
    elif question.type == 'fib_flash':
        all_items = list(question.flash_options.all())
        presentation_items = sample(all_items, question.flash_items_count)
        
        context.update({
            'presentation_items': [
                {
                    'id': item.id,
                    'text': item.text,
                    'image': item.image.url if item.image else None
                } for item in presentation_items
            ],
            'flash_interval': question.flash_interval or 3,
            'flash_items_count': question.flash_items_count
        })

    return context

@login_required
def load_question(request, session_id, question_id):
    session = get_object_or_404(AssessmentSession, id=session_id, user=request.user)
    question = get_object_or_404(Question, id=question_id)
    
    # Update current question in session
    session.current_question = question
    session.save()
    
    # Get existing response if any
    response = QuestionResponse.objects.filter(session=session, question=question).first()
    
    context = prepare_question_context(question, session)
    context['response'] = response
    
    return render(request, context['question_template'], context)

def process_text_parts(text, answers, previous_answers=None):
    # Process text for display
    display_text = text
    for i, answer in enumerate(answers):
        pattern = re.escape(f'{{answer}}')
        display_text = re.sub(pattern, f'(______{i+1}_____)', display_text)
    
    # Create input fields with previous answers if available
    input_fields = [
        {
            'number': i + 1,
            'blank_id': f'blank_{i}',
            'previous_answer': previous_answers[i] if previous_answers and i < len(previous_answers) else ''
        }
        for i in range(len(answers))
    ]
    
    return {
        'display_text': display_text,
        'input_fields': input_fields
    }


def get_question_template(question):
    return f'assessment/questions/{question.type}.html'

def get_or_create_session(user, assessment_id):
        try:
            session = AssessmentSession.objects.get(
                user=user,
                assessment_id=assessment_id,
                status__in=['in_progress', 'suspended', 'completed']
            )
            if session.status == 'suspended':
                session.resume()
        except AssessmentSession.DoesNotExist:
            session = AssessmentSession.objects.create(
                user=user,
                assessment_id=assessment_id,
                status='in_progress'
            )
            # Set first question as current question
            first_question = get_first_question(assessment_id)
            if first_question:
                session.current_question_id = first_question.id
                session.save()
        return session

def get_first_question(assessment_id):
    assessment_session = AssessmentSession.objects.get(assessment_id=assessment_id)
    sections_data = get_sections_with_progress(assessment_session)
    
    # Get first question from the first section that has questions
    for section in sections_data:
        if section['questions']:
            first_question_id = section['questions'][0]['id']
            return Question.objects.get(id=first_question_id)
            
    return None

@login_required
@require_http_methods(['POST'])
def save_question_response(request, session_id):
    session = get_object_or_404(AssessmentSession, id=session_id, user=request.user)
    data = json.loads(request.body)
    
    with transaction.atomic():
        response, created = QuestionResponse.objects.update_or_create(
            session=session,
            question_id=data['question_id'],
            defaults={
                'status': data.get('status', 'skipped'),
                'answer_data': data.get('answer_data', {}),
                'is_bookmarked': data.get('is_bookmarked', False),
            }
        )

        # Validate answer and calculate score
        response.validate_answer()
        response.calculate_score()
        
    return JsonResponse({
        'status': 'success',
        'is_correct': response.is_correct,
        'score': response.score
    })

# def check_answer_correctness(question, answer_data):
#     if not answer_data:
#         return False
    
#     if question.type.startswith('mcq'):
#         if question.type in ['mcq_text', 'mcq_image', 'mcq_audio', 'mcq_video', 'mcq_paragraph']:
#             selected_option = answer_data.get('selected_option')
#             correct_option = question.options.filter(is_correct=True).first()
#             return selected_option == str(correct_option.id) if correct_option else False
#         else: # mcq_flash
#             pass
#             # return check_mcq_correctness(question, answer_data)
#         # return check_mcq_correctness(question, answer_data)
#     elif question.type.startswith('fib'):
#         if question.type in ['fib_text', 'fib_image', 'fib_audio', 'fib_video', 'fib_paragraph']:
#             user_answers = answer_data.get('answers', [])
#             correct_answers, _ = question.get_fib_info()
            
#             if len(user_answers) != len(correct_answers):
#                 return False
                
#             return all(
#                 user_answer.lower().strip() == correct_answer.lower().strip()
#                 for user_answer, correct_answer in zip(user_answers, correct_answers)
#             )
#         else: # fib_flash
#             pass
#         # return check_fib_correctness(question, answer_data)
#     elif question.type.startswith('psy'):
#         if question.type == 'psy_rating':
#             selected_value = answer_data.get('selected_value')
#             correct_value = question.rating_options.filter(is_correct=True).first()
#             return selected_value == correct_value.value if correct_value else False
#         elif question.type == 'psy_ranking':
#             selected_order = answer_data.get('selected_order')
#             correct_order = json.loads(question.ranking_structure) if question.ranking_structure else []
#             return selected_order == correct_order
#         elif question.type == 'psy_rank_n_rate':
#             selected_value = answer_data.get('selected_value')
#             correct_value = question.rating_options.filter(is_correct=True).first()
#             selected_order = answer_data.get('selected_order')
#             correct_order = json.loads(question.ranking_structure) if question.ranking_structure else []
#             return selected_value == correct_value.value if correct_value else False and selected_order == correct_order
#         return False
#     elif question.type.startswith('cus'):
#         if question.type == 'cus_hotspot_single':
#             selected_hotspots = answer_data.get('selected_hotspots')
#             correct_hotspots = question.hotspot_items
#             return selected_hotspots == correct_hotspots
#         elif question.type == 'cus_hotspot_multiple':
#             selected_hotspots = answer_data.get('selected_hotspots')
#             correct_hotspots = question.hotspot_items
#             return selected_hotspots == correct_hotspots
#         elif question.type == 'cus_grid':
#             selected_rows = answer_data.get('selected_rows')
#             correct_rows = json.loads(question.grid_structure) if question.grid_structure else []
#             return selected_rows == correct_rows
#         elif question.type == 'cus_match':
#             selected_pairs = answer_data.get('selected_pairs')
#             correct_pairs = json.loads(question.match_structure) if question.match_structure else []
#             return selected_pairs == correct_pairs
        
#         return False
#         # return check_cus_correctness(question, answer_data)
#     return False

# @login_required
# @require_http_methods(['POST'])
# def validate_all_responses(request, session_id):
#     session = get_object_or_404(AssessmentSession, id=session_id, user=request.user)
#     responses = QuestionResponse.objects.filter(session=session)
    
#     with transaction.atomic():
#         for response in responses:
#             question = response.question
#             is_correct = response. # check_answer_correctness(question, response.answer_data)
#             response.is_correct = is_correct
#             response.save()
    
#     return JsonResponse({
#         'status': 'success',
#         'message': 'All responses validated',
#         'total_responses': responses.count(),
#         'correct_responses': responses.filter(is_correct=True).count()
#     })

@login_required
@require_http_methods(['POST'])
def assessment_control(request, session_id):
    data = json.loads(request.body)
    action = data.get('action')
    session = get_object_or_404(AssessmentSession, id=session_id, user=request.user)

    if action == 'suspend':
        session.status = 'suspended'
        session.save_state()
        return JsonResponse({'status': 'success', 'message': 'Assessment suspended'})
    
    elif action == 'resume':
        return resume_session(request, session_id)
    
    elif action == 'submit':
        session.status = 'completed'
        session.is_completed = True
        session.end_time = timezone.now()
        session.save()
        
        # Calculate final scores
        session.calculate_scores()
        
        return JsonResponse({'status': 'success', 'redirect_url': f'/assessment/complete/{session_id}/'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid action'})


@login_required
def assessment_complete(request, session_id):
    session = get_object_or_404(AssessmentSession, id=session_id, user=request.user)
    
    # Get assessment summary
    summary = get_assessment_summary(session)
    
    # Get all responses with questions
    responses = QuestionResponse.objects.filter(session=session).select_related('question')
    
    # Organize responses by section
    sections_with_responses = {}
    for response in responses:
        section = response.question.section_set.first()
        if section not in sections_with_responses:
            sections_with_responses[section] = []
        sections_with_responses[section].append({
            'question': response.question,
            'answer_data': response.answer_data,
            'is_correct': response.is_correct,
            'score': response.score
        })
    
    context = {
        'session': session,
        'sections': sections_with_responses,
        'summary': summary,
        'total_questions': responses.count(),
        'correct_answers': responses.filter(is_correct=True).count(),
        'assessment': session.assessment,
        'section_scores': session.scores
    }
    
    return render(request, 'assessment/complete.html', context)


# def question_detail_api(request, pk):
#     question = get_object_or_404(Question, pk=pk)
    
#     # Base question data
#     data = {
#         'question_id': question.id,
#         'title': question.title,
#         'type': question.type,
#         'category_id': question.category.id,
#         'category_name': question.category.name if question.category else None,
#         'difficulty_level': question.difficulty_level,
#         'cognitive_level': question.cognitive_level,
#         'text': question.text.html if question.text else '',
#         'objectives': question.objectives.html if question.objectives else '',
#         'instructions': question.instructions.html if question.instructions else '',
#         'exposure_limit': question.exposure_limit,
#         'status': question.status,
#     }
    
#     # Add type-specific data
#     if question.type.startswith('mcq'):
#         data['options'] = list(question.options.annotate(
#             image_url=Case(
#                 When(image='', then=Value('')),
#                 default=Concat(Value('/media/'), F('image'), output_field=CharField()),
#             )
#         ).values('id', 'text', 'image_url', 'is_correct'))
#     if question.type.startswith('fib'):
#         data['blanks'] = question.get_fib_options()
#     if question.type.endswith('image') or question.type.endswith('mixed'):
#         data['image_url'] = question.image.url
#     elif question.type.endswith('audio'):
#         data['audio_url'] = question.audio.url
#     elif question.type.endswith('video'):
#         data['video_url'] = question.video.url
#     if question.type.endswith('paragraph'):
#         data['paragraph'] = question.paragraph.html if question.paragraph else ''
#         data['display_time'] = question.paragraph_interval or 60
#     elif question.type.endswith('flash'):
#         data['flash_items'] = list(question.flash_options.annotate(
#             image_url=Case(
#                 When(image='', then=Value('')),
#                 default=Concat(Value('/media/'), F('image'), output_field=CharField()),
#             )
#         ).values('id', 'text', 'image_url'))
#         data['flash_time'] = question.flash_interval or 60 #flash_display_time
#         data['flash_items_count'] = question.flash_items_count or 0
    
#     elif question.type.startswith('cus_hotspot'):
#         data['image_url'] = question.image.url
#         data['hotspots'] = question.hotspot_items
#         data['multiple_selection'] = question.type == 'cus_hotspot_multiple'
    
#     elif question.type == 'cus_grid':
#         data['grid_items'] = list(question.grid_options.annotate(
#             image_url=Case(
#                 When(image='', then=Value('')),
#                 default=Concat(Value('/media/'), F('image'), output_field=CharField()),
#             )
#         ).values('id', 'text', 'image_url', 'row', 'col', 'is_correct'))
#         data['grid_size'] = {'rows': question.grid_rows, 'cols': question.grid_cols}
#         data['grid_type'] = question.grid_type
    
#     elif question.type == 'cus_match':
#         data['pairs'] = list(question.match_options.values('id', 'left_item', 'right_item'))
    
#     elif question.type.startswith('psy'):
#         # data['items'] = list(question.items.values())
#         if question.type == 'psy_rating':
#             data['rating_options'] = list(question.rating_options.values('id', 'text', 'value'))
#         elif question.type == 'psy_ranking':
#             data['ranking_options'] = json.loads(question.ranking_structure) if question.ranking_structure else None
#         elif question.type == 'psy_rank_n_rate':
#             data['rating_options'] = list(question.rating_options.values('id', 'text', 'value'))
#             data['ranking_options'] = json.loads(question.ranking_structure) if question.ranking_structure else None
    
#     return JsonResponse(data, safe=False)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.db import transaction
from django.utils import timezone
import os

from django.contrib.auth import get_user_model
User = get_user_model()

from .models import (
    ReportConfiguration, Cutoff, Band, ContrastVariable, 
    AssessmentBooking, GeneratedReport, TypeBand
)
from .forms import (
    ReportConfigurationForm, CutoffForm, BandForm, 
    ContrastVariableForm, AssessmentBookingForm,
    CandidateSelectionForm
)
from assessment.models import Assessment, Section, AssessmentSession, QuestionResponse
from cjapp.payment import RzpClient

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import numpy as np
from django.template.loader import render_to_string
import tempfile
from xhtml2pdf import pisa
import base64
from matplotlib.colors import LinearSegmentedColormap
from datetime import datetime
import json

@login_required
def report_configuration_list(request):
    """List all report configurations for the user"""
    configurations = ReportConfiguration.objects.filter(created_by=request.user).order_by('-created_at')
    
    paginator = Paginator(configurations, 10)
    page = request.GET.get('page')
    
    try:
        configurations = paginator.page(page)
    except PageNotAnInteger:
        configurations = paginator.page(1)
    except EmptyPage:
        configurations = paginator.page(paginator.num_pages)
    
    return render(request, 'reports/configuration_list.html', {
        'configurations': configurations,
        'is_paginated': True if paginator.num_pages > 1 else False
    })

@login_required
def create_report_configuration(request):
    """Create a new report configuration"""
    if request.method == 'POST':
        form = ReportConfigurationForm(request.POST, request.FILES, user=request.user)

        # Initialize candidate form as None by default
        candidate_form = None
        
        # Only process candidate form if report type is 'group'
        if request.POST.get('report_type') == 'group':
            # Get the assessment from the form data
            try:
                assessment_id = int(request.POST.get('assessment'))
                assessment = Assessment.objects.get(id=assessment_id)
                candidate_form = CandidateSelectionForm(request.POST, assessment=assessment)
            except (ValueError, Assessment.DoesNotExist):
                # Handle case where assessment doesn't exist or isn't valid
                pass

        if form.is_valid() and (candidate_form is None or candidate_form.is_valid()):
            configuration = form.save(commit=False)
            configuration.created_by = request.user
            
            # Process score_level as JSON
            score_levels = request.POST.getlist('score_level')
            configuration.score_level = score_levels
            
            configuration.save()
            form.save_m2m()  # Save many-to-many relationships
            
            # Save selected candidates for group reports
            if configuration.report_type == 'group' and candidate_form and candidate_form.is_valid():
                # Get the selected candidate IDs from the form
                selected_candidates = candidate_form.cleaned_data.get('candidates', [])
                
                # Add debugging output
                print(f"Selected candidates: {selected_candidates}")
                
                # Clear existing candidates and add new ones
                configuration.candidates.clear()
                if selected_candidates:
                    configuration.candidates.add(*selected_candidates)
            
            
            messages.success(request, "Report configuration created successfully.")
            
            # If this is a descriptive/interpretative/typological report, redirect to edit sections
            if configuration.has_cutoffs or configuration.has_bands or configuration.has_contrast_variables:
                return redirect('reports:edit_report_sections', pk=configuration.id)
            
            return redirect('reports:report_configuration_list')
    else:
        form = ReportConfigurationForm(user=request.user)
        candidate_form = None  # Initialize as None, will be populated via AJAX
    
    return render(request, 'reports/configuration_form.html', {
        'form': form,
        'candidate_form': candidate_form,
        'title': 'Create Report Configuration'
    })

@login_required
def load_candidates(request):
    """AJAX view to load candidates based on selected assessment"""
    assessment_id = request.GET.get('assessment_id')
    
    if not assessment_id:
        return JsonResponse({'error': 'No assessment selected'}, status=400)
    
    try:
        assessment = Assessment.objects.get(id=assessment_id)
        
        # Get users who have completed this assessment
        from assessment.models import AssessmentSession
        completed_sessions = AssessmentSession.objects.filter(
            assessment=assessment,
            status='completed'
        ).values_list('user_id', flat=True)
        
        candidates = User.objects.filter(
            id__in=completed_sessions
        ).order_by('last_name', 'first_name')
        
        # Format candidates for select2
        candidate_list = []
        for candidate in candidates:
            # Check if get_full_name is callable
            if callable(getattr(candidate, 'get_full_name', None)):
                full_name = candidate.get_full_name()
            else:
                # Fallback to concatenating first and last name
                full_name = f"{candidate.first_name} {candidate.last_name}".strip()
                if not full_name:
                    full_name = candidate.username  # Use username if no name available
            
            candidate_list.append({
                'id': candidate.id,
                'text': f"{full_name} ({candidate.email})"
            })
        
        return JsonResponse({'candidates': candidate_list})
    
    except Assessment.DoesNotExist:
        return JsonResponse({'error': 'Assessment not found'}, status=404)


@login_required
def edit_report_configuration(request, pk):
    """Edit an existing report configuration"""
    configuration = get_object_or_404(ReportConfiguration, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = ReportConfigurationForm(request.POST, request.FILES, instance=configuration, user=request.user)
        
        # Only show candidate selection for group reports
        if configuration.report_type == 'group':
            candidate_form = CandidateSelectionForm(request.POST, assessment=configuration.assessment)
        else:
            candidate_form = None
            
        if form.is_valid() and (candidate_form is None or candidate_form.is_valid()):
            configuration = form.save(commit=False)
            
            # Process score_level as JSON
            score_levels = request.POST.getlist('score_level')
            configuration.score_level = score_levels
            
            configuration.save()

            # Save selected candidates for group reports
            if configuration.report_type == 'group' and candidate_form:
                # Clear existing candidates
                configuration.candidates.clear()
                
                # Add selected candidates
                selected_candidates = candidate_form.cleaned_data['candidates']
                configuration.candidates.add(*selected_candidates)
            
            messages.success(request, "Report configuration updated successfully.")
            
            # If this is a descriptive/interpretative/typological report, redirect to edit sections
            if configuration.has_cutoffs or configuration.has_bands or configuration.has_contrast_variables:
                return redirect('reports:edit_report_sections', pk=configuration.id)
            
            return redirect('reports:report_configuration_list')
    else:
        form = ReportConfigurationForm(instance=configuration, user=request.user)

        # Only show candidate selection for group reports
        if configuration.report_type == 'group':
            candidate_form = CandidateSelectionForm(
                assessment=configuration.assessment,
                initial={'candidates': configuration.candidates.all()}
            )
        else:
            candidate_form = None

    return render(request, 'reports/configuration_form.html', {
        'form': form,
        'candidate_form': candidate_form,
        'configuration': configuration,
        'title': 'Edit Report Configuration'
    })

@login_required
def delete_report_configuration(request, pk):
    """Delete a report configuration"""
    configuration = get_object_or_404(ReportConfiguration, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        configuration.delete()
        messages.success(request, "Report configuration deleted successfully.")
    
    return redirect('reports:report_configuration_list')

@login_required
def edit_report_sections(request, pk):
    """Edit sections for descriptive, interpretative, or typological reports"""
    configuration = get_object_or_404(ReportConfiguration, pk=pk, created_by=request.user)
    assessment = configuration.assessment
    
    # Get all sections that are actual sections (is_section=True)
    sections = Section.objects.filter(assessment=assessment, is_section=True)
    
    return render(request, 'reports/edit_report_sections.html', {
        'configuration': configuration,
        'assessment': assessment,
        'sections': sections,
    })

@login_required
def get_assessment_sections(request, assessment_id):
    """AJAX view to get assessment sections for jstree"""
    def build_jstree_node(section, section_type=None):
        return {
            'id': f"{section_type}_{section.id}" if section_type else str(section.id),
            'text': section.title,
            'children': section.children.filter(is_section=True).exists(),
            'type': 'section',
            'a_attr': {
                'data-id': section.id,
                'data-type': section_type or 'section'
            }
        }
    
    assessment = get_object_or_404(Assessment, pk=assessment_id)
    node_id = request.GET.get('id', '#')
    
    if node_id == '#':
        # Root level sections
        sections = Section.objects.filter(
            assessment=assessment,
            parent=None,
            is_section=True
        ).order_by('order')
        
        return JsonResponse([build_jstree_node(section) for section in sections], safe=False)
    else:
        # Get children of the selected node
        section_id = node_id
        sections = Section.objects.filter(
            parent_id=section_id,
            is_section=True
        ).order_by('order')
        
        return JsonResponse([build_jstree_node(section) for section in sections], safe=False)

@login_required
@csrf_exempt
def manage_cutoff(request, config_id):
    """AJAX view to add/edit/delete cutoffs"""
    configuration = get_object_or_404(ReportConfiguration, pk=config_id, created_by=request.user)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'get':
            section_id = data.get('section_id')
            section = get_object_or_404(Section, pk=section_id)
            
            try:
                cutoff = Cutoff.objects.get(
                    configuration=configuration,
                    assessment_section=section
                )
                return JsonResponse({
                    'status': 'success',
                    'cutoff': {
                        'id': cutoff.id,
                        'cutoff_score': cutoff.cutoff_score,
                        'cutoff_label': cutoff.cutoff_label,
                        'above_cutoff_description': cutoff.above_cutoff_description.html if cutoff.above_cutoff_description else '',
                        'below_cutoff_description': cutoff.below_cutoff_description.html if cutoff.below_cutoff_description else '',
                    }
                })
            except Cutoff.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No cutoff exists for this section.'
                })
                
        elif action == 'create' or action == 'update':
            section_id = data.get('section_id')
            section = get_object_or_404(Section, pk=section_id)
            
            cutoff_id = data.get('cutoff_id')
            
            # Process the Quill field data
            above_cutoff_description = data.get('above_cutoff_description', '')
            below_cutoff_description = data.get('below_cutoff_description', '')
            
            # Format the descriptions as Quill data if they're not already
            if above_cutoff_description and not is_valid_quill_json(above_cutoff_description):
                above_cutoff_description = format_as_quill_json(above_cutoff_description)
                
            if below_cutoff_description and not is_valid_quill_json(below_cutoff_description):
                below_cutoff_description = format_as_quill_json(below_cutoff_description)
            
            cutoff_data = {
                'cutoff_score': data.get('cutoff_score'),
                'cutoff_label': data.get('cutoff_label'),
                'above_cutoff_description': above_cutoff_description,
                'below_cutoff_description': below_cutoff_description,
                'configuration': configuration,
                'assessment_section': section
            }
            
            if action == 'update' and cutoff_id:
                cutoff = get_object_or_404(Cutoff, pk=cutoff_id)
                form = CutoffForm(cutoff_data, instance=cutoff)
            else:
                form = CutoffForm(cutoff_data)
                
            if form.is_valid():
                cutoff = form.save(commit=False)
                cutoff.configuration = configuration  # Explicitly set configuration
                cutoff.assessment_section = section  # Explicitly set section
                cutoff.save()  # Now save to DB
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Cutoff saved successfully',
                    'cutoff': {
                        'id': cutoff.id,
                        'cutoff_score': cutoff.cutoff_score,
                        'cutoff_label': cutoff.cutoff_label
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid form data',
                    'errors': form.errors
                })
                
        elif action == 'delete':
            cutoff_id = data.get('cutoff_id')
            cutoff = get_object_or_404(Cutoff, pk=cutoff_id, configuration=configuration)
            cutoff.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Cutoff deleted successfully'
            })
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# Helper functions for Quill data handling
def is_valid_quill_json(text):
    """Check if the text is already in valid Quill JSON format"""
    try:
        data = json.loads(text)
        return isinstance(data, dict) and 'html' in data and 'delta' in data
    except (json.JSONDecodeError, TypeError):
        return False

def format_as_quill_json(text):
    """Format plain text as Quill JSON"""
    # For plain text, create a simple delta with just an insert operation
    delta = {'ops': [{'insert': text}]}
    
    # For HTML, wrap in a paragraph if it doesn't look like HTML already
    if not text.strip().startswith('<'):
        html = f"<p>{text}</p>"
    else:
        html = text
        
    return json.dumps({
        'html': html,
        'delta': delta
    })

@login_required
@csrf_exempt
def manage_band(request, config_id):
    """AJAX view to add/edit/delete bands"""
    configuration = get_object_or_404(ReportConfiguration, pk=config_id, created_by=request.user)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'get':
            section_id = data.get('section_id')
            section = get_object_or_404(Section, pk=section_id)
            
            bands = Band.objects.filter(
                configuration=configuration,
                assessment_section=section
            )
            
            return JsonResponse({
                'status': 'success',
                'bands': [{
                    'id': band.id,
                    'name': band.name,
                    'min_range': band.min_range,
                    'max_range': band.max_range,
                    'color': band.color,
                    'label': band.label,
                    'description': band.description.html if band.description else '',
                } for band in bands]
            })
                
        elif action == 'create':
            section_id = data.get('section_id')
            section = get_object_or_404(Section, pk=section_id)
            
            band_data = {
                'configuration': configuration,
                'assessment_section': section,
                'name': data.get('name'),
                'min_range': data.get('min_range'),
                'max_range': data.get('max_range'),
                'color': data.get('color'),
                'label': data.get('label'),
                'description': data.get('description', '')
            }
            
            form = BandForm(band_data)
            if form.is_valid():
                band = form.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Band created successfully',
                    'band': {
                        'id': band.id,
                        'name': band.name,
                        'min_range': band.min_range,
                        'max_range': band.max_range,
                        'color': band.color,
                        'label': band.label
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid form data',
                    'errors': form.errors
                })
                
        elif action == 'update':
            band_id = data.get('band_id')
            band = get_object_or_404(Band, pk=band_id, configuration=configuration)
            
            section_id = data.get('section_id')
            section = get_object_or_404(Section, pk=section_id)

            band_data = {
                'configuration': configuration,
                'assessment_section': section,
                'name': data.get('name'),
                'min_range': data.get('min_range'),
                'max_range': data.get('max_range'),
                'color': data.get('color'),
                'label': data.get('label'),
                'description': data.get('description', '')
            }
            
            form = BandForm(band_data, instance=band)
            if form.is_valid():
                band = form.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Band updated successfully',
                    'band': {
                        'id': band.id,
                        'name': band.name,
                        'min_range': band.min_range,
                        'max_range': band.max_range,
                        'color': band.color,
                        'label': band.label
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid form data',
                    'errors': form.errors
                })
                
        elif action == 'delete':
            band_id = data.get('band_id')
            band = get_object_or_404(Band, pk=band_id, configuration=configuration)
            band.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Band deleted successfully'
            })
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
@csrf_exempt
def manage_contrast_variable(request, config_id):
    """AJAX view to add/edit/delete contrast variables"""
    configuration = get_object_or_404(ReportConfiguration, pk=config_id, created_by=request.user)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'get':
            subcategory = data.get('subcategory')
            
            try:
                cv = ContrastVariable.objects.get(
                    configuration=configuration,
                    subcategory=subcategory
                )
                return JsonResponse({
                    'status': 'success',
                    'contrast_variable': {
                        'id': cv.id,
                        'name': cv.name,
                        'code': cv.code,
                        'color': cv.color,
                        'description': cv.description.html if cv.description else '',
                    }
                })
            except ContrastVariable.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No contrast variable exists for this subcategory.'
                })
                
        elif action == 'create' or action == 'update':
            subcategory = data.get('subcategory')
            
            cv_id = data.get('cv_id')
            cv_data = {
                'subcategory': subcategory,
                'name': data.get('name'),
                'code': data.get('code'),
                'color': data.get('color'),
            }
            
            # Handle description as Quill data
            description = data.get('description', '')
            if description:
                try:
                    # If it's already in JSON format, use it directly
                    json.loads(description)
                    cv_data['description'] = description
                except json.JSONDecodeError:
                    # If it's not valid JSON, format it as Quill data
                    cv_data['description'] = json.dumps({
                        'html': description,
                        'delta': {'ops': [{'insert': description}]}
                    })
            else:
                cv_data['description'] = None
            
            if action == 'update' and cv_id:
                cv = get_object_or_404(ContrastVariable, pk=cv_id)
                cv_data['configuration'] = configuration
                form = ContrastVariableForm(cv_data, instance=cv)
            else:
                cv_data['configuration'] = configuration
                form = ContrastVariableForm(cv_data)
                
            if form.is_valid():
                cv = form.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Contrast variable saved successfully',
                    'contrast_variable': {
                        'id': cv.id,
                        'name': cv.name,
                        'code': cv.code,
                        'color': cv.color
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid form data',
                    'errors': form.errors
                })
                
        elif action == 'delete':
            cv_id = data.get('cv_id')
            cv = get_object_or_404(ContrastVariable, pk=cv_id, configuration=configuration)
            cv.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Contrast variable deleted successfully'
            })
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
@csrf_exempt
def manage_type_band(request, config_id):
    """AJAX view to add/edit/delete type bands"""
    configuration = get_object_or_404(ReportConfiguration, pk=config_id, created_by=request.user)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'get':
            cv_id = data.get('cv_id')
            cv = get_object_or_404(ContrastVariable, pk=cv_id)
            
            bands = TypeBand.objects.filter(
                configuration=configuration,
                contrast_variable=cv
            )
            
            return JsonResponse({
                'status': 'success',
                'bands': [{
                    'id': band.id,
                    'name': band.name,
                    'min_range': band.min_range,
                    'max_range': band.max_range,
                    'color': band.color,
                    'label': band.label,
                    'description': band.description.html if band.description else '',
                } for band in bands]
            })
                
        elif action == 'create':
            cv_id = data.get('cv_id')
            cv = get_object_or_404(ContrastVariable, pk=cv_id)
            
            # Handle description as Quill data
            description = data.get('description', '')
            if description:
                try:
                    # If it's already in JSON format, use it directly
                    json.loads(description)
                    description_data = description
                except json.JSONDecodeError:
                    # If it's not valid JSON, format it as Quill data
                    description_data = json.dumps({
                        'html': description,
                        'delta': {'ops': [{'insert': description}]}
                    })
            else:
                description_data = None
            
            band_data = {
                'configuration': configuration,
                'contrast_variable': cv,
                'name': data.get('name'),
                'min_range': data.get('min_range'),
                'max_range': data.get('max_range'),
                'color': data.get('color'),
                'label': data.get('label'),
                'description': description_data
            }
            
            from .forms import TypeBandForm
            form = TypeBandForm(band_data)
            if form.is_valid():
                band = form.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Band created successfully',
                    'band': {
                        'id': band.id,
                        'name': band.name,
                        'min_range': band.min_range,
                        'max_range': band.max_range,
                        'color': band.color,
                        'label': band.label
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid form data',
                    'errors': form.errors
                })
                
        elif action == 'update':
            band_id = data.get('band_id')
            band = get_object_or_404(TypeBand, pk=band_id, configuration=configuration)
            
            cv_id = data.get('cv_id')
            cv = get_object_or_404(ContrastVariable, pk=cv_id)

            # Handle description as Quill data
            description = data.get('description', '')
            if description:
                try:
                    # If it's already in JSON format, use it directly
                    json.loads(description)
                    description_data = description
                except json.JSONDecodeError:
                    # If it's not valid JSON, format it as Quill data
                    description_data = json.dumps({
                        'html': description,
                        'delta': {'ops': [{'insert': description}]}
                    })
            else:
                description_data = None

            band_data = {
                'configuration': configuration,
                'contrast_variable': cv,
                'name': data.get('name'),
                'min_range': data.get('min_range'),
                'max_range': data.get('max_range'),
                'color': data.get('color'),
                'label': data.get('label'),
                'description': description_data
            }
            
            from .forms import TypeBandForm
            form = TypeBandForm(band_data, instance=band)
            if form.is_valid():
                band = form.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Band updated successfully',
                    'band': {
                        'id': band.id,
                        'name': band.name,
                        'min_range': band.min_range,
                        'max_range': band.max_range,
                        'color': band.color,
                        'label': band.label
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid form data',
                    'errors': form.errors
                })
                
        elif action == 'delete':
            band_id = data.get('band_id')
            band = get_object_or_404(TypeBand, pk=band_id, configuration=configuration)
            band.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Band deleted successfully'
            })
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def get_subcategories(request, assessment_id):
    """AJAX view to get subcategories for jstree"""
    def build_jstree_node(node, node_type, parent_id=None):
        return {
            'id': f"{node_type}_{node['id']}",
            'text': node['text'],
            'children': node.get('children', []),
            'type': node_type,
            'a_attr': {
                'data-id': node['id'],
                'data-type': node_type,
                'data-parent': parent_id
            }
        }
    
    assessment = get_object_or_404(Assessment, pk=assessment_id)
    node_id = request.GET.get('id', '#')
    
    # Get all forced choice questions for this assessment
    from assessment.models import Section
    sections = Section.objects.filter(
        assessment=assessment,
        question__type__startswith='psy_forced'
    ).select_related('question')
    
    # Extract unique question IDs
    question_ids = set(section.question_id for section in sections if section.question)
    
    # Get all questions
    from question_bank.models import Question
    questions = Question.objects.filter(id__in=question_ids)
    
    # Build category tree
    if node_id == '#':
        # Root level - show categories
        categories = set()
        for question in questions:
            if question.ranking_structure:
                structure = json.loads(question.ranking_structure)
                if 'leftTree' in structure:
                    for category in structure['leftTree']:
                        if category['type'] == 'category':
                            # Include subcategories in the category node
                            subcategories = []
                            for child in category.get('children', []):
                                if child['type'] == 'subcategory':
                                    subcategories.append({
                                        'id': child['id'],
                                        'text': child['text'],
                                        'type': 'subcategory'
                                    })
                            
                            categories.add((
                                category['id'], 
                                category['text'],
                                json.dumps(subcategories)  # Store subcategories as JSON string
                            ))
        
        # Convert to list of dictionaries
        category_nodes = []
        for cat_id, cat_text, subcats_json in categories:
            node = {
                'id': cat_id, 
                'text': cat_text,
                'children': json.loads(subcats_json) if subcats_json else []
            }
            category_nodes.append(node)
        
        # Build jstree nodes
        result = []
        for node in category_nodes:
            jstree_node = build_jstree_node(node, 'category')
            
            # Add subcategory children
            if node['children']:
                jstree_node['children'] = [
                    build_jstree_node(subcat, 'subcategory', node['id']) 
                    for subcat in node['children']
                ]
            
            result.append(jstree_node)
        
        return JsonResponse(result, safe=False)
    else:
        # This part is kept for compatibility but won't be used with the new approach
        # since we're loading all subcategories with their parent categories
        node_type, node_id = node_id.split('_', 1)
        
        if node_type == 'category':
            # Get subcategories for this category
            subcategories = set()
            
            for question in questions:
                if question.ranking_structure:
                    structure = json.loads(question.ranking_structure)
                    if 'leftTree' in structure:
                        for category in structure['leftTree']:
                            if category['type'] == 'category' and str(category['id']) == node_id:
                                for child in category.get('children', []):
                                    if child['type'] == 'subcategory':
                                        subcategories.add((child['id'], child['text']))
            
            # Convert to list of dictionaries
            subcategory_nodes = [{'id': subcat_id, 'text': subcat_text} for subcat_id, subcat_text in subcategories]
            
            return JsonResponse([build_jstree_node(node, 'subcategory', node_id) for node in subcategory_nodes], safe=False)
        
        return JsonResponse([], safe=False)



@login_required
def select_sample_session(request, config_id):
    """Select a sample session to generate a report for preview purposes"""
    config = get_object_or_404(ReportConfiguration, pk=config_id, created_by=request.user)
    
    # Get available completed sessions for this assessment
    sessions = AssessmentSession.objects.filter(
        assessment=config.assessment,
        status='completed'
    ).order_by('-end_time')[:10]  # Get latest 10 sessions
    
    return render(request, 'reports/select_sample_session.html', {
        'config': config,
        'sessions': sessions
    })

@login_required
def select_sessions(request, config_id):
    """Select multiple sessions for bulk report generation"""
    config = get_object_or_404(ReportConfiguration, pk=config_id, created_by=request.user)
    
    # Get available completed sessions for this assessment
    sessions = AssessmentSession.objects.filter(
        assessment=config.assessment,
        status='completed'
    ).order_by('-end_time')
    
    return render(request, 'reports/select_sessions.html', {
        'config': config,
        'sessions': sessions
    })

@login_required
def generate_bulk_reports(request, pk):
    """Generate reports for multiple sessions at once"""
    if request.method != 'POST':
        return redirect('reports:report_configuration_list')
    
    config = get_object_or_404(ReportConfiguration, pk=pk, created_by=request.user)
    
    # config_id = request.POST.get('config_id')
    session_ids = request.POST.getlist('session_ids')
    
    generated_count = 0
    for session_id in session_ids:
        # Check if report already exists
        existing_report = GeneratedReport.objects.filter(
            configuration=config,
            assessment_session_id=session_id
        ).exists()
        
        if not existing_report:
            # Redirect to the existing generate_report view, let it handle the logic
            # This will be called via server code, not browser redirect
            try:
                # We can call the view function directly with a mock request
                from django.test import RequestFactory
                factory = RequestFactory()
                mock_request = factory.get('/')
                mock_request.user = request.user
                generate_report(mock_request, session_id=int(session_id), config_id=int(config_id))
                generated_count += 1
            except Exception as e:
                messages.error(request, f"Error generating report for session {session_id}: {str(e)}")
    
    if generated_count > 0:
        messages.success(request, f"Successfully generated {generated_count} reports.")
    else:
        messages.info(request, "No new reports were generated. They may already exist.")
    
    return redirect('reports:list_generated_reports', pk=pk)

@login_required
def list_generated_reports(request, config_id):
    """List all generated reports for a specific configuration"""
    config = get_object_or_404(ReportConfiguration, pk=config_id, created_by=request.user)
    
    reports = GeneratedReport.objects.filter(
        configuration=config
    ).select_related('assessment_session__user').order_by('-generated_at')
    
    return render(request, 'reports/list_generated_reports.html', {
        'config': config,
        'reports': reports
    })


@login_required
def generate_report(request, session_id, config_id=None):
    """Generate a report for an assessment session"""
    session = get_object_or_404(AssessmentSession, pk=session_id)
    
    # Check if user can access this session
    if session.user != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to access this session.")
        return redirect('dashboard')
    
    # Get configuration
    if config_id:
        configuration = get_object_or_404(ReportConfiguration, pk=config_id)
    else:
        # Use default configuration
        configuration = ReportConfiguration.objects.filter(
            assessment=session.assessment,
            is_default=True
        ).first()
        
        if not configuration:
            messages.error(request, "No report configuration found for this assessment.")
            return redirect('assessment:assessment_complete', session_id=session_id)
    
    # Check if report already exists
    existing_report = GeneratedReport.objects.filter(
        configuration=configuration,
        assessment_session=session
    ).first()
    
    if existing_report and existing_report.report_file:
        # Return existing report
        return redirect(existing_report.report_file.url)
    
    # Generate new report
    context = prepare_report_context(configuration, session, request)
    
    # Add domain to context
    context['domain'] = request.build_absolute_uri('/').rstrip('/')

    html = render_to_string(f'reports/{configuration.report_type}_report.html', context)
    
    # Save HTML for debugging
    debug_path = os.path.join(settings.BASE_DIR, 'debug_report.html')
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Debug HTML saved to: {debug_path}")  # Log the location

    # Convert HTML to PDF
    result_file = io.BytesIO()
    pdf = pisa.pisaDocument(
        io.BytesIO(html.encode("UTF-8")),
        result_file
    )
    
    if not pdf.err:
        # Save the PDF
        filename = f"{configuration.title}_{session.user.email}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        
        # Create or update GeneratedReport
        if existing_report:
            report = existing_report
        else:
            report = GeneratedReport(
                configuration=configuration,
                assessment_session=session,
                user=request.user
            )
        
        from django.core.files.base import ContentFile
        report.report_file.save(filename, ContentFile(result_file.getvalue()))
        report.save()
        
        return redirect(report.report_file.url)
    else:
        messages.error(request, "Error generating PDF report.")
        return redirect('assessment:assessment_complete', session_id=session_id)

# from django.contrib.sites.models import Site
# from django.conf import settings
# from django.utils import timezone

def prepare_report_context(configuration, session, request=None):
    """Prepare context for report generation based on configuration type"""
    
    # Define domain from request or use default
    if request:
        # Get scheme (http or https) dynamically
        scheme = request.scheme  # This will be 'http' or 'https'
        domain = request.get_host()
        base_url = f"{scheme}://{domain}"
    else:
        # Fallback if no request object is available
        domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
        base_url = f"http://{domain}"  # Default to http when no request available

    context = {
        'configuration': configuration,
        'session': session,
        'assessment': session.assessment,
        'user': session.user,
        'generated_date': timezone.now(),
        'logo_url': f'{base_url}{settings.MEDIA_URL}logo.png',
        'base_url': base_url,
    }

    # Format the Quill HTML content for description and objectives
    if configuration.description and configuration.description.html:
        formatted_description = format_quill_html_section(configuration.description.html, request) #, base_url
        # Store the formatted description in context
        context['formatted_description'] = formatted_description
    
    if configuration.objectives and configuration.objectives.html:
        formatted_objectives = format_quill_html_section(configuration.objectives.html, request) #, base_url
        # Store the formatted objectives in context
        context['formatted_objectives'] = formatted_objectives


    # Create an absolute URL for the logo - use settings.MEDIA_ROOT for the file path
    # import os
    logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')
    
    # Check if the logo file exists
    if os.path.exists(logo_path):
        # For PDF generation, we can use a data URI for the logo if it's small enough
        with open(logo_path, 'rb') as f:
            import base64
            logo_data = base64.b64encode(f.read()).decode('utf-8')
            context['logo_data_uri'] = f'data:image/png;base64,{logo_data}'
    
    # Process description image if it exists
    if configuration.description_img:
        try:
            img_path = configuration.description_img.path
            if os.path.exists(img_path):
                with open(img_path, 'rb') as f:
                    import base64
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(img_path)
                    if not mime_type:
                        mime_type = 'image/jpeg'  # Default to jpeg if can't determine
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                    context['description_img_data_uri'] = f'data:{mime_type};base64,{img_data}'
        except Exception as e:
            print(f"Error processing description image: {e}")

    # Get scores based on configuration.score_level
    scores = get_scores_by_level(configuration, session)
    context['scores'] = scores
    
    # Add report type specific context
    if configuration.report_type == 'descriptive':
        context.update(prepare_descriptive_report_context(configuration, session, scores))
    elif configuration.report_type == 'interpretative':
        context.update(prepare_interpretative_report_context(configuration, session, scores, request))
    elif configuration.report_type == 'typological':
        context.update(prepare_typological_report_context(configuration, session, scores))
    elif configuration.report_type == 'group':
        context.update(prepare_group_report_context(configuration, session, scores))
    elif configuration.report_type == 'question_level':
        context.update(prepare_question_level_report_context(configuration, session))
    
    return context

def get_scores_by_level(configuration, session):
    """Get scores based on configured score levels"""
    scores = {}
    
    # Get all scores from session
    session_scores = session.scores
    
    # Get all sections
    sections = Section.objects.filter(assessment=session.assessment)
    
    # Process scores based on selected levels
    for level in configuration.score_level:
        if level == 'level_0':
            # Level 0 - Summary of main sections
            main_sections = sections.filter(parent=None, is_section=True)
            scores['level_0'] = {
                'sections': main_sections,
                'scores': {section.id: session_scores.get(f'section_{section.id}', 0) for section in main_sections}
            }
        
        elif level == 'level_1':
            # Level 1 - Main sections
            main_sections = sections.filter(parent=None, is_section=True)
            scores['level_1'] = {
                'sections': main_sections,
                'scores': {section.id: session_scores.get(f'section_{section.id}', 0) for section in main_sections}
            }
        
        elif level == 'level_2':
            # Level 2 - Subsections
            main_sections = sections.filter(parent=None, is_section=True)
            all_subsections = []
            
            for main_section in main_sections:
                subsections = sections.filter(parent=main_section, is_section=True)
                all_subsections.extend(subsections)
            
            scores['level_2'] = {
                'sections': all_subsections,
                'scores': {section.id: session_scores.get(f'section_{section.id}', 0) for section in all_subsections}
            }
        
        elif level == 'question_level':
            # Question Level - All questions
            responses = QuestionResponse.objects.filter(session=session)
            scores['question_level'] = {
                'responses': responses
            }
    
    return scores

def prepare_descriptive_report_context(configuration, session, scores, request=None, base_url=None):
    """Prepare context for descriptive report"""
    context = {
        'cutoffs': {}
    }
    
    # Get all cutoffs for this configuration
    cutoffs = Cutoff.objects.filter(configuration=configuration)
    
    # Calculate overall metrics
    total_sections = cutoffs.count()
    passed_sections = 0
    total_score = 0
    
    # Prepare cutoff data for each section
    for cutoff in cutoffs:
        section_id = cutoff.assessment_section.id
        
        # Find section score
        section_score = 0
        
        for level, level_data in scores.items():
            if level != 'question_level' and section_id in level_data['scores']:
                section_score = level_data['scores'][section_id]
                break
        
        # Determine if above or below cutoff
        is_above_cutoff = section_score >= cutoff.cutoff_score
        
        # Format the description HTML
        if is_above_cutoff and cutoff.above_cutoff_description:
            description_html = cutoff.above_cutoff_description.html
            formatted_description = format_quill_html_section(description_html, request, base_url)
        elif not is_above_cutoff and cutoff.below_cutoff_description:
            description_html = cutoff.below_cutoff_description.html
            formatted_description = format_quill_html_section(description_html, request, base_url)
        else:
            formatted_description = ""
        
        context['cutoffs'][section_id] = {
            'section': cutoff.assessment_section,
            'score': section_score,
            'cutoff_score': cutoff.cutoff_score,
            'is_above_cutoff': is_above_cutoff,
            'description': formatted_description,
            'cutoff_label': cutoff.cutoff_label
        }
        
        # Update overall metrics
        if is_above_cutoff:
            passed_sections += 1
        total_score += section_score
    
    # Calculate overall score as average of section scores
    overall_score = total_score / total_sections if total_sections > 0 else 0
    
    context['overall_score'] = round(overall_score, 1)
    context['total_sections'] = total_sections
    context['passed_sections'] = passed_sections
    
    # Generate cutoff graphs
    context['cutoff_graphs'] = generate_cutoff_graphs(cutoffs, context['cutoffs'])
    
    return context

def generate_cutoff_graphs(cutoffs, cutoff_data):
    """Generate graphs for cutoffs"""
    graphs = {}
    
    for cutoff in cutoffs:
        section_id = cutoff.assessment_section.id
        if section_id not in cutoff_data:
            continue
            
        data = cutoff_data[section_id]
        
        # Create figure with better styling
        fig, ax = plt.subplots(figsize=(8, 3))
        
        # Create a horizontal bar chart
        score_bar = ax.barh(['Your Score'], [data['score']], height=0.4, color='#3498db', label='Your Score')
        cutoff_bar = ax.barh(['Cutoff'], [cutoff.cutoff_score], height=0.4, color='#e74c3c', label='Cutoff')
        
        # Add data labels
        for bar in [score_bar, cutoff_bar]:
            for rect in bar:
                width = rect.get_width()
                ax.text(width + 1, rect.get_y() + rect.get_height()/2, f'{width:.1f}%',
                        ha='left', va='center', fontweight='bold')
        
        # Add styling
        ax.set_xlim(0, 105)  # Give some space for labels
        ax.set_xlabel('Score (%)', fontweight='bold')
        ax.set_title(f"{cutoff.assessment_section.title} Performance", fontweight='bold')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='x', linestyle='--', alpha=0.7)
        
        # Add legend
        ax.legend(loc='lower right')
        
        # Add pass/fail indicator
        is_pass = data['score'] >= cutoff.cutoff_score
        status_text = "PASS" if is_pass else "NEEDS IMPROVEMENT"
        status_color = "#27ae60" if is_pass else "#e74c3c"
        
        # Add text annotation for pass/fail
        plt.figtext(0.5, 0.01, status_text, ha="center", fontsize=12, 
                   bbox={"facecolor": status_color, "alpha": 0.2, "pad": 5, "boxstyle": "round"})
        
        # Save to buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        
        # Convert to base64
        graph_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        graphs[section_id] = f"data:image/png;base64,{graph_data}"
        
        plt.close(fig)
    
    return graphs

def prepare_interpretative_report_context(configuration, session, scores, request):
    """Prepare context for interpretative report"""
    context = {
        'sections': {},
        'bands': {}  # Keep this for backward compatibility
    }
    
    # Calculate overall score
    overall_score = 0
    section_count = 0
    
    # Get main sections scores for level_0 or level_1
    main_sections = []
    main_scores = {}
    
    if 'level_0' in scores:
        main_sections = scores['level_0']['sections']
        main_scores = scores['level_0']['scores']
    elif 'level_1' in scores:
        main_sections = scores['level_1']['sections']
        main_scores = scores['level_1']['scores']
    
    # Calculate overall score as average of main section scores
    if main_scores:
        overall_score = sum(main_scores.values()) / len(main_scores)
    
    context['overall_score'] = round(overall_score, 1)
    
    # Handle score conversion
    if configuration.score_conversion == 'percentage':
        context['converted_score'] = round(overall_score, 1)
        context['score_conversion_label'] = 'Percentage'
    elif configuration.score_conversion == 'percentile':
        context['converted_score'] = round(overall_score, 1)  # Would need percentile calculation
        context['score_conversion_label'] = 'Percentile'
    elif configuration.score_conversion == 'sten':
        # Convert to STEN (1-10 scale)
        sten_score = 1 + (overall_score / 100) * 9
        context['converted_score'] = round(sten_score, 1)
        context['score_conversion_label'] = 'STEN Score'
    elif configuration.score_conversion == 'stenine':
        # Convert to STENINE (1-9 scale)
        stenine_score = 1 + (overall_score / 100) * 8
        context['converted_score'] = round(stenine_score, 1)
        context['score_conversion_label'] = 'STENINE Score'
    else:  # raw
        context['converted_score'] = round(overall_score, 1)
        context['score_conversion_label'] = 'Raw Score'
    
    # Get all bands for this configuration
    bands = Band.objects.filter(configuration=configuration)
    
    # Try to find an overall band
    for band in bands:
        if band.assessment_section.parent is None and band.min_range <= overall_score <= band.max_range:
            context['overall_band'] = band
            break
    
    # If no specific overall band, use the first main section's band
    if 'overall_band' not in context and bands.exists():
        context['overall_band'] = bands.first()
    
    # Generate overall performance chart
    context['overall_chart'] = generate_overall_performance_chart(main_sections, main_scores)
    
    # Group bands by section
    section_bands = {}
    for band in bands:
        section_id = band.assessment_section.id
        if section_id not in section_bands:
            section_bands[section_id] = []
        section_bands[section_id].append(band)
    
    # Find appropriate band for each section
    for section_id, section_band_list in section_bands.items():
        # Find section score
        section_score = 0
        section = None
        
        for level, level_data in scores.items():
            if level != 'question_level' and section_id in level_data['scores']:
                section_score = level_data['scores'][section_id]
                # Find the section object from the scores
                for s in level_data['sections']:
                    if s.id == section_id:
                        section = s
                        break
                break
        
        if not section:
            continue
            
        # Find the band that matches the score
        matching_band = None
        for band in section_band_list:
            if band.min_range <= section_score <= band.max_range:
                matching_band = band
                break
        
        if matching_band:
            # Get the original description HTML
            description_html = matching_band.description.html if matching_band.description else ''
            
            # Initialize chart_data as None or empty string before the if blocks
            chart_data = ""
            scores_table = ""

            # Replace placeholders in the description
            if description_html:
                # Format the HTML content
                description_html = format_quill_html_section(description_html, request)
                
                # Replace placeholders
                if '[[table]]' in description_html:
                    # Update table styling for better PDF rendering
                    scores_table = f"""
                    <!--div class="table-container"-->
                        <table class="report-table" style="width:80%; margin: 0 auto; border-collapse:collapse;">
                            <thead>
                                <tr>
                                    <th style="padding:8px; background-color:#3498db; color:white; border:1px solid #ddd; text-align:left;">Section</th>
                                    <th style="padding:8px; background-color:#3498db; color:white; border:1px solid #ddd; text-align:left;">Score</th>
                                    <th style="padding:8px; background-color:#3498db; color:white; border:1px solid #ddd; text-align:left;">Band</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style="padding:8px; border:1px solid #ddd;">{section.title}</td>
                                    <td style="padding:8px; border:1px solid #ddd;">{section_score}%</td>
                                    <td style="padding:8px; border:1px solid #ddd;">{matching_band.label}</td>
                                </tr>
                            </tbody>
                        </table>
                    <!--/div-->
                    """
                    description_html = description_html.replace('[[table]]', scores_table)
                
                if '[[graph]]' in description_html:
                    chart_data = generate_band_graph(section, section_score, matching_band)
                    # Wrap graph in div with center alignment
                    chart_html = f"""
                    <!--div class="graph-container"-->
                        <img src="{chart_data}" alt="{section.title} Performance Chart" style="max-width: 80%; margin: 0 auto;">
                    <!--/div-->
                    """
                    description_html = description_html.replace('[[graph]]', chart_html)
            
            
            # Add to context using sections dictionary (for template)
            context['sections'][section_id] = {
                'section': section,
                'score': section_score,
                'band': matching_band,
                'chart': chart_data,
                'scores_table': scores_table,
                'processed_description': description_html  # Add the processed description with placeholders replaced
            }
            
            # Keep band data separately in bands dict (for backward compatibility)
            context['bands'][section_id] = {
                'section': section,
                'score': section_score,
                'band': matching_band,
                'description': description_html  # Use the processed description here too
            }
    
    return context

def format_quill_html_section(html_content, request=None, base_url=None):
    """Format a section of Quill HTML content for PDF rendering"""
    if not html_content:
        return ""
    
    # Process images - convert to absolute URLs or data URIs
    import re
    from django.conf import settings
    import os
    import base64
    import mimetypes

    # Determine base URL for absolute paths
    if request and not base_url:
        scheme = request.scheme
        domain = request.get_host()
        base_url = f"{scheme}://{domain}"
    elif not base_url:
        # Fallback if no request object is available
        domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
        base_url = f"http://{domain}"
    
    def replace_image_src(match):
        img_tag = match.group(0)
        src_match = re.search(r'src=["\'](.*?)["\']', img_tag)
        if not src_match:
            return img_tag
            
        src = src_match.group(1)
        
        # Skip if already absolute URL or data URI
        if src.startswith(('http://', 'https://', 'data:')):
            return img_tag
            
        # Try to convert to absolute URL
        if src.startswith('/'):
            # Already starts with slash
            absolute_url = f"{base_url}{src}"
        else:
            # Relative path, add slash
            absolute_url = f"{base_url}/{src}"
            
        # Try to convert to data URI if file is accessible
        try:
            # Remove leading slash if present for file path
            file_path = src.lstrip('/')
            # Check if it's a media file
            if src.startswith(settings.MEDIA_URL):
                file_path = src.replace(settings.MEDIA_URL, '', 1)
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            else:
                # For static files
                full_path = os.path.join(settings.STATIC_ROOT, file_path)
                
            if os.path.exists(full_path):
                # Get MIME type
                mime_type, _ = mimetypes.guess_type(full_path)
                if not mime_type:
                    mime_type = 'application/octet-stream'
                    
                # Read file and convert to base64
                with open(full_path, 'rb') as f:
                    encoded = base64.b64encode(f.read()).decode('utf-8')
                    data_uri = f'data:{mime_type};base64,{encoded}'
                    return img_tag.replace(src, data_uri)
        except Exception as e:
            # If any error occurs, fall back to absolute URL
            print(f"Error converting image to data URI: {e}")
            
        # Return with absolute URL
        return img_tag.replace(src, absolute_url)
    
    # Replace all image tags with processed versions
    html_content = re.sub(r'<img[^>]+>', replace_image_src, html_content)
    


    # Split the content by placeholders to process each text section separately
    placeholders = ["[[table]]", "[[graph]]"]
    sections = []
    current_text = html_content
    
    # Extract sections separated by placeholders
    for placeholder in placeholders:
        if placeholder in current_text:
            parts = current_text.split(placeholder)
            for i, part in enumerate(parts):
                if i > 0:
                    sections.append(placeholder)  # Add the placeholder back
                if part.strip():  # Only add non-empty parts
                    sections.append(part)
            current_text = ""  # Processed all content
        
    # If no placeholders were found, add the whole content as one section
    if current_text.strip():
        sections.append(current_text)
    
    # Process each text section according to the rules
    for i, section in enumerate(sections):
        if section in placeholders:
            continue  # Skip placeholder sections
            
        # Rule 1: Remove first <p> tag
        if section.startswith('<p>'):
            section = section[3:]
            
        # Rule 2: Replace intermediate </p><p> with <br>
        section = section.replace('</p><p>', '<br>')
        
        # Rule 3: Remove last </p> tag
        if section.endswith('</p>'):
            section = section[:-4]
            
        sections[i] = section
    
    # Rejoin all sections
    return ''.join(sections)

def generate_overall_performance_chart(sections, scores):
    """Generate chart for overall performance"""
    if not sections:
        return ""
        
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract section titles and scores
    titles = [section.title for section in sections]
    values = [scores.get(section.id, 0) for section in sections]
    
    # Create horizontal bar chart
    bars = ax.barh(titles, values, height=0.5, color='#007bff')
    
    # Add data labels
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2, f'{width:.1f}%', 
                ha='left', va='center', fontweight='bold')
    
    # Set chart properties
    ax.set_xlim(0, 100)
    ax.set_xlabel('Score (%)')
    ax.set_title('Overall Performance by Section')
    
    # Add grid lines
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Save to buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    
    # Convert to base64
    graph_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return f"data:image/png;base64,{graph_data}"

def generate_band_graph(section, score, band):
    """Generate graph for a band"""
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 2))
    
    # Add bar
    ax.barh([section.title], [score], height=0.4, color=band.color)
    
    # Add labels
    ax.set_xlim(0, 100)
    ax.set_xlabel('Score (%)')
    ax.set_title(f"{section.title} - {band.label}")
    
    # Save to buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    
    # Convert to base64
    graph_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{graph_data}"

def prepare_group_report_context(configuration, session, scores, request=None, base_url=None):
    """Prepare context for group report"""
    context = {
        'candidates': [],
        'organization_name': configuration.title,  # Use configuration title as org name
    }
    
    # Get candidates from the ManyToMany relationship
    # Check if the candidates attribute exists (for backward compatibility)
    if hasattr(configuration, 'candidates'):
        candidates = configuration.candidates.all()
    else:
        # Fallback to empty list if no candidates attribute
        candidates = []

    if not candidates:
        return context
    
    # Get sessions for all candidates who took this assessment
    candidate_sessions = AssessmentSession.objects.filter(
        assessment=configuration.assessment,
        user__in=candidates,
        status='completed'
    ).select_related('user').order_by('user__last_name', 'user__first_name')
    
    # Get main sections for the assessment
    main_sections = Section.objects.filter(
        assessment=configuration.assessment,
        parent=None,
        is_section=True
    ).order_by('order')
    
    context['main_sections'] = main_sections
    
    # Prepare candidate data
    for candidate_session in candidate_sessions:
        # Get all section scores for this candidate
        section_scores = {}
        
        # Process scores from session.scores dictionary
        for key, value in candidate_session.scores.items():
            # Keys are in format 'section_X' where X is the section ID
            if key.startswith('section_'):
                section_id = int(key.split('_')[1])
                section_scores[section_id] = value
        
        candidate_data = {
            'user': candidate_session.user,
            'session': candidate_session,
            'scores': section_scores
        }
        
        context['candidates'].append(candidate_data)
    
    return context

def prepare_question_level_report_context(configuration, session):
    """Prepare context for question level report"""
    context = {
        'question_responses': []
    }
    
    # Get all responses for this session
    responses = QuestionResponse.objects.filter(
        session=session
    ).select_related('question', 'question__category').prefetch_related(
        'question__options'  # Keep only valid relationships
    ).order_by('id')
    
    # Count correct and incorrect answers
    correct_count = sum(1 for response in responses if response.is_correct)
    incorrect_count = len(responses) - correct_count
    
    # Calculate overall score
    if responses:
        overall_score = (correct_count / len(responses)) * 100
    else:
        overall_score = 0
    
    # Prepare question response data
    question_responses = []
    for response in responses:
        # Ensure answer_data is properly formatted
        if isinstance(response.answer_data, str):
            try:
                # Try to parse JSON if it's a string
                import json
                answer_data = json.loads(response.answer_data)
            except (json.JSONDecodeError, TypeError):
                # If not valid JSON, keep as is
                answer_data = response.answer_data
        else:
            answer_data = response.answer_data
            
        processed_response = {
            'question': response.question,
            'answer_data': answer_data,
            'is_correct': response.is_correct,
            'score': response.score
        }
        
        question_responses.append(processed_response)
    
    # Add to context
    context['question_responses'] = question_responses
    context['correct_count'] = correct_count
    context['incorrect_count'] = incorrect_count
    context['overall_score'] = round(overall_score, 1)
    
    # Format description and objectives from Quill fields
    if configuration.description and configuration.description.html:
        context['formatted_description'] = format_quill_html_section(configuration.description.html)
    
    if configuration.objectives and configuration.objectives.html:
        context['formatted_objectives'] = format_quill_html_section(configuration.objectives.html)
    
    return context

# def prepare_typological_report_context(configuration, session, scores):
#     """Prepare context for typological report"""
#     context = {
#         'contrast_variables': [],
#         'type_code': ''
#     }
    
#     # Get all responses for this session with contrast variables
#     responses = QuestionResponse.objects.filter(
#         session=session,
#         question__type='psy_forced_one'
#     )
    
#     # Extract category and subcategory scores from responses
#     category_scores = {}
#     subcategory_scores = {}
#     percentage_scores = {}
    
#     for response in responses:
#         if response.psy_score:
#             # Process scores for categories and subcategories
#             if 'scores' in response.psy_score:
#                 scores_data = response.psy_score['scores']
                
#                 # Update category scores
#                 if 'category_scores' in scores_data:
#                     for cat_id, score in scores_data['category_scores'].items():
#                         if cat_id not in category_scores:
#                             category_scores[cat_id] = 0
#                         category_scores[cat_id] += score
                
#                 # Update subcategory scores
#                 if 'subcategory_scores' in scores_data:
#                     for subcat_id, score in scores_data['subcategory_scores'].items():
#                         if subcat_id not in subcategory_scores:
#                             subcategory_scores[subcat_id] = 0
#                         subcategory_scores[subcat_id] += score
                
#                 # Get percentage scores for CV1 and CV2
#                 if 'percentage_scores' in scores_data:
#                     for subcat_id, percentage in scores_data['percentage_scores'].items():
#                         if subcat_id not in percentage_scores:
#                             percentage_scores[subcat_id] = 0
#                         percentage_scores[subcat_id] += percentage
    
#     # Get all contrast variables for this configuration
#     contrast_variables = ContrastVariable.objects.filter(
#         configuration=configuration
#     ).order_by('name')
    
#     # Calculate scores for each contrast variable
#     cv_scores = []
#     for cv in contrast_variables:
#         subcategory_id = cv.subcategory
#         raw_score = subcategory_scores.get(subcategory_id, 0)
        
#         # Use percentage score if available, otherwise calculate
#         percentage_score = percentage_scores.get(subcategory_id, 0)
        
#         cv_data = {
#             'id': cv.id,
#             'name': cv.name,
#             'code': cv.code,
#             'color': cv.color,
#             'description': cv.description.html if cv.description else '',
#             'score': raw_score,
#             'percentage_score': percentage_score
#         }
        
#         # Find matching band for this score
#         bands = TypeBand.objects.filter(
#             configuration=configuration,
#             contrast_variable=cv
#         )
        
#         for band in bands:
#             if band.min_range <= percentage_score <= band.max_range:
#                 cv_data['band'] = {
#                     'id': band.id,
#                     'name': band.name,
#                     'label': band.label,
#                     'color': band.color,
#                     'description': band.description.html if band.description else ''
#                 }
#                 break
        
#         cv_scores.append(cv_data)
    
#     # Sort contrast variables by score (descending)
#     cv_scores.sort(key=lambda x: x['percentage_score'], reverse=True)
    
#     # Get top N contrast variables based on type_code_count
#     top_cvs = cv_scores[:configuration.type_code_count]
    
#     # Generate type code from top contrast variables
#     type_code = ''.join([cv['code'] for cv in top_cvs])
    
#     context['contrast_variables'] = top_cvs
#     context['type_code'] = type_code
    
#     # Generate summary graph for all contrast variables
#     context['summary_chart'] = generate_cv_summary_chart(cv_scores)
    
#     return context

def prepare_typological_report_context(configuration, session, scores):
    """Prepare context for typological report"""
    context = {
        'contrast_variables': [],
        'type_code': ''
    }
    
    # Get all responses for this session with contrast variables
    responses = QuestionResponse.objects.filter(
        session=session,
        question__type='psy_forced_one'
    )
    
    # Extract category and subcategory scores from responses
    category_scores = {}
    subcategory_scores = {}
    percentage_scores = {}
    
    for response in responses:
        if response.psy_score:
            # Process scores for categories and subcategories
            if 'scores' in response.psy_score:
                scores_data = response.psy_score['scores']
                
                # Update category scores
                if 'category_scores' in scores_data:
                    for cat_id, score in scores_data['category_scores'].items():
                        if cat_id not in category_scores:
                            category_scores[cat_id] = 0
                        category_scores[cat_id] += score
                
                # Update subcategory scores
                if 'subcategory_scores' in scores_data:
                    for subcat_id, score in scores_data['subcategory_scores'].items():
                        if subcat_id not in subcategory_scores:
                            subcategory_scores[subcat_id] = 0
                        subcategory_scores[subcat_id] += score
                
                # Get percentage scores for CV1 and CV2
                if 'percentage_scores' in scores_data:
                    for subcat_id, percentage in scores_data['percentage_scores'].items():
                        if subcat_id not in percentage_scores:
                            percentage_scores[subcat_id] = 0
                        percentage_scores[subcat_id] += percentage
    
    # Get all contrast variables for this configuration
    contrast_variables = ContrastVariable.objects.filter(
        configuration=configuration
    ).order_by('name')
    
    # Calculate scores for each contrast variable
    cv_scores = []
    for cv in contrast_variables:
        subcategory_id = cv.subcategory
        raw_score = subcategory_scores.get(subcategory_id, 0)
        
        # Use percentage score if available, otherwise calculate
        percentage_score = percentage_scores.get(subcategory_id, 0)
        
        cv_data = {
            'id': cv.id,
            'name': cv.name,
            'code': cv.code,
            'color': cv.color,
            'description': cv.description.html if cv.description else '',
            'score': raw_score,
            'percentage_score': percentage_score
        }
        
        # Find matching band for this score
        bands = TypeBand.objects.filter(
            configuration=configuration,
            contrast_variable=cv
        )
        
        for band in bands:
            if band.min_range <= percentage_score <= band.max_range:
                # Process band description with placeholders
                band_description = band.description.html if band.description else ''
                
                # Process the description to replace placeholders
                if band_description:
                    # Format the HTML content
                    band_description = format_quill_html_section(band_description)
                    
                    # Replace placeholders
                    if '[[table]]' in band_description:
                        # Create a table showing the contrast variable score
                        scores_table = f"""
                        <table class="report-table" style="width:80%; margin: 0 auto; border-collapse:collapse;">
                            <thead>
                                <tr>
                                    <th style="padding:8px; background-color:{cv.color}; color:white; border:1px solid #ddd; text-align:left;">Contrast Variable</th>
                                    <th style="padding:8px; background-color:{cv.color}; color:white; border:1px solid #ddd; text-align:left;">Score</th>
                                    <th style="padding:8px; background-color:{cv.color}; color:white; border:1px solid #ddd; text-align:left;">Band</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style="padding:8px; border:1px solid #ddd;">{cv.name}</td>
                                    <td style="padding:8px; border:1px solid #ddd;">{percentage_score}%</td>
                                    <td style="padding:8px; border:1px solid #ddd;">{band.label}</td>
                                </tr>
                            </tbody>
                        </table>
                        """
                        band_description = band_description.replace('[[table]]', scores_table)
                    
                    if '[[graph]]' in band_description:
                        # Generate a simple bar chart for this contrast variable
                        chart_data = generate_cv_band_graph(cv, percentage_score, band)
                        chart_html = f"""
                        <img src="{chart_data}" alt="{cv.name} Performance Chart" style="max-width: 80%; margin: 0 auto; display: block;">
                        """
                        band_description = band_description.replace('[[graph]]', chart_html)
                
                cv_data['band'] = {
                    'id': band.id,
                    'name': band.name,
                    'label': band.label,
                    'color': band.color,
                    'description': band_description  # Use processed description
                }
                break
        
        cv_scores.append(cv_data)
    
    # Sort contrast variables by score (descending)
    cv_scores.sort(key=lambda x: x['percentage_score'], reverse=True)
    
    # Get top N contrast variables based on type_code_count
    top_cvs = cv_scores[:configuration.type_code_count]
    
    # Generate type code from top contrast variables
    type_code = ''.join([cv['code'] for cv in top_cvs])
    
    context['contrast_variables'] = top_cvs
    context['type_code'] = type_code
    
    # Generate summary graph for all contrast variables
    context['summary_chart'] = generate_cv_summary_chart(cv_scores)
    
    return context

# Add a new function to generate contrast variable band graphs
def generate_cv_band_graph(cv, score, band):
    """Generate graph for a contrast variable band"""
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 2))
    
    # Add bar
    ax.barh([cv.name], [score], height=0.4, color=band.color)
    
    # Add labels
    ax.set_xlim(0, 100)
    ax.set_xlabel('Score (%)')
    ax.set_title(f"{cv.name} - {band.label}")
    
    # Save to buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    
    # Convert to base64
    graph_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return f"data:image/png;base64,{graph_data}"

def generate_cv_summary_chart(cv_scores):
    """Generate chart for contrast variable summary"""
    if not cv_scores:
        return ""
        
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract CV names and scores
    names = [cv['name'] for cv in cv_scores]
    values = [cv['percentage_score'] for cv in cv_scores]
    colors = [cv['color'] for cv in cv_scores]
    
    # Create horizontal bar chart
    bars = ax.barh(names, values, height=0.5, color=colors)
    
    # Add data labels
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2, f'{width:.1f}%', 
                ha='left', va='center', fontweight='bold')
    
    # Set chart properties
    ax.set_xlim(0, 100)
    ax.set_xlabel('Score (%)')
    ax.set_title('Contrast Variable Scores')
    
    # Add grid lines
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Save to buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    
    # Convert to base64
    graph_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return f"data:image/png;base64,{graph_data}"



# Assessment Payment 

@login_required
def assessment_booking_list(request):
    """List all assessment bookings for the user"""
    bookings = AssessmentBooking.objects.filter(user=request.user).order_by('-booked_at')
    
    paginator = Paginator(bookings, 10)
    page = request.GET.get('page')
    
    try:
        bookings = paginator.page(page)
    except PageNotAnInteger:
        bookings = paginator.page(1)
    except EmptyPage:
        bookings = paginator.page(paginator.num_pages)
    
    return render(request, 'reports/booking_list.html', {
        'bookings': bookings,
        'is_paginated': True if paginator.num_pages > 1 else False
    })

@login_required
def book_assessment(request):
    """Book an assessment"""
    if request.method == 'POST':
        form = AssessmentBookingForm(request.POST, user=request.user)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            
            # Calculate amount based on report count
            assessment = booking.assessment
            base_price = 100.00  # Default price, customize as needed
            report_count = booking.report_count
            booking.amount = base_price * report_count
            
            booking.save()
            
            # Proceed to payment
            return redirect('reports:assessment_payment', booking_id=booking.id)
    else:
        form = AssessmentBookingForm(user=request.user)
    
    # Get published assessments for display in cards
    assessments = Assessment.objects.filter(published=True)
    
    return render(request, 'reports/book_assessment.html', {
        'form': form,
        'assessments': assessments
    })

@login_required
def assessment_payment(request, booking_id):
    """Payment for assessment booking"""
    booking = get_object_or_404(AssessmentBooking, pk=booking_id, user=request.user)
    
    # Create Razorpay order
    rzp = RzpClient()
    amount = int(booking.amount * 100)  # Convert to paise
    currency = settings.RAZORPAY_CURRENCY
    
    order_data = {
        "amount": amount,
        "currency": currency,
        "payment_capture": "1",
        "receipt": str(booking.id)
    }
    
    order = rzp.createOrder(order_data)
    order_id = order['id']
    booking.rzp_order_id = order_id
    booking.save()
    
    context = {
        "key": settings.RAZORPAY_KEY_ID,
        "amount": amount,
        "currency": currency,
        "order_id": order_id,
        "booking": booking,
        "callback_url": request.build_absolute_uri(reverse('reports:payment_callback'))
    }
    
    return render(request, 'reports/payment.html', context)

@csrf_exempt
def payment_callback(request):
    """Callback for payment verification"""
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        
        # Verify payment
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        rzp = RzpClient()
        
        try:
            verified = rzp.verifyPayment(params_dict)
            
            if verified:
                # Payment successful
                booking = AssessmentBooking.objects.get(rzp_order_id=order_id)
                booking.rzp_payment_id = payment_id
                booking.rzp_signature = signature
                booking.paid = True
                booking.status = 'completed'
                booking.save()
                
                messages.success(request, "Payment successful. Your assessment is now available.")
                return redirect('reports:assessment_booking_list')
            else:
                messages.error(request, "Payment verification failed.")
                return redirect('reports:assessment_booking_list')
                
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('reports:assessment_booking_list')
    
    return redirect('reports:assessment_booking_list')

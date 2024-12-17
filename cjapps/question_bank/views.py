# from django.shortcuts import render
# from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Category
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Question, GridOption
from .forms import (
    QuestionBasicForm, #QuestionCategoryForm, QuestionContentForm,
    QuestionOptionFormSet, FlashCardFormSet, MatchingPairFormSet, AnswerOptionFormSet,
    GridOptionFormSet, GridOptionForm,
)
from . import models
from . import forms
import json
from .utils import DecimalEncoder

def manage_categories(request):
    return render(request, 'question_bank/manage_categories.html')

def get_categories(request):
    categories = Category.objects.all()
    return JsonResponse([{
        'id': category.id,
        'parent': category.parent_id or '#',
        'text': category.name,
    } for category in categories], safe=False)

@require_POST
@csrf_exempt
def update_category(request):
    category_id = request.POST.get('id')
    parent_id = request.POST.get('parent')
    name = request.POST.get('name')

    try:
        category = Category.objects.get(id=category_id)
        
        if parent_id is not None:
            if parent_id != '#':
                category.parent = Category.objects.get(id=parent_id)
            else:
                category.parent = None

        if name is not None:
            category.name = name
        category.save()
        return JsonResponse({'status': 'success'})
    except Category.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Category not found'}, status=404)
    except ValidationError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@csrf_exempt
def create_category(request):
    name = request.POST.get('name')
    parent_id = request.POST.get('parent')

    try:
        parent = None if parent_id == '#' else Category.objects.get(id=parent_id)
        category = Category.objects.create(name=name, parent=parent)
        return JsonResponse({
            'status': 'success',
            'id': category.id,
            'name': category.name,
        })
    except ValidationError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
@csrf_exempt
def delete_category(request):
    category_id = request.POST.get('id')
    try:
        category = Category.objects.get(id=category_id)
        category.delete()
        return JsonResponse({'status': 'success'})
    except Category.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Category not found'}, status=404)


# question section

@login_required
def create_question(request):
    if request.method == 'POST':
        basic_form = QuestionBasicForm(request.POST, request.FILES)
        if basic_form.is_valid():
            question = basic_form.save(commit=False)
            question.created_by = request.user
            question.save()
            
            grid_formset = GridOptionFormSet(request.POST, request.FILES, instance=question, prefix='grid')
            option_formset = QuestionOptionFormSet(request.POST, request.FILES, instance=question, prefix='option')
            flash_formset = FlashCardFormSet(request.POST, request.FILES, instance=question, prefix='flash')
            match_formset = MatchingPairFormSet(request.POST, request.FILES, instance=question, prefix='match')

            if option_formset.is_valid():
                option_formset.save()
            if flash_formset.is_valid():
                flash_formset.save()
            if match_formset.is_valid():
                match_formset.save()
            if grid_formset.is_valid():
                grid_formset.save()

            rating_formset = forms.PsyRatingFormSet(request.POST, instance=question, prefix='rating')
            if question.type == 'psy_rating':
                if rating_formset.is_valid():
                    rating_formset.save()

            if question.type == 'psy_ranking':
                question.ranking_structure = request.POST.get('ranking_data')
                question.save()

            messages.success(
                request, f"Question ({question.title}) has been created successfully."
            )

            return redirect('question_bank:question_list')
        else:
            messages.error(
                request, f"Something went wrong, please fill all fields correctly."
            )
    # else:
    basic_form = QuestionBasicForm()

    grid_formset = GridOptionFormSet(prefix='grid')
    option_formset = QuestionOptionFormSet(prefix='option')
    flash_formset = FlashCardFormSet(prefix='flash')
    match_formset = MatchingPairFormSet(prefix='match')
    answer_formset = AnswerOptionFormSet(prefix='answer')

    # rating_formset = RatingItemFormSet(prefix='rating')
    # ranking_formset = RankingItemFormSet(prefix='ranking')

    # ranking_formset = forms.RankingFormSet(prefix='ranking')
    # ranknrate_formset = forms.RankRateFormSet(prefix='ranknrate')
    # # rating_formset = forms.RatingFormSet(prefix='rating')
    # forcedsingle_formset = forms.ForcedChoiceSingleFormSet(prefix='forcedsingle')
    # forcedtwo_formset = forms.ForcedChoiceTwoFormSet(prefix='forcedtwo')

    rating_formset = forms.PsyRatingFormSet(prefix='rating')

    return render(request, 'question_bank/create_question.html', {
        'basic_form': basic_form,
        'answer_formset': answer_formset,
        'option_formset': option_formset,
        'match_formset': match_formset,
        'flash_formset': flash_formset,
        'grid_formset': grid_formset,

        'rating_formset': rating_formset,
    })

@login_required
def edit_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        basic_form = QuestionBasicForm(request.POST, request.FILES, instance=question)
        if basic_form.is_valid():
            question = basic_form.save(commit=False)
            question.save()
        
        grid_formset = GridOptionFormSet(request.POST, request.FILES, instance=question, prefix='grid')
        option_formset = QuestionOptionFormSet(request.POST, request.FILES, instance=question, prefix='option')
        flash_formset = FlashCardFormSet(request.POST, request.FILES, instance=question, prefix='flash')
        match_formset = MatchingPairFormSet(request.POST, request.FILES, instance=question, prefix='match')
        
        if option_formset.is_valid():
            option_formset.save()
        if flash_formset.is_valid():
            flash_formset.save()
        if match_formset.is_valid():
            match_formset.save()
        if grid_formset.is_valid():
            grid_formset.save()
        
        rating_formset = forms.PsyRatingFormSet(request.POST, prefix='rating', instance=question)
        if question.type == 'psy_rating' and rating_formset.is_valid():
            rating_formset.save()

        if question.type == 'psy_ranking':
            question.ranking_structure = request.POST.get('ranking_data')
            question.save()

        messages.success(
            request, f"Question ({question.title}) has been updated successfully."
        )

        return redirect('question_bank:question_list')
    else:
        basic_form = QuestionBasicForm(instance=question) #, initial={'flash_interval': question.flash_interval}

        option_formset = QuestionOptionFormSet(prefix='option', instance=question)
        match_formset = MatchingPairFormSet(prefix='match', instance=question)
        flash_formset = FlashCardFormSet(prefix='flash', instance=question)
        answer_formset = AnswerOptionFormSet(prefix='answer', instance=question)
        grid_formset = GridOptionFormSet(prefix='grid', instance=question)
    
        grid_forms = [grid_formset.forms[i:i+question.grid_cols] for i in range(0, len(grid_formset.forms), question.grid_cols)]

        rating_formset = forms.PsyRatingFormSet(prefix='rating', instance=question)
        # ranking_formset = RankingItemFormSet(prefix='ranking', instance=question)
        
    return render(request, 'question_bank/edit_question.html', {
        'question': question,
        'basic_form': basic_form,
        
        'answer_formset': answer_formset,
        'option_formset': option_formset,
        'match_formset': match_formset,
        'flash_formset': flash_formset,
        
        'grid_formset': grid_formset,
        'grid_forms': grid_forms,

        'rating_formset': rating_formset,
        # 'ranking_formset': ranking_formset,

    })

@login_required
def question_detail(request, pk):
    question = get_object_or_404(Question, pk=pk)
    return render(request, 'question_bank/question_detail.html', {'question': question})

@login_required
def question_list(request):
    if request.user.is_superuser:
        questions = Question.objects.all().order_by('-created_at')
    else:
        questions = Question.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'question_bank/question_list.html', {'questions': questions})

@login_required
def delete_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'GET':
        question.delete()
        # return redirect('question_bank:question_list')
    return redirect('question_bank:question_list')
    #return render(request, 'question_bank/delete_question.html', {'question': question})


def get_ranking_categories(request):
    def get_category_data(category):
        return {
            'id': category.id,
            'name': category.name,
            'subcategories': [get_category_data(subcat) for subcat in category.subcategories.all()],
            'statements': [{'id': statement.id, 'text': statement.text} for statement in category.statements.all()]
        }

    categories = Category.objects.filter(parent=None).prefetch_related('subcategories', 'statements')
    data = [get_category_data(category) for category in categories]
    return JsonResponse(data, safe=False)

def get_ranking_groups(request):
    rank_groups = RankGroup.objects.all()
    data = [
        {
            'id': group.id,
            'name': group.name,
            'statements': []
        }
        for group in rank_groups
    ]
    return JsonResponse(data, safe=False)

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import PsyCategory, PsySubcategory, PsyStatement, PsyRankGroup, PsyRankGroupStatement

def ranking_question_view(request):
    categories = PsyCategory.objects.prefetch_related('subcategories', 'statements').all()
    return render(request, 'ranking_question.html', {'categories': categories})

# @csrf_exempt
# def create_category(request):
#     name = request.POST.get('name')
#     category = PsyCategory.objects.create(name=name)
#     return JsonResponse({'id': category.id, 'name': category.name})

@csrf_exempt
def create_subcategory(request):
    category_id = request.POST.get('category_id')
    name = request.POST.get('name')
    category = get_object_or_404(PsyCategory, id=category_id)
    subcategory = PsySubcategory.objects.create(category=category, name=name)
    return JsonResponse({'id': subcategory.id, 'name': subcategory.name})

# @csrf_exempt
# def create_statement(request):
#     category_id = request.POST.get('category_id')
#     subcategory_id = request.POST.get('subcategory_id', None)
#     text = request.POST.get('text')
#     category = get_object_or_404(PsyCategory, id=category_id)
#     subcategory = None if not subcategory_id else get_object_or_404(PsySubcategory, id=subcategory_id)
#     statement = PsyStatement.objects.create(category=category, subcategory=subcategory, text=text)
#     return JsonResponse({'id': statement.id, 'text': statement.text})
@csrf_exempt
def create_statement(request):
    category_id = request.POST.get('category_id', None)
    subcategory_id = request.POST.get('subcategory_id', None)
    text = request.POST.get('text')

    # Extract numeric ID by removing any prefix ('cat_', 'sub_')
    if category_id:
        category_id = category_id.split('_')[1]  # Only keep the numeric part

    if subcategory_id:
        subcategory_id = subcategory_id.split('_')[1]  # Only keep the numeric part

    # Create a new statement under the correct category or subcategory
    if category_id:
        statement = PsyStatement.objects.create(category_id=category_id, text=text)
    elif subcategory_id:
        statement = PsyStatement.objects.create(subcategory_id=subcategory_id, text=text)
    
    return JsonResponse({'id': statement.id, 'text': statement.text})

@csrf_exempt
def create_rank_group(request):
    title = request.POST.get('title')
    rank_group = PsyRankGroup.objects.create(title=title)
    return JsonResponse({'id': rank_group.id, 'title': rank_group.title})

@csrf_exempt
def add_statement_to_rank_group(request):
    rank_group_id = request.POST.get('rank_group_id')
    statement_id = request.POST.get('statement_id')
    rank_group = get_object_or_404(PsyRankGroup, id=rank_group_id)
    statement = get_object_or_404(PsyStatement, id=statement_id)
    PsyRankGroupStatement.objects.create(rank_group=rank_group, statement=statement)
    return JsonResponse({'status': 'success'})


@csrf_exempt
def fetch_jstree_data(request):
    node_id = request.GET.get('id', '#')
    
    if node_id == '#':  # This is the root node, so we return categories.
        categories = PsyCategory.objects.all()
        data = [
            {
                "id": f"cat_{category.id}",
                "text": category.name,
                "children": True,  # This indicates the category has children (subcategories/statements)
            }
            for category in categories
        ]
    else:
        node_type, node_id = node_id.split('_')
        
        if node_type == 'cat':  # If the node is a category, return its subcategories/statements.
            subcategories = PsySubcategory.objects.filter(category_id=node_id)
            statements = PsyStatement.objects.filter(category_id=node_id, subcategory__isnull=True)
            data = [
                {
                    "id": f"sub_{subcategory.id}",
                    "text": subcategory.name,
                    "children": True  # Subcategories can have statements as children
                }
                for subcategory in subcategories
            ] + [
                {
                    "id": f"stmt_{statement.id}",
                    "text": statement.text,
                    "children": False  # Statements don't have children
                }
                for statement in statements
            ]
        elif node_type == 'sub':  # If the node is a subcategory, return its statements.
            statements = PsyStatement.objects.filter(subcategory_id=node_id)
            data = [
                {
                    "id": f"stmt_{statement.id}",
                    "text": statement.text,
                    "children": False  # Statements don't have children
                }
                for statement in statements
            ]
        else:
            data = []
    
    return JsonResponse(data, safe=False)
from django.shortcuts import render
from . import models
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.urls import reverse, reverse_lazy

from django.contrib.auth.decorators import login_required

import datetime, json
from django.conf import settings
from django.contrib import messages

from cjapp.payment import RzpClient
from cjapp.zoom import ZoomClient

from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.templatetags.static import static
# Create your views here.
from . import forms
from django.forms import inlineformset_factory, modelformset_factory

from django.core import serializers
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseNotAllowed

from django.forms.models import model_to_dict
import os

import mimetypes
from django.apps import apps


class TrainingCategoryListView(ListView):
    paginate_by = 5
    model = models.Category
    template_name = 'training_category_list.html'
    
class TrainingCategoryAddView(CreateView):
    model = models.Category
    fields = ['name', 'desc']  
    template_name = 'training_category_add.html'

    def get_success_url(self):
        return reverse('training_category_list')

class TrainingCategoryEditView(UpdateView):
    model = models.Category
    fields = ['name', 'desc']
    template_name = 'training_category_edit.html'

    def get_success_url(self):
        return reverse('training_category_list')

class TrainingCategoryDeleteView(DeleteView):
    model = models.Category
    success_url = reverse_lazy("training_category_list")
    template_name = 'training_category_delete.html'

class TrainingBookingListView(ListView):
    paginate_by = 5
    model = models.Booking
    template_name = 'training_booking_list.html'

@csrf_exempt
def training_booking_payment_submit_view(request):
    if request.method == "POST":
        order_id = request.POST.get('razorpay_order_id')
        payment_id = request.POST.get('razorpay_payment_id')
        signature = request.POST.get('razorpay_signature')
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        # try:
        rzp = RzpClient()
        verified = rzp.verifyPayment(params_dict)
        if verified:
            # Payment signature verification successful
            # Perform any required actions (e.g., update the order status)
            # return render(request, 'payment_success.html')
            # bid = 10
            booking = models.Booking.objects.get(rzp_order_id=order_id)
            booking.rzp_payment_id = payment_id
            booking.rzp_signature = signature
            booking.paid = verified
            booking.save()

            messages.success(request, "Training booked Successfully.")
        else:
            # except razorpay.errors.SignatureVerificationError as e:
            # Payment signature verification failed
            # Handle the error accordingly
            # return render(request, 'payment_failure.html')
            messages.success(request, "Training booking Failed.")

        return HttpResponseRedirect(reverse('training_booking_list'))

@login_required     
def training_booking_payment_view(request, bookid=None):
    # form = forms.BookingForm(user=request.user)
    booking = models.Booking.objects.get(pk=bookid)
    amount = int(booking.training.amount) * 100
    currency = settings.RAZORPAY_CURRENCY

    """Create Razorpay Order"""
    rzp = RzpClient()
    orderOpts = {
        "amount": amount,
        "currency": currency,
        "payment_capture": "1",
        "receipt": str(booking.id)
    }
    order = rzp.createOrder(orderOpts)
    order_id = order['id']
    booking.rzp_order_id = order_id
    booking.save()
    
    context = {
        "key": settings.RAZORPAY_KEY_ID, 
        "amount": amount, 
        "currency": currency, 
        "image": static('img/favicon.png'), 
        "order_id": order_id, 
        "user": request.user,
        "redirect_url": request.build_absolute_uri(reverse('training_booking_payment_submit'))
    }
        
    return render(request, "training_payment.html", context)

@login_required     
def training_booking_add_view(request):
    if request.method == "POST":
        form = forms.BookingForm(request.POST, user=request.user)

        if form.is_valid():
            booking = form.save()

            return HttpResponseRedirect(reverse('training_booking_payment', args=[str(booking.id)]))
        else:
            messages.error(
                request, f"Somthing is not correct, please fill all fields correctly."
            )
    else:
        form = forms.BookingForm(user=request.user)
        # categories = models.Category.objects.all()


    return render(request, "training_booking.html", {
        "form": form, 
        # "categories": categories,
        "user": request.user
    })

@login_required
def training_booking_cancel_view(request, pk):
    if request.method == 'POST':
        form = forms.TrainingCancelForm(request.POST)
        if form.is_valid():
            booking = models.Booking.objects.get(pk=pk)
            booking.status = models.Booking.STATUS_CANCELLED
            booking.reason = form.cleaned_data['reason']
            booking.save()

            messages.success(request, "Training booking cancelled Successfully.")
        else:
            messages.success(request, "Something went wrong.")
        
        return HttpResponseRedirect(reverse('training_booking_list')) #, args=[str(booking.id)]
    else:
        form = forms.TrainingCancelForm()
        
    return render(request, "training_booking_cancel.html", {"title":"Training Booking Cancellation", "form": form, "user": request.user})

@login_required
def training_by_category_view(request, category_id=None):
    if category_id:
        try:
            category = models.Category.objects.get(pk=category_id)    
        except (models.Category.DoesNotExist):
            category = None

        if category:
            trainings = category.training.all()
            #data = model_to_dict(trainings)
            data = serializers.serialize('json', trainings)
            data = json.loads(data)

            return JsonResponse({'status': True, 'data': data}, safe=False)
        else:
            data = {}
            return JsonResponse({'status': False, 'data': data}, safe=False)

@login_required
def training_delivery_view(request, booking_id=None):
    booking = models.Booking.objects.get(pk=booking_id)
    training = booking.training

    if request.method == 'GET':
        modules = training.modules.all()

        # active_node.ancestors(include_self=True)
        # structure_data = get_json_tree(training.id, 'delivery')

        structure_data = get_training_state(booking, request.user)

        tracker = models.Tracker.objects.get(booking=booking)

        current_item = get_current_item(booking, request)

        completed = 'true' if tracker.completed == True else 'false'

        context = {
            "title": "Training Delivery", 
            # "form": form, 
            # "user": request.user,
            "booking_id": booking.id,
            "training_id": training.id,
            "training": training,
            "structure_data": structure_data,
            "current_item": current_item,
            "tracker": tracker,
            "completed": completed,
            "request": request,
        }
        context.update(current_item)
        return render(request, "training_delivery.html", context)
    else:
        post = request.POST
        files = request.FILES
        if 'submit_report' in post:
            assignment_id = post['assignment_id']
            tracker_id = post['tracker_id']
            # assignment = models.Assignment.objects.get(pk=post['submit_report'])
            # assignment.

            trackassignment = models.TrackAssignment(tracker_id=tracker_id, assignment_id=assignment_id, file=files['report_file'])
            trackassignment.save()

            # assignment.file = files['report_file']
            # assignment.save()
            return JsonResponse({ 'status': True, 'data': assignment_id }, safe=False)
        else:
            training = models.Training.objects.get(pk=post['training_id'])
            tracker = models.Tracker.objects.get(booking=booking)
            if post['next_id'] == 'complete':
                tracker.completed = True
            else:
                tracker.active_node = models.Node.objects.get(pk=post['next_id'])
            tracker.save()

        return HttpResponseRedirect(reverse('training_delivery', args=[str(post['booking_id'])]))

@login_required
def initiate_livesession_view(request):
    if request.method == 'POST':
        tracker_id = request.POST['tracker_id']
        livesession_id = request.POST['livesession_id']

        tracklivesession = models.TrackLivesession(tracker_id=tracker_id, session_id=livesession_id, init_schedule=True)
        tracklivesession.save()

        data = model_to_dict(tracklivesession)

        return JsonResponse({'status': True, 'data': data}, safe=False)
    else:
        data = {}
        return JsonResponse({'status': False, 'data': data}, safe=False)
    
@login_required
def submit_assignment_report_view(request):
    tracker_id = request.POST['tracker_id']
    assignment_id = request.POST['assignment_id']

@login_required
def schedule_livesession_view(request):
    if request.method == 'POST':
        from cjapp.notifications import get_notification

        notification_id = request.POST['notification_id']
        start_time      = request.POST['start_time']
        duration        = request.POST['duration']

        notification = get_notification(notification_id)

        metadata = notification.metadata.split(':')
        model_name  = metadata[0]
        model_id    = metadata[1]
        model = apps.get_model('training', model_name)
        livesession = model.objects.get(pk = model_id)
        livesession.tracker_livesession.start_time = start_time
        livesession.tracker_livesession.duration = duration
        livesession.tracker_livesession.trainer_scheduled = True
        livesession.tracker_livesession.save()

        zoom = ZoomClient()
        zoom_response = zoom.create_meeting(livesession.name, duration, start_time+':00Z')
        # livesession.zoom_response = zoom_response
        # livesession.save()

        livesession.tracker_livesession.zoom_response = zoom_response
        livesession.tracker_livesession.save()

        notification.read = True
        notification.save()

        # print(zoom_response)
        return JsonResponse({'status': True, 'data': []}, safe=False)
    else:
        return HttpResponseNotAllowed(['POST'])

@login_required
def training_activate_view(request, training_id=None):
    training = models.Training.objects.get(pk=training_id)
    if training.active == True:
        training.active = False
    else:
        training.active = True
    training.save()

    # return JsonResponse({'status': True, 'data': model_to_dict(training)}, safe=False)
    return HttpResponseRedirect(reverse('training_list')) #, args=[str(post['booking_id'])]

@login_required
def training_information_view(request, training_id=None):
    if request.method == 'POST':
        training = models.Training.objects.get(pk=training_id)

        return render(request, 'training_information.html', { "training": training })

        #return JsonResponse({'status': True, 'data': html}, safe=False)
    else:
        return JsonResponse({'status': False, 'data': []}, safe=False)




# def training_delivery_action_view(request, training_id=None, action='prev'):
#     training = models.Training.objects.get(pk=training_id)
#     tracker = models.Tracker.objects.get(user=request.user, training=training)
#     tracker.active_node

def get_current_item(booking=None, request=None):
    tracker = booking.tracker
    #tracker = models.Tracker.objects.get(booking=booking)
    extra = None
    if tracker.active_node.type == 'content':
        current_item = models.Content.objects.get(pk=tracker.active_node.ref_id)
        extra = request.build_absolute_uri(current_item.file.url) 
    elif tracker.active_node.type == 'assignment':
        current_item = models.Assignment.objects.get(pk=tracker.active_node.ref_id)
    elif tracker.active_node.type == 'livesession':
        current_item = models.Session.objects.get(pk=tracker.active_node.ref_id)
    
    return { "node": tracker.active_node, "item": current_item, "abs_url": extra }

def get_training_state(booking=None, user=None):
    training = booking.training
    # training = models.Training.objects.get(pk=training.id)
    modules = training.modules.all()

    try:
        tracker = models.Tracker.objects.get(booking=booking)
    except (models.Tracker.DoesNotExist):
        tracker = models.Tracker.objects.create(booking=booking, started=True)

    return get_current_training_structure(booking, tracker)

    if tracker.active_node is None:
        """Not yet started any modules or lessons"""
        return traverse_tracker_node(modules, tracker)
        
    else: 
        """Already started a module or lesson"""
        return traverse_tracker_node(modules, tracker)

def get_training_first_content(training=None):

    def traverse_node(node=None):
        if node.children.all().exists():
            # children = list()
            for child in node.children.all():
                if child.type == 'content':
                    return child
                # if child.type == 'session':
                #     session = models.Session.objects.get(pk=child.ref_id)
                #     if not session.contents.all().exists():
                #         continue
                #     else:
                #         return session.contents.all().first()
                else:
                    # children.append(traverse_node(child)) 
                    value = traverse_node(child)
                    if value:
                        return value

            # tree['children'] = children
        return None

    json_data = list()
    for module in training.modules.all():
        node = traverse_node(module)
        if not node is None:
            return node


def get_current_training_structure(booking, tracker):
    training = booking.training
    modules = training.modules.all()
    
    if tracker.active_node is None:
        # first_content_node = get_training_node(modules, 'content', 1)
        first_content_node = get_training_first_content(training)
        tracker.active_node = first_content_node
        tracker.save()
    else:
        pass

    def construct_tree_node(node):
        tree = model_to_dict(node, fields=['text', 'type', 'order', 'active', 'ref_id', 'id', 'status']) #
        
        # active_node = models.Node.objects.get(pk=tracker.active_node)
        parent_ids = tracker.active_node.ancestors(include_self=True).values_list('id', flat=True)

        if node.pk in parent_ids:
            if node.pk == tracker.active_node.pk:
                tree['state'] = { 'opened': True, 'selected' : True } #'disabled' : False, 
            else:
                tree['state'] = { 'opened' : True } # 'disabled' : False
        else:
            tree['state'] = { 'opened': False } # 'disabled' : True,
            
        
        if node.children.all().exists():
            children = list()
            for child in node.children.all():
                # if child.type == 'content' and child.pk != tracker.active_node.pk:
                #     continue
                # else:
                children.append(construct_tree_node(child)) 

            tree['children'] = children

        return tree

    json_data = list()
    for module in modules:
        json_data.append(construct_tree_node(module))

    return json_data


def find_first_session_node(modules):
    node = get_training_node(modules, 'content', 4)
    return node
    return traverse_node(modules[0])

count = 0
def get_training_node(nodes=None, node_type=None, order=1):
    
    def get_node(node=None):
        global count
        if node.children.all().exists():
            # children = list()
            for child in node.children.all():
                if child.type == node_type:
                    count += 1
                    if count != order:
                        continue
                    else:
                        count = 0
                        return child
                else:
                    # children.append(traverse_node(child)) 
                    value = get_node(child)
                    if value:
                        return value

            # tree['children'] = children
        return None

    if hasattr(nodes, '__iter__'):
        for node in nodes:
            fnode = get_node(node)
            if fnode is None:
                continue
            else:
                return fnode
    else:
        fnode = get_node(nodes)
        return fnode

def traverse_node(node=None):
    if node.children.all().exists():
        # children = list()
        for child in node.children.all():
            if child.type == 'session':
                session = models.Session.objects.get(pk=child.ref_id)
                if not session.contents.all().exists():
                    continue
                else:
                    return child
            elif child.type == 'assignment':
                return child
            elif child.type == 'livesession':
                return child
            else:
                # children.append(traverse_node(child)) 
                value = traverse_node(child)
                if value:
                    return value

        # tree['children'] = children
    return None


def traverse_tracker_node(modules, tracker):
    if tracker.active_node is None:
        first_session_node = find_first_session_node(modules)
        tracker.active_node = first_session_node
        tracker.save()
        # start_first_session(first_session)
    else:
        # node_status = json.dumps(tracker.node_status)
        pass

    def traverse_tree_node(node):
        tree = model_to_dict(node, fields=['text', 'type', 'order', 'active', 'ref_id', 'id', 'status']) #
        
        # active_node = models.Node.objects.get(pk=tracker.active_node)
        parent_ids = tracker.active_node.ancestors(include_self=True).values_list('id', flat=True)

        if node.pk in parent_ids:
            if node.pk == tracker.active_node.pk:
                tree['state'] = {  'disabled' : False, 'selected' : True, 'opened': True }
            else:
                tree['state'] = { 'disabled' : False }
        else:
            tree['state'] = { 'disabled' : True, 'closed': True }
            
        
        if node.children.all().exists():
            children = list()
            for child in node.children.all():
                # if child.type == 'content' and child.pk != tracker.active_node.pk:
                #     continue
                # else:
                children.append(traverse_tree_node(child)) 

            tree['children'] = children

        return tree

    json_data = list()
    for module in modules:
        json_data.append(traverse_tree_node(module))

    return json_data

@login_required
def training_view(request, training_id=None):
    training = models.Training.objects.get(pk=training_id)

    return render(request, "training_booking_view.html", { 'training': training })

class TrainingDetailView(DetailView):
    model = models.Training
    template_name = 'training_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["now"] = timezone.now()
        return context

class TrainingListView(ListView):
    paginate_by = 5
    model = models.Training
    template_name = 'training_list.html'

# class TrainingInline():
    # form_class = forms.TrainingForm
    # model = models.Training
    # template_name = "training_create_or_update.html"

    # def form_valid(self, form):
    #     named_formsets = self.get_named_formsets()
    #     if not all((x.is_valid() for x in named_formsets.values())):
    #         return self.render_to_response(self.get_context_data(form=form))

    #     self.object = form.save()

    #     # for every formset, attempt to find a specific formset save function
    #     # otherwise, just save.
    #     for name, formset in named_formsets.items():
    #         formset_save_func = getattr(self, 'formset_{0}_valid'.format(name), None)
    #         if formset_save_func is not None:
    #             formset_save_func(formset)
    #         else:
    #             formset.save()
    #     return redirect('products:list_products')

    # def formset_contents_valid(self, formset):
    #     """
    #     Hook for custom formset saving.Useful if you have multiple formsets
    #     """
    #     contents = formset.save(commit=False)  # self.save_formset(formset, contact)
    #     # add this 2 lines, if you have can_delete=True parameter 
    #     # set in inlineformset_factory func
    #     for obj in formset.deleted_objects:
    #         obj.delete()
    #     for content in contents:
    #         content.training = self.object
    #         content.save()

    # def formset_assignments_valid(self, formset):
    #     """
    #     Hook for custom formset saving. Useful if you have multiple formsets
    #     """
    #     assignments = formset.save(commit=False)  # self.save_formset(formset, contact)
    #     # add this 2 lines, if you have can_delete=True parameter 
    #     # set in inlineformset_factory func
    #     for obj in formset.deleted_objects:
    #         obj.delete()
    #     for assignment in assignments:
    #         assignment.training = self.object
    #         assignment.save()

    # def formset_links_valid(self, formset):
    #     """
    #     Hook for custom formset saving. Useful if you have multiple formsets
    #     """
    #     links = formset.save(commit=False)  # self.save_formset(formset, contact)
    #     # add this 2 lines, if you have can_delete=True parameter 
    #     # set in inlineformset_factory func
    #     for obj in formset.deleted_objects:
    #         obj.delete()
    #     for link in links:
    #         link.assignment = self.object
    #         link.save()

@login_required
def training_edit(request, training_id):
    try:
        training = models.Training.objects.get(pk=training_id)
    except (models.Training.DoesNotExist):
        training = None
        
    if request.method == 'POST':
        training_form = forms.TrainingForm(request.POST, request.FILES, instance=training)

        if training_form.is_valid():
            training = training_form.save()

            return HttpResponseRedirect(reverse('training_list')) #, args=[str(booking.id)]

            # senddata = serializers.serialize('json', [training])
            # response = JsonResponse({'status': True, 'obj': senddata}, safe=False)
            # response.set_cookie('training_id', training.pk)

            # return response
        else:
            return HttpResponseRedirect(reverse('training_edit', args=[str(training_id)])) #

            # # senddata = serializers.serialize('json', [training_form.errors])
            # return JsonResponse({'status': False, 'obj': training_form.errors}, safe=False)
    else:
        # json_data = get_json_tree(training_id)
        training_form = forms.TrainingForm(instance=training)
        
        content_form = forms.TrainingContentForm()
        assignment_form = forms.TrainingAssignmentForm()
        assignment_links_formset = forms.TrainingAssignmentLinkFormset(prefix='assignment_links')
        live_session_form = forms.TrainingLiveSessionForm()

        tab = int(request.GET.get('tab', 1))

        return render(request, "training_edit.html", {
            # 'json_data': json_data,
            'tab': tab,
            "training_id": training_id,

            "training_form": training_form,
            'content_form': content_form,
            'assignment_form': assignment_form,
            'assignment_links_formset': assignment_links_formset,
            
            'live_session_form': live_session_form,
        }) 

@login_required
def training_delete(request, training_id):
    training = models.Training.objects.get(pk=training_id)
    training.delete()

    return HttpResponseRedirect(reverse('training_list')) #, args=[str(booking.id)]

@login_required
def training_create(request):
    if request.method == 'POST':
        training_form = forms.TrainingForm(request.POST, request.FILES)

        if training_form.is_valid():
            training = training_form.save(commit=False)
            training.created_by = request.user
            training.save()

            messages.success(request, "Training information saved Successfully.")
            
            return HttpResponseRedirect(reverse('training_edit', args=[str(training.id)]))
        else:
            for field, error in training_form.errors.items():
                messages.error(request, f"Field '{field}' having error : {error}.")

            return HttpResponseRedirect(reverse('training_add'))
            # senddata = serializers.serialize('json', [training_form.errors])
            # return JsonResponse({'status': False, 'obj': training_form.errors}, safe=False)
    else:
        training_form = forms.TrainingForm()
        tab = int(request.GET.get('tab', 1))

        return render(request, "training_new.html", {
            "training_form": training_form,
            'tab': tab,
        })

@login_required
def training_session_save(request, training_id=None):
    if request.method == "POST":
        training = models.Training.objects.get(pk=training_id)
        formset = forms.TrainingSessionFormset(request.POST or None, request.FILES or None, instance=training, prefix='sessions')

        if formset.is_valid():
            sessions = formset.save(commit=False)

            for obj in formset.deleted_objects:
                obj.delete()

            ids = []
            for session in sessions:
                session.training = training
                session.save()
                ids.append(session.pk)

            # return JsonResponse({'status': True, 'data': ids}, safe=False)
            messages.success(request, "Training Session saved Successfully.")
            return HttpResponseRedirect(reverse("training_add") + "?tab=6")# , args=(year,)
        else:
            # return JsonResponse({'status': False, 'data': []}, safe=False)
            messages.error(request, f"Something went wrong, please fill all fields correctly.")
            return HttpResponseRedirect(reverse("training_add") + "?tab=6")# , args=(year,)

# def training_content_save(request, training_id=None):
    # if request.method == "POST":
    #     training = models.Training.objects.get(pk=training_id)
    #     formset = forms.TrainingContentFormset(request.POST or None, request.FILES or None, instance=training, prefix='contents')

    #     if formset.is_valid():
    #         contents = formset.save(commit=False)

    #         for obj in formset.deleted_objects:
    #             obj.delete()

    #         ids = []
    #         for content in contents:
    #             content.training = training
    #             content.save()
    #             ids.append(content.pk)

    #         # return JsonResponse({'status': True, 'data': ids}, safe=False)
    #         messages.success(request, "Training content saved Successfully.")
    #         return HttpResponseRedirect(reverse("training_add") + "?tab=3")# , args=(year,)
    #     else:
    #         # return JsonResponse({'status': False, 'data': []}, safe=False)
    #         messages.error(request, f"Something went wrong, please fill all fields correctly.")
    #         return HttpResponseRedirect(reverse("training_add") + "?tab=3")# , args=(year,)

@login_required
def training_structure_actions(request, mode=None):
    if request.method == 'POST':
        if mode == 'create':
            return create_structure(request, mode)
        elif mode == 'change':
            return change_structure(request, mode)
        elif mode == 'delete':
            return delete_structure(request, mode)
        elif mode == 'fetch':
            return fetch_structure(request, mode)

@login_required
def create_structure(request, mode=None):
    post            = request.POST
    files           = request.FILES
    data            = post['data']
    data            = json.loads(data)

    node            = data['node']
    node_parent_id  = data['parent']
    node_position   = data['position']
    node_text       = node['text']
    node_type       = node['type']
    
    training_id     = post['training_id']
    training        = models.Training.objects.get(pk=training_id)
    
    node_referenced = None

    if node_type == 'module':
        module_node = models.Node(text=node_text, type=models.Node.MODULE, order=node_position, training=training)
        module_node.save()
        node_created = module_node
    elif node_type == 'lesson':
        node_parent = models.Node.objects.get(pk=node_parent_id)
        lesson_node = models.Node(text=node_text, type=models.Node.LESSON, order=node_position, parent=node_parent)
        lesson_node.save()
        node_created = lesson_node
    elif node_type == 'topic':
        node_parent = models.Node.objects.get(pk=node_parent_id)
        topic_node = models.Node(text=node_text, type=models.Node.TOPIC, order=node_position, parent=node_parent)
        topic_node.save()
        node_created = topic_node
    elif node_type == 'subtopic':
        node_parent = models.Node.objects.get(pk=node_parent_id)
        subtopic_node = models.Node(text=node_text, type=models.Node.SUBTOPIC, order=node_position, parent=node_parent)
        subtopic_node.save()
        node_created = subtopic_node
    elif node_type == 'session':
        node_parent = models.Node.objects.get(pk=node_parent_id)
        session_node = models.Node(text=node_text, type=models.Node.SESSION, order=node_position, parent=node_parent)
        session_node.save()
        node_created = session_node

        session = models.Session(name=node_text, order=node_position, node=session_node, training=training)
        session.save()
        # node_referenced = session
        node_referenced = model_to_dict(session)

        session_node.ref_id = session.pk
        session_node.save()
    elif node_type == 'content':
        node_parent = models.Node.objects.get(pk=node_parent_id)
        content_node = models.Node(text=node_text, type=models.Node.CONTENT, order=node_position, parent=node_parent)
        content_node.save()
        node_created = content_node

        content_file = files['content_file']
        session_id = post['session_id']
        content_type = post['content_type']
        mime, encoding = mimetypes.guess_type(content_file.name)
        content_session = models.Session.objects.get(pk=session_id)
        content = models.Content(name=content_file.name, file=content_file, type=content_type, session=content_session, node=content_node, mime=mime)
        content.save()

        content_name = os.path.basename(content.file.name)
        content.name = content_name
        content.save()
        content_node.text = content_name
        content_node.save()
        # node_referenced = content

        # from django.core import serializers
        # node_referenced = serializers.serialize("json", [node_referenced])
        node_referenced = model_to_dict(content, exclude=['file'])
        node_referenced['file'] = content.file.name

        content_node.ref_id = content.pk
        content_node.save()
    elif node_type == 'assignment':
        node = node['original']

        node_parent = models.Node.objects.get(pk=node_parent_id)
        assignment_node = models.Node(text=node['title'], type=models.Node.ASSIGNMENT, order=node_position, parent=node_parent)
        assignment_node.save()
        node_created = assignment_node

        submit_report = True if ('submit_report' in node and node['submit_report'] == "on") else False 
        mandatory = True if ('mandatory' in node and node['mandatory'] == "on") else False 
        assignment = models.Assignment(title=node['title'], desc=node['desc'], submit_report=submit_report, mandatory=mandatory, node=assignment_node, training=training)
        assignment.save()
        node_referenced = model_to_dict(assignment, exclude=['file'])

        assignment_node.ref_id = assignment.pk
        assignment_node.save()

        # assignment_links_formset = forms.TrainingAssignmentLinkFormset(prefix='assignment_links')
        assignment_links_formset = forms.TrainingAssignmentLinkFormset(node or None, instance=assignment, prefix='assignment_links')
        if assignment_links_formset.is_valid():
            assignment_links_formset.save()
        else:
            pass
    elif node_type == 'livesession':
        node = node['original']

        node_parent = models.Node.objects.get(pk=node_parent_id)
        livesession_node = models.Node(text=node['name'], type=models.Node.LIVESESSION, order=node_position, parent=node_parent)
        livesession_node.save()
        node_created = livesession_node

        # submit_report = True if ('submit_report' in node and node['submit_report'] == "on") else False 
        # mandatory = True if ('mandatory' in node and node['mandatory'] == "on") else False 
        
        # start_time = node['start_time'] if bool(node['start_time']) else None
        # end_time = node['end_time'] if bool(node['end_time']) else None

        # if start_time and end_time:
        #     start_time
        #     zoom = ZoomClient()
        #     zoom.create_meeting(node['name'], node['duration'], start_date, start_time)

        livesession = models.Session(
            name=node['name'],
            objectives=node['objectives'],
            duration=node['duration'],
            duration_type=node['duration_type'],
            #start_time=start_time,
            #end_time=end_time,
            order=node_position, 
            live=True, 
            node=livesession_node, 
            training=training
        )
        livesession.save()
        # node_referenced = session
        node_referenced = model_to_dict(livesession)

        livesession_node.ref_id = livesession.pk
        livesession_node.save()
    elif node_type == 'assessment':
        pass

    node_created = model_to_dict(node_created)
    # node_created = serializers.serialize('json', [ node_created, ])

    return JsonResponse({ 'status': True, 'node_server': node_created, 'node_client': node, 'node_referenced': node_referenced }, safe=False)

@login_required
def change_structure(request, mode=None):
    data            = request.POST['data']
    data            = json.loads(data)

    node_changed = {}
    if 'node' in data:
        node            = data['node']
        new_text        = data['text']
        # old_text        = data['old']

        if node['id'].isnumeric():
            node_server = models.Node.objects.get(pk=node['id'])
            node_server.text = new_text
            node_server.save()
            node_changed = node_server

            if node['type'] == 'session' and node_server.ref_id:
                session_server = models.Session.objects.get(pk=node_server.ref_id)
                session_server.name = new_text
                session_server.save()
            if node['type'] == 'content' and node_server.ref_id:
                content_server = models.Content.objects.get(pk=node_server.ref_id)
                content_server.name = new_text
                content_server.save()
            if node['type'] == 'assignment' and node_server.ref_id:
                assignment_server = models.Assignment.objects.get(pk=node_server.ref_id)
                assignment_server.title = new_text
                assignment_server.save()

            node_changed = model_to_dict(node_changed)
    else:
        # node = data
        if data['type'] == 'assignment':
            assignment_node_id = data['assignment_node_id']

            submit_report = True if ('submit_report' in data and data['submit_report'] == "on") else False 
            mandatory = True if ('mandatory' in data and data['mandatory'] == "on") else False 
            assignment_node = models.Node.objects.get(pk=assignment_node_id)
            assignment = models.Assignment.objects.get(pk=assignment_node.ref_id)
            assignment.title = data['title']
            assignment.desc = data['desc']
            assignment.submit_report = submit_report
            assignment.mandatory = mandatory
            assignment.save()
            node_changed = model_to_dict(assignment, exclude=['file'])

            assignment_node.text = assignment.title
            assignment_node.save()

            # assignment_links_formset = forms.TrainingAssignmentLinkFormset(prefix='assignment_links')
            for link in assignment.links.all():
                link.delete()
                
            assignment_links_formset = forms.TrainingAssignmentLinkFormset(data or None, instance=assignment, prefix='assignment_links')
            if assignment_links_formset.is_valid():
                assignment_links_formset.save()
            else:
                pass
        elif data['type'] == 'livesession':
            live_session_node_id = data['live_session_node_id']
            live_session_node = models.Node.objects.get(pk=live_session_node_id)
            live_session = models.Session.objects.get(pk=live_session_node.ref_id)

            live_session_form = forms.TrainingLiveSessionForm(data, instance=live_session)
            if live_session_form.is_valid():
                live_session = live_session_form.save()

                live_session_node.text = live_session.name
                live_session_node.save()

                node_changed = model_to_dict(live_session)

    return JsonResponse({ 'status': True, 'node_changed': node_changed }, safe=False)

@login_required
def delete_structure(request, mode=None):
    data            = request.POST['data']
    data            = json.loads(data)

    node            = data['node']
    parent_id       = data['parent']

    node_server = models.Node.objects.get(pk=node['id'])
    node_deleted = node_server

    # if node['type'] == 'assignment' and node_server.ref_id:
    #     session_server = models.Session.objects.get(pk=node_server.ref_id)
    #     # session_server.name = new_text
    #     session_server.delete()
    # if node['type'] == 'content' and node_server.ref_id:
    #     content_server = models.Content.objects.get(pk=node_server.ref_id)
    #     content_server.delete()
    
    node_server.delete()

    node_deleted = model_to_dict(node_deleted)
    return JsonResponse({ 'status': True, 'node_deleted': node_deleted }, safe=False)

@login_required
def fetch_structure(request, mode=None):
    if request.method == 'POST':
        node_id = request.POST['node_id']
        node = models.Node.objects.get(pk=node_id)
        
        if node.type == 'assignment':
            assignment = models.Assignment.objects.get(pk=node.ref_id)
            
            assignment_dict = model_to_dict(assignment, exclude=['file'])
            links = assignment.links.all()
            link_list = []
            for link in links:
                link_list.append(model_to_dict(link))

            assignment_dict['links'] = link_list
            output = assignment_dict
        if node.type == 'livesession':
            session = models.Session.objects.get(pk=node.ref_id)
            
            session_dict = model_to_dict(session) #, exclude=['file']
            # links = session.links.all()
            # link_list = []
            # for link in links:
            #     link_list.append(model_to_dict(link))
            # session_dict['links'] = link_list

            output = session_dict
        if node.type == 'content':
            content = models.Content.objects.get(pk=node.ref_id)

        return JsonResponse({ 'status': True, 'data': output }, safe=False)

@login_required
def training_structure_json(request):
    training_id = request.GET.get('training_id', None)
    mode = request.GET.get('mode', 'training')

    if training_id is not None:
        json_data = get_json_tree(training_id, mode)
    else:
        json_data = []

    return JsonResponse(json_data, safe=False)

# def training_structure_save(request, training_id=None):
    # if request.method == 'POST':
    #     # check for existing data, if there then delete all
    #     training = models.Training.objects.get(pk=training_id)

    #     sessions = training.sessions.all()
    #     for session in sessions:
    #         session.delete()

    #     # nodes = models.Node.objects.with_tree_fields()
    #     # nodes = models.Node.objects.with_tree_fields().all()
    #     nodes = models.Node.objects.with_tree_fields().training_structure(training)

    #     for node in nodes:
    #         node.delete()

    #     data = json.loads(request.body)
    #     items = data['json_data']

    #     create_tree_item(items, training_id)

    #     context = {}
    #     context['status'] = True

    #     json_data = get_json_tree(training_id)
    #     context['json_data'] = json_data
        
    #     return JsonResponse(context, safe=False)

# def create_tree_item(items, parent_id=None):

#     for item in items:
#         training = models.Training.objects.get(pk=parent_id)
#         type =  item['type']
#         # TYPE = type.upper()
#         if type == 'module':
#             module = models.Node(name=item['text'], type=models.Node.MODULE, training=training)
#             module.save()
#             # child_parent_id = module.id
#         elif type == 'lesson':
#             # module = models.Module.objects.get(pk=parent_id)
#             lesson = models.Lesson(name=item['text'], type=models.Node.LESSON, training=training)
#             lesson.save()
#             # child_parent_id = lesson.id
#         elif type == 'topic':
#             # lesson = models.Lesson.objects.get(pk=parent_id)
#             topic = models.Topic(name=item['text'], type=models.Node.TOPIC, training=training)
#             topic.save()
#             # child_parent_id = topic.id
#         elif type == 'subtopic':
#             # topic = models.Topic.objects.get(pk=parent_id)
#             subtopic = models.SubTopic(name=item['text'], type=models.Node.SUBTOPIC, training=training)
#             subtopic.save()
#             # child_parent_id = subtopic.id
            
#         if len(item['children']) > 0:
#             create_tree_item(item['children'], child_parent_id)

training_id = None
def create_tree_item(items, parent_id=None):
    global training_id
    if training_id is None:
        training_id = parent_id
    training = models.Training.objects.get(pk=training_id)

    for index, item in enumerate(items):
        type =  item['type']
        if type == 'module':
            module = models.Node(text=item['text'], type=models.Node.MODULE, order=index, training=training)
            module.save()
            child_parent_id = module.id
        elif type == 'lesson':
            node = models.Node.objects.get(pk=parent_id)
            lesson = models.Node(text=item['text'], type=models.Node.LESSON, order=index, parent=node)
            lesson.save()
            child_parent_id = lesson.id
        elif type == 'topic':
            node = models.Node.objects.get(pk=parent_id)
            topic = models.Node(text=item['text'], type=models.Node.TOPIC, order=index, parent=node)
            topic.save()
            child_parent_id = topic.id
        elif type == 'subtopic':
            node = models.Node.objects.get(pk=parent_id)
            subtopic = models.Node(text=item['text'], type=models.Node.SUBTOPIC, order=index, parent=node)
            subtopic.save()
            child_parent_id = subtopic.id
        elif type == 'session':
            node = models.Node.objects.get(pk=parent_id)
            session_node = models.Node(text=item['text'], type=models.Node.SESSION, order=index, parent=node)
            session_node.save()
            child_parent_id = session_node.id

            session = models.Session(name=item['text'], order=index, node=node, training=training)
            session.save()

            session_node.ref_id = session.pk
            session_node.save()
        elif type == 'content':
            node = models.Node.objects.get(pk=parent_id)
            content_node = models.Node(text=item['text'], type=models.Node.CONTENT, order=index, parent=node)
            concontent_nodetent.save()
            child_parent_id = content_node.id

            # content = models.Content(name=item['text'], order=index, node=node, training=training)
            # content.save()

            # content_node.ref_id = content.pk
            # contentn_node.save()
        elif type == 'assignment':
            node = models.Node.objects.get(pk=parent_id)
            assignment = models.Node(text=item['text'], type=models.Node.ASSIGNMENT, order=index, parent=node)
            assignment.save()
            child_parent_id = assignment.id
        elif type == 'assessment':
            pass
            
        if len(item['children']) > 0:
            create_tree_item(item['children'], child_parent_id)

def get_json_tree(training_id=None, mode=None):
    json = []
    if (training_id == None):
        return json

    try:
        training = models.Training.objects.get(pk=training_id)
    except (models.Training.DoesNotExist):
        return json

    nodes = models.Node.objects.with_tree_fields().training_structure(training)
    count = nodes.count()

    def get_tree(node):
        # ancestors = node.ancestors(include_self=True)
        tree = model_to_dict(node, fields=['text', 'type', 'order', 'active', 'ref_id', 'id', 'status']) #
        
        if mode == 'delivery':

            tree['state'] = { 'disabled' : True }
        else:
            tree['state'] = { 'opened' : True }

        if node.children.all().exists():
            children = list()
            for child in node.children.all():
                if ((mode == 'booking' or mode == 'delivery') and child.type == 'content'):
                    continue
                else:
                    children.append(get_tree(child)) 
            tree['children'] = children

        return tree

    json = []
    for node in nodes:
        json.append(get_tree(node))


                # for j, lesson in enumerate(module.children.all()):
                    # lesson_obj = {
                    #     'id': 'lesson-' + str(lesson.id),
                    #     'text': lesson.name,
                    #     'type': lesson.__class__.__name__.lower(),
                    #     'icon': 'fa fa-clipboard-list',
                    #     'children': [],
                    #     'state' : { 'opened' : True },
                    # }
                    # json[i]['children'].insert(j, lesson_obj)
                    # if lesson.children.count() > 0:
                    #     for k, topic in enumerate(lesson.children.all()):
                    #         topic_obj = {
                    #             'id': 'topic-' + str(topic.id),
                    #             'text': topic.name,
                    #             'type': topic.__class__.__name__.lower(),
                    #             'icon': 'fa fa-list-check',
                    #             'children': [],
                    #             'state' : { 'opened' : True },
                    #         }
                    #         json[i]['children'][j]['children'].insert(k, topic_obj)
                    #         if topic.children.count() > 0:
                    #             for l, subtopic in enumerate(topic.children.all()):
                    #                 subtopic_obj = {
                    #                     'id': 'subtopic-' + str(subtopic.id),
                    #                     'text': subtopic.name,
                    #                     'type': subtopic.__class__.__name__.lower(),
                    #                     'icon': 'fa fa-list',
                    #                     'state' : { 'opened' : True },
                    #                 }
                    #                 json[i]['children'][j]['children'][k]['children'].insert(l, subtopic_obj)
    return json

@login_required
def training_assignment_save(request, training_id=None):
    if request.method == "POST":
        training = models.Training.objects.get(pk=training_id)
        formset = forms.TrainingAssignmentFormset(request.POST or None, request.FILES or None, instance=training, prefix='assignments')

        if formset.is_valid():
            assignments = formset.save(commit=False)

            for obj in formset.deleted_objects:
                obj.delete()

            # ids = []
            for assignment in assignments:
                assignment.training = training
                assignment.save()
                # ids.append(assignment.pk)

            # return JsonResponse({'status': True, 'data': ids}, safe=False)
            messages.success(request, "Training Assignment saved Successfully.")
            return HttpResponseRedirect(reverse("training_add") + "?tab=4")# , args=(year,)
        else:
            # return JsonResponse({'status': False, 'data': []}, safe=False)
            messages.error(request, f"Something went wrong, please fill all fields correctly.")
            return HttpResponseRedirect(reverse("training_add") + "?tab=4")# , args=(year,)

@login_required
def training_assignment_links_save(request, assignment_id):
    if request.method == "POST":
        assignment = models.Assignment.objects.get(pk=assignment_id)
        formset = forms.TrainingAssignmentLinkFormset(request.POST or None, request.FILES or None, instance=assignment,  prefix='links')

        if formset.is_valid():
            links = formset.save(commit=False)

            for obj in formset.deleted_objects:
                obj.delete()

            ids = []
            for link in links:
                link.assignment = assignment
                link.save()
                ids.append(link.pk)

            return JsonResponse({'status': True, 'data': ids}, safe=False)
            # messages.success(request, "Training Assignment links saved Successfully.")
            # return HttpResponseRedirect(reverse("training_add") + "?tab=4")# , args=(year,)
        else:
            return JsonResponse({'status': False, 'data': []}, safe=False)
            # messages.error(request, f"Something went wrong, please fill all fields correctly.")
            # return HttpResponseRedirect(reverse("training_add") + "?tab=4")# , args=(year,)

#------------------------
# def training_content_save(request):
    # if request.method == "POST":
    #     form = forms.TrainingContentForm(request.POST or None, request.FILES or None)
    #     if form.is_valid():
    #         content = form.save(commit=False)

    #         session = models.Session.objects.get(pk=request.POST.get('session'))
    #         # content.session = session
    #         content.save()

    #     # session_id = request.POST.get('session_id')
    #     # session = models.Session.objects.get(pk=session_id)
    #     # formset = forms.TrainingContentFormset(request.POST or None, request.FILES or None, instance=session, prefix='contents')

    #     # if formset.is_valid():
    #     #     contents = formset.save(commit=False)

    #     #     for obj in formset.deleted_objects:
    #     #         obj.delete()

    #     #     # ids = []
    #     #     for content in contents:
    #     #         content.session = session
    #     #         content.save()
    #     #         # ids.append(content.pk)

    #         # return JsonResponse({'status': True, 'data': ids}, safe=False)
    #         messages.success(request, "Training content saved Successfully.")
    #         return HttpResponseRedirect(reverse("training_add") + "?tab=2")# , args=(year,)
    #     else:
    #         # return JsonResponse({'status': False, 'data': []}, safe=False)
    #         messages.error(request, f"Something went wrong, please fill all fields correctly.")
    #         return HttpResponseRedirect(reverse("training_add") + "?tab=2")# , args=(year,)

# def training_content_save(request, training_id=None):
    # author = Author.objects.get(pk=author_id)
    # BookInlineFormSet = inlineformset_factory(Author, Book, fields=["title"])
    # if request.method == "POST":
    #     formset = BookInlineFormSet(request.POST, request.FILES, instance=author)
    #     if formset.is_valid():
    #         formset.save()
    #         # Do something. Should generally end with a redirect. For example:
    #         return HttpResponseRedirect(author.get_absolute_url())
    # else:
    #     formset = BookInlineFormSet(instance=author)
    # return render(request, "manage_books.html", {"formset": formset})

# def training_structure(request, parent_id, type=None, name=None):
    # if request.method == 'POST':
    #     if type == 'module':
    #         training = models.Training.objects.get(pk=parent_id)
    #         created = models.Module(name=name, parent=training)
    #     elif type == 'lesson':
    #         module = models.Module.objects.get(pk=parent_id)
    #         created = models.Lesson(name=name, parent=module)
    #     elif type == 'topic':
    #         lesson = models.Lesson.objects.get(pk=parent_id)
    #         created = models.Topic(name=name, parent=lesson)
    #     elif type == 'subtopic':
    #         topic = models.Topic.objects.get(pk=parent_id)
    #         created = models.SubTopic(name=name, parent=topic)
    #     else:
    #         created = None

    #     senddata = serializers.serialize('json', [created])
    #     return JsonResponse({'status': True, 'obj': senddata}, safe=False)
    # else:
    #     training = models.Training.objects.get(pk=training_id)

    #     senddata = serializers.serialize('json', [training])
    #     return JsonResponse({'status': True, 'obj': senddata}, safe=False)

# class TrainingUpdate(TrainingInline, UpdateView):

    # def get_context_data(self, **kwargs):
    #     ctx = super(TrainingUpdate, self).get_context_data(**kwargs)
    #     ctx['named_formsets'] = self.get_named_formsets()
    #     return ctx

    # def get_named_formsets(self):
    #     return {
    #         'variants': VariantFormSet(self.request.POST or None, self.request.FILES or None, instance=self.object, prefix='variants'),
    #         'images': ImageFormSet(self.request.POST or None, self.request.FILES or None, instance=self.object, prefix='images'),
    #     }

# class TrainingAddView(CreateView):
    # model = models.Training
    # # form_class = forms.TrainingAddForm

    # template_name = 'training_add.html'
    # fields = '__all__' #['name', 'module', 'desc', 'duration', 'frequency', 'link', 'category', 'amount'] 

    # def get(self, request, *args, **kwargs):
    #     # SessionFormSet = modelformset_factory(models.Session, fields=["name"])
    #     # formset = SessionFormSet() #instance=session
    #     session = models.Session.objects.get(pk=1)

    #     TrainingInlineFormSet = inlineformset_factory(models.Session, models.Training, fields=('title',))
    #     formset = TrainingInlineFormSet(instance=session)
    #     return render(request, "training_setup.html", {"formset": formset})

    # def post(self, request, *args, **kwargs):
    #     TrainingInlineFormSet = inlineformset_factory(models.Session, models.Training, fields=["title"])
    #     formset = TrainingInlineFormSet(request.POST, request.FILES) #, instance=author
    #     if formset.is_valid():
    #         formset.save()
    #         # Do something. Should generally end with a redirect. For example:
    #         return HttpResponseRedirect(reverse('training_list')) #training.get_absolute_url()
    #     return render(request, "training_setup.html", {"formset": formset})
    #     # author = Author.objects.get(pk=author_id)
    #     # BookInlineFormSet = inlineformset_factory(Author, Book, fields=["title"])
    #     # if request.method == "POST":
    #     #     formset = BookInlineFormSet(request.POST, request.FILES, instance=author)
    #     #     if formset.is_valid():
    #     #         formset.save()
    #     #         # Do something. Should generally end with a redirect. For example:
    #     #         return HttpResponseRedirect(author.get_absolute_url())
    #     # else:
    #     #     formset = BookInlineFormSet(instance=author)
    #     # return render(request, "manage_books.html", {"formset": formset})

    # def get_success_url(self):
    #     return reverse('training_list')
    
    # def get_context_data(self, **kwargs):
    #     data = super(ProfileFamilyMemberCreate, self).get_context_data(**kwargs)
    #     if self.request.POST:
    #         data['familymembers'] = FamilyMemberFormSet(self.request.POST)
    #     else:
    #         data['familymembers'] = FamilyMemberFormSet()
    #     return data

    # def form_valid(self, form):
    #     context = self.get_context_data()
    #     familymembers = context['familymembers']
    #     with transaction.atomic():
    #         self.object = form.save()

    #         if familymembers.is_valid():
    #             familymembers.instance = self.object
    #             familymembers.save()
    #     return super(ProfileFamilyMemberCreate, self).form_valid(form)

# class TrainingEditView(UpdateView):
    # model = models.Training
    # template_name = 'training_edit.html'
    # fields = ['name', 'module', 'desc', 'duration', 'frequency', 'link', 'category', 'amount']

    # success_url = reverse_lazy("training_list")
    # # def get_success_url(self):
    # #     return reverse('training_list')

# class TrainingDeleteView(DeleteView):
    # model = models.Training
    # template_name = 'training_delete.html'
    # success_url = reverse_lazy("training_list")






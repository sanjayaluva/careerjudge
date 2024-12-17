from django.shortcuts import render
from . import forms
from django.contrib import messages
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView
from . import models
from django.urls import reverse

from django.contrib.auth import get_user_model
User = get_user_model()

from django.http import JsonResponse, HttpResponseRedirect
import datetime

from django.conf import settings
from cjapp.payment import RzpClient

from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.templatetags.static import static

# Create your views here.
class CounsellingBookingListView(ListView):
    paginate_by = 5
    model = models.Booking
    template_name = 'booking_list.html'

    # def get_context_data(self, **kwargs):
    #     # Call the base implementation first to get a context
    #     context = super().get_context_data(**kwargs)
    #     # Add in a QuerySet of all the books
    #     context["timeslots"] = models.TIME_SLOTS
    #     return context

@csrf_exempt
def counselling_booking_payment_submit_view(request):
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

            messages.success(request, "Counselling booked Successfully.")
        else:
            # except razorpay.errors.SignatureVerificationError as e:
            # Payment signature verification failed
            # Handle the error accordingly
            # return render(request, 'payment_failure.html')
            messages.success(request, "Counselling booking Failed.")

        return HttpResponseRedirect(reverse('counselling_booking_list'))
        
def counselling_booking_payment_view(request, bookid=None):
    # form = forms.BookingForm(user=request.user)
    booking = models.Booking.objects.get(pk=bookid)
    amount = int(booking.counsellor.rate) * 100
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
        "redirect_url": request.build_absolute_uri(reverse('counselling_booking_payment_submit'))
    }
        
    return render(request, "payment.html", context)

def counselling_booking_add_view(request):
    if request.method == "POST":
        form = forms.BookingForm(request.POST, user=request.user)

        if form.is_valid():
            booking = form.save()

            return HttpResponseRedirect(reverse('counselling_booking_payment', args=[str(booking.id)]))
        else:
            messages.error(
                request, f"Somthing is not correct, please fill all fields correctly."
            )
    else:
        form = forms.BookingForm(user=request.user)

    return render(request, "booking.html", {"form": form, "user": request.user})

def counselling_booking_cancel_view(request, pk):
    if request.method == 'POST':
        form = forms.CounsellingCancelForm(request.POST)
        if form.is_valid():
            booking = models.Booking.objects.get(pk=pk)
            booking.status = models.Booking.STATUS_CANCELLED
            booking.reason = form.cleaned_data['reason']
            booking.save()

            messages.success(request, "Counselling booking cancelled Successfully.")
        else:
            messages.success(request, "Something went wrong.")
        
        return HttpResponseRedirect(reverse('counselling_booking_list')) #, args=[str(booking.id)]
    else:
        form = forms.CounsellingCancelForm()
        
    return render(request, "booking_cancel.html", {"title":"Counselling Booking Cancellation", "form": form, "user": request.user})

class CounsellingCategoryListView(ListView):
    paginate_by = 5
    model = models.Category
    template_name = 'category_list.html'
    
class CounsellingCategoryAddView(CreateView):
    model = models.Category
    fields = ['name']  
    template_name = 'category_add.html'

    def get_success_url(self):
        return reverse('counselling_category_list')

class CounsellingCategoryEditView(UpdateView):
    model = models.Category
    fields = ['name']
    template_name = 'category_edit.html'

    def get_success_url(self):
        return reverse('counselling_category_list')

def get_counsellors_by_category(request, pk):
    counsellors = list(User.objects.filter(category=pk).values())
    return JsonResponse(counsellors, safe=False)

def counselling_timeslots_view(request, counsellor):
    upcoming_dates = datetime.datetime.today()
    avail = list(models.Availability.objects.filter(counsellor=counsellor, date__gte=upcoming_dates).values())
    return JsonResponse(avail, safe=False)

def counselling_availability_view(request, date=None):
    if (date):
        avail = models.Availability.objects.filter(counsellor=request.user, date=date).first()
        if (avail):
            if (request.method == "POST"):
                form = forms.AvailabilityForm(request.POST, instance=avail, user=request.user)
            else:
                form = forms.AvailabilityForm(instance=avail, user=request.user)
        else:
            if (request.method == "POST"):
                form = forms.AvailabilityForm(request.POST, user=request.user)
            else:
                form = forms.AvailabilityForm(user=request.user, initial={'date': date})
    else:
        form = forms.AvailabilityForm(user=request.user)
    
    if request.method == "POST":
        if form.is_valid():
            availability = form.save()
                
            messages.success(request, "Counselling Availability timeslot successfully saved.")
            return HttpResponseRedirect(reverse('counselling_availability_date', args=[availability.date]))
        else:
            # pass
            # for error in form.errors:
            messages.error(
                request, f"Somthing is not correct, please fill all fields correctly."
            )
    # else:
        # form = forms.AvailabilityForm(user=request.user)
    
    return render(request, "availability.html", {"form": form})

# def counselling_availability_load_view(request, date):
#     user = request.user
#     availability = list(models.Availability.objects.filter(counsellor=user, date=date).values())
#     # print(availability)
#     return JsonResponse(availability, safe=False)
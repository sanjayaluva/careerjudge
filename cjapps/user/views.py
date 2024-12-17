
from django.contrib.auth import authenticate, get_user_model, login

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import EmailMessage
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings

from django.contrib.auth.forms import PasswordChangeForm
from user import forms

from django_filters.views import FilterView
from .filters import UserFilter

from django.views.generic.list import ListView
from django.views.generic.edit import FormView

from django.contrib.auth.models import Group

from .resources import UserResource
from tablib import Dataset

# so we can reference the user model as User instead of CustomUser
User = get_user_model()

def signup_view(request):
    if request.method == "POST":
        next = request.GET.get('next')
        form = forms.UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            user.set_password(password)
            user.save()
            new_user = authenticate(email=user.email, password=password)
            login(request, new_user)
            if next:
                return redirect(next)
            else:
                return redirect('verify-email')
    else:
        form = forms.UserRegisterForm()
    
    return render(request, 'user/signup.html', {
        'form': form
    })

# send email with verification link
def verify_email(request):
    if request.method == "POST":
        if request.user.email_is_verified != True:
            current_site = get_current_site(request)
            user = request.user
            email = request.user.email
            subject = "Verify Email"
            message = render_to_string('user/verify_email_message.html', {
                'request': request,
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            email = EmailMessage(
                subject, message, to=[email]
            )
            email.content_subtype = 'html'
            email.send()
            return redirect('verify-email-done')
        else:
            return redirect('signup')
    return render(request, 'user/verify_email.html')

def verify_email_done(request):
    return render(request, 'user/verify_email_done.html')

def verify_email_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.email_is_verified = True
        user.is_active = True
        user.save()
        messages.success(request, 'Your email has been verified.')
        return redirect('verify-email-complete')   
    else:
        messages.warning(request, 'The link is invalid.')
    return render(request, 'user/verify_email_confirm.html')

def verify_email_complete(request):
    return render(request, 'user/verify_email_complete.html')


def homepage_view(request):
    return render(request, "core/index.html") #, {"form": form}

def register_view(request):
    if request.method == "POST":
        form = forms.UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # form = forms.UserRegisterForm()

            role = User.ROLES[user.role]
            group = Group.objects.get(name=role)
            user.groups.add(group)

            # if request.user.email_is_verified != True:
            current_site = get_current_site(request)
            # user = request.user
            email = user.email
            subject = "Verify Email"
            message = render_to_string('user/verify_email_message.html', {
                'request': request,
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
                'email':user.email,
                'password':form.cleaned_data.get("password1"), 
            })
            email = EmailMessage(
                subject, message, to=[email]
            )
            email.content_subtype = 'html'
            email.send()
            # return redirect('verify-email-done')
            # else:
                # return redirect('signup')
                
            messages.success(request, f"User Account created successfuly, An email has been sent with instructions to verify your email.")
            return HttpResponseRedirect(reverse('register'))
        else:
            pass
            # for error in form.errors:
            # messages.error(
            #     request, f"Somthing is not correct, please fill all fields correctly."
            # )
    else:
        form = forms.UserRegisterForm()
    return render(request, "user/register.html", {"form": form})

# @admin_required
@login_required
def dashboard_view(request):
    # logs = ActivityLog.objects.all().order_by("-created_at")[:10]
    # gender_count = Student.get_gender_count()
    context = {
        # "student_count": User.objects.get_student_count(),
        # "lecturer_count": User.objects.get_lecturer_count(),
        # "superuser_count": User.objects.get_superuser_count(),
        # "males_count": gender_count["M"],
        # "females_count": gender_count["F"],
        # "logs": logs,
    }
    return render(request, "core/dashboard.html", context)

@login_required
def profile_view(request):
    """Show profile of any user that fire out the request"""
    # if request.user.is_individual:
    return render(
        request,
        "user/profile.html",
        {
            "title": request.user.get_full_name,
            "user": request.user,
        },
    )

@login_required
def profile_edit_view(request):
    if request.method == "POST":
        form = forms.ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = forms.ProfileEditForm(instance=request.user)
    return render(
        request,
        "user/profile_edit.html",
        {
            "title": "Setting",
            "form": form,
            "user": request.user,
        },
    )


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("profile")
        else:
            messages.error(request, "Please correct the error(s) below. ")
    else:
        form = PasswordChangeForm(request.user)
    return render(
        request,
        "setting/password_change.html",
        {
            "form": form,
        },
    )


@method_decorator([login_required], name="dispatch")
class UserListView(ListView):
    model = User
    paginate_by = 10 # if pagination is desired
    template_name = "user/user_list.html"
    # queryset = User.objects.filter(createby=)

    def get_queryset(self):
        if self.request.user.is_cjadmin:
            queryset = User.objects.all()
        else:
            queryset = User.objects.filter(createdby=self.request.user.id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["now"] = 1#timezone.now()
        return context

# class UserListView(FilterView):
#     queryset = User.objects.all()
#     filterset_class = UserFilter
#     # model = User
#     template_name = "user/user_list.html"
#     paginate_by = 10

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["title"] = "Users"
#         return context

@login_required
def user_add_view(request):
    if request.method == "POST":
        form = forms.UserAddForm(request.POST, user=request.user)
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        if form.is_valid():
            user = form.save()

            # reset password again
            generated_password = User.objects.make_random_password()
            user.set_password(generated_password)
            user.createdby = request.user
            user.save()

            # setup user group
            role = User.ROLES[user.role]
            group = Group.objects.get(name=role)
            user.groups.add(group)

            messages.success(
                request,
                "Account for " + first_name + " " + last_name + " has been created. Verification email sent.",
            )

            # send verify email 
            current_site = get_current_site(request)
            btn_caption = 'Verify Email' if not (user.is_psychometrician or user.is_reviewer or user.is_trainer or user.is_counsellor) else 'I Accept'
            group_desc = group.desc if (user.is_psychometrician or user.is_reviewer or user.is_trainer or user.is_counsellor) else None
            # user = request.user
            email = user.email
            subject = "Verify Email"
            message = render_to_string('user/verify_email_message.html', {
                'request': request,
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
                'email':user.email,
                'password':generated_password, 
                'btn_caption': btn_caption,
                'group_desc': group_desc,
            })
            email = EmailMessage(
                subject, message, to=[email]
            )
            email.content_subtype = 'html'
            email.send()

            return redirect("user_list")
        else:
            messages.error(request, "Correct the error(s) below.")
    else:
        form = forms.UserAddForm(user=request.user)

    return render(
        request,
        "user/user_add.html",
        {"title": "Add User", "form": form},
    )


# @admin_required
@login_required
def user_edit_view(request, pk):
    # instance = User.objects.get(pk=pk)
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = forms.UserEditForm(request.POST, request.FILES, instance=user)
        full_name = user.get_full_name
        if form.is_valid():
            form.save()

            messages.success(request, ("User " + full_name + " has been updated."))
            return redirect("profile_single", user.id)
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = forms.UserEditForm(instance=user)
    return render(
        request,
        "user/user_edit.html",
        {
            "title": "Edit Profile",
            "form": form,
            "user": user,
        },
    )

# @admin_required
@login_required
def user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    # full_name = student.user.get_full_name
    user.delete()
    messages.success(request, "User has been deleted.")
    return redirect("user_list")


# @admin_required
@login_required
def profile_single_view(request, id):
    """Show profile of any selected user"""
    
    user = User.objects.get(pk=id)
    
    context = {
        "title": user.get_full_name,
        "user": user,
        # "user_type": "user",
        # "courses": courses,
        # "student": student,
        # "current_session": current_session,
        # "current_semester": current_semester,
    }
    return render(request, "user/profile_single.html", context)


@method_decorator([login_required], name="dispatch")
class GroupListView(ListView):
    model = Group
    paginate_by = 15 # if pagination is desired
    template_name = "user/group_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["now"] = 1#timezone.now()
        return context

@login_required
def group_desc_edit_view(request, pk):
    # instance = User.objects.get(pk=pk)
    group = get_object_or_404(Group, pk=pk)
    if request.method == "POST":
        form = forms.GroupEditForm(request.POST, request.FILES, instance=group)
        full_name = group.name
        if form.is_valid():
            form.save()

            messages.success(request, ("Group desctiption has been updated."))
            return redirect("group_edit", group.id)
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = forms.GroupEditForm(instance=group)
    return render(
        request,
        "user/group_edit.html",
        {
            "title": "Edit Group",
            "form": form,
            "user": request.user,
        },
    )


# @login_required
# def group_edit_view(request, pk):
#     # instance = User.objects.get(pk=pk)
#     group = get_object_or_404(Group, pk=pk)
#     if request.method == "POST":
#         form = GroupEditForm(request.POST, request.FILES, instance=group)
#         full_name = group.name
#         if form.is_valid():
#             form.save()

#             messages.success(request, ("User " + full_name + " has been updated."))
#             return redirect("profile_single", group.id)
#         else:
#             messages.error(request, "Please correct the error below.")
#     else:
#         form = GroupEditForm(instance=group)
#     return render(
#         request,
#         "user/group_edit.html",
#         {
#             "title": "Edit Profile",
#             "form": form,
#             "user": user,
#         },
#     )

# from django.views.generic.edit import CreateView, DeleteView, UpdateView
# class GroupUpdateView(UpdateView):
#     model = Group
#     fields = ["name"]

def user_import_view(request):
    """Show profile of any user that fire out the request"""

    from import_export.forms import ImportForm
    from import_export.forms import ConfirmImportForm

    from import_export.formats import base_formats

    DEFAULT_FORMATS = (
        base_formats.CSV,
        base_formats.XLS,
        base_formats.TSV,
        base_formats.ODS,
        base_formats.JSON,
        base_formats.YAML,
        base_formats.HTML,
    )
    formats = DEFAULT_FORMATS

    result = confirm_form = None
    if request.method == "POST":
        form = ImportForm(formats, request.POST, request.FILES)#, instance=group
        # full_name = group.name
        if form.is_valid():
            # form.save()
            user_resource = UserResource()
            dataset = Dataset()
            new_users = request.FILES['import_file']

            imported_data = dataset.load(new_users.read().decode(), format='csv')#, headers=False
            result = user_resource.import_data(imported_data, dry_run=True)  # Test the data import

            # import os
            if not result.has_errors():
                confirm_form = ConfirmImportForm(initial={
                    'import_file_name': new_users.name, #os.path.basename(uploaded_file.name),
                    'input_format': form.cleaned_data['input_format'],
                })

            # if not result.has_errors():
            #     user_resource.import_data(imported_data, dry_run=False)  # Actually import now

            # messages.success(request, f"User Accounts created successfuly.")

            # return redirect("profile_single", group.id)
        else:
            messages.error(request, "Please correct the error below.")
    else:
        
        form = ImportForm(formats) #instance=group

    return render(
        request,
        "user/user_import.html",
        {
            "form": form,
            "result": result,
            "confirm_form": confirm_form,
        },
    )

class ImportUserView(FormView):
    
    template_name = "user/user_import.html"
    form_class = forms.UserImportForm
    # success_url = "/thanks/"
    # initial = 'csv'

    def form_valid(self, form):
        
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        # form.send_email()
        return super().form_valid(form)
    
    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        user_resource = UserResource()
        dataset = Dataset()
        new_users = request.FILES['import_file']

        imported_data = dataset.load(new_users.read().decode(), format='csv')#, headers=False
        result = user_resource.import_data(imported_data, dry_run=True)  # Test the data import

        if not result.has_errors():
            user_resource.import_data(imported_data, dry_run=False)  # Actually import now
               
        form = self.form_class(request.POST, request.FILES)
        # if form.is_valid():
        #     f = request.FILES["import_file"]
        #     with open(settings.BASE_DIR / "media/user_import/file.csv", "wb+") as destination:
        #         for chunk in f.chunks():
        #             destination.write(chunk)
        #     messages.success(request, f"User Accounts created successfuly.")
        #     # return HttpResponseRedirect("/success/")

        return render(request, self.template_name, {"form": form, "result": result})

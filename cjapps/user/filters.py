from django.db.models import Q
import django_filters
from .models import User


# class LecturerFilter(django_filters.FilterSet):
#     username = django_filters.CharFilter(lookup_expr="exact", label="")
#     name = django_filters.CharFilter(method="filter_by_name", label="")
#     email = django_filters.CharFilter(lookup_expr="icontains", label="")
    
#     class Meta:
#         model = User
#         fields = ["username", "email"]

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # Change html classes and placeholders
#         self.filters["username"].field.widget.attrs.update(
#             {"class": "au-input", "placeholder": "ID No."}
#         )
#         self.filters["name"].field.widget.attrs.update(
#             {"class": "au-input", "placeholder": "Name"}
#         )
#         self.filters["email"].field.widget.attrs.update(
#             {"class": "au-input", "placeholder": "Email"}
#         )

#     def filter_by_name(self, queryset, name, value):
#         return queryset.filter(
#             Q(first_name__icontains=value) | Q(last_name__icontains=value)
#         )


class UserFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="user__name", method="filter_by_name", label="Name"
    )
    email = django_filters.CharFilter(
        field_name="user__email", lookup_expr="exact", label="Email"
    )
    role = django_filters.CharFilter(
        field_name="user__role", lookup_expr="icontains", label="Role"
    )
    # program = django_filters.CharFilter(
    #     field_name="user__program", lookup_expr="icontains", label=""
    # )

    class Meta:
        model = User
        fields = [
            "first_name",
            "email",
            "role",
            # "program",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change html classes and placeholders
        # self.filters["id_no"].field.widget.attrs.update(
        #     {"class": "au-input", "placeholder": "ID No."}
        # )
        self.filters["name"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Name"}
        )
        self.filters["email"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Email"}
        )
        self.filters["role"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Role"}
        )

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            Q(user__first_name__icontains=value)
            | Q(user__middle_name__icontains=value)
            | Q(user__last_name__icontains=value)
        )

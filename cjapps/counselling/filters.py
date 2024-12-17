from django_property_filter import PropertyFilterSet, PropertyBooleanFilter, PropertyNumberFilter
# from . import models

from django.contrib.auth import get_user_model
User = get_user_model()

class UserFilterSet(PropertyFilterSet):
    # prop_number = PropertyNumberFilter(field_name='discounted_price', lookup_expr='gte')

    class Meta:
        model = User
        # exclude = ['price']
        property_fields = [
            ('is_counsellor', PropertyBooleanFilter, ['exact']),
            # ('is_helpdesk', PropertyBooleanFilter, ['exact']),
            # ('series.book_count.', PropertyNumberFilter, ['gt', 'exact']),
        ]
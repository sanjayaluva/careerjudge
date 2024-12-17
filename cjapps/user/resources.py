from import_export import resources
# from .models import User

from django.contrib.auth import get_user_model
User = get_user_model()

class UserResource(resources.ModelResource):
    def before_save_instance(self, instance, using_transactions, dry_run):
        if not dry_run:
            instance.set_password('import_password')

    class Meta:
        model = User
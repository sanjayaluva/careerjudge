from django.apps import AppConfig


class CjappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cjapp'

    def ready(self):
        import cjapp.signals
from django.apps import AppConfig


class AjcarpartsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'AJcarparts'

    def ready(self):
        import AJcarparts.signals
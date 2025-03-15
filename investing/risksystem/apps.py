from django.apps import AppConfig


class RisksystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'risksystem'

    def ready(self):
        # Register any signals or perform other initialization here
        pass

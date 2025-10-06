from django.apps import AppConfig


class FindyourshoeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'findyourshoe'

    def ready(self):
        from .signals import save_foot_to_user
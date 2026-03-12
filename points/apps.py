from django.apps import AppConfig


class PointsConfig(AppConfig):
    name = 'points'

    def ready(self):
        import points.signals
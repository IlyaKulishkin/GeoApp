import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geopointsapp.settings')

app = Celery('geopointsapp')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
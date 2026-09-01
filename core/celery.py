import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Procura arquivos "tasks.py" dentro dos apps
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'atualizar-precos-cripto': {
        'task': 'assets.tasks.fetch_and_update_prices',
        'schedule': crontab(minute='*/4'),
    },
}
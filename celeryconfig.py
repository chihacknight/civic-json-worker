import os
from celery.schedules import crontab

BROKER_URL = 'redis://localhost:6379/0'

CELERY_IMPORTS = ("tasks", )
#CELERY_LOG_FILE=os.path.join(os.path.dirname(__file__), '../../run/celery.log')

CELERYBEAT_SCHEDULE = {
    'update-projects': {
        'task': 'tasks.update_projects',
        'schedule': crontab(minute='*/10'),
     },
    'backup-projects': {
        'task': 'tasks.backup_data',
        'schedule': crontab(minute='0', hour='*/6'),
     },
}

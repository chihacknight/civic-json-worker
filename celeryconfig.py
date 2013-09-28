import os
from celery.schedules import crontab

BROKER_URL = 'sqs://%s:%s@' % (os.environ['AWS_ACCESS_KEY'], os.environ['AWS_SECRET_KEY'])

CELERY_IMPORTS = ("tasks", )
CELERY_DEFAULT_QUEUE = 'civic-json'
#CELERY_LOG_FILE=os.path.join(os.path.dirname(__file__), '../../run/celery.log')

CELERYBEAT_SCHEDULE = {
    'update-projects': {
        'task': 'tasks.update_projects',
        'schedule': crontab(minute='*/10'),
     },
    'backup-projects': {
        'task': 'tasks.backup_data',
        'schedule': crontab(minute='*/60'),
     },
}

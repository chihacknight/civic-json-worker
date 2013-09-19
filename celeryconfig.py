import os
from datetime import timedelta

BROKER_URL = 'sqs://%s:%s@' % (os.environ['AWS_ACCESS_KEY'], os.environ['AWS_SECRET_KEY'])
CELERY_IMPORTS = ('worker', )

CELERYBEAT_SCHEDULE = {
    'grab-every-5-mins': {
        'task': 'worker.update_all_projects',
        'schedule': timedelta(seconds=300),
    },
}

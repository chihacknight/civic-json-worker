import os

BROKER_URL = 'sqs://%s:%s@' % (os.environ['AWS_ACCESS_KEY'], os.environ['AWS_SECRET_KEY'])
CELERY_IMPORTS = ('worker', )

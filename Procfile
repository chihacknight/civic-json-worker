web: gunicorn app:app -w 3
celery: celery -A worker worker --loglevel=info -B

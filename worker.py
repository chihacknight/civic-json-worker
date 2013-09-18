from urlparse import urlparse
from celery import Celery
import json
import requests
import os

celery = Celery('worker')
celery.config_from_object('celeryconfig')

GITHUB = 'https://api.github.com'

@celery.task
def update_all_projects():
    details = []
    with open('projects.json', 'rb') as f:
        projects = json.loads(f.read())
        for project in projects:
            # Call task below as normal function so processing
            # is not delayed.
            pj_details = update_project(project['full_name'])
            if pj_details:
                details.append(pj_details)
    with open('projects.json', 'wb') as f:
        f.write(json.dumps(details))
    return 'woot'

@celery.task
def update_project(full_name):
    url = '%s/repos/%s' % (GITHUB, full_name)
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    else:
        # if it returns an error, well, that's OK for now.
        return None

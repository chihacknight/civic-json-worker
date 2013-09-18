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
            pj_details = update_project(project)
            if pj_details:
                details.append(pj_details)
    with open('project_details.json', 'wb') as f:
        f.write(json.dumps(details))
    return 'woot'

@celery.task
def update_project(project_url):
    full_name = '/'.join(urlparse(project_url).path.split('/')[1:])
    url = '%s/repos/%s' % (GITHUB, full_name)
    r = requests.get(url)
    if r.status_code == 200:
        f = open('projects.json', 'rb')
        inp = json.loads(f.read())
        f.close()
        if not project_url in inp:
            inp.append(project_url)
            f = open('projects.json', 'wb')
            f.write(json.dumps(inp))
            f.close()
        return r.json()
    else:
        # if it returns an error, well, that's OK for now.
        return None

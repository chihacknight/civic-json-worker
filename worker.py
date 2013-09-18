from urlparse import urlparse
from celery import Celery
import json
import requests
import os

celery = Celery('worker')
celery.config_from_object('celeryconfig')

GITHUB = 'https://api.github.com'

@celery.task
def loadit():
    details = []
    with open('projects.json', 'rb') as f:
        projects = json.loads(f.read())
        for project in projects:
            user, pj = urlparse(project).path.split('/')[1:]
            url = '%s/repos/%s/%s' % (GITHUB, user, pj)
            r = requests.get(url)
            if r.status_code == 200:
                details.append(r.json())
            # else:
            #     print r.content
    print details
    if os.path.exists('details.json'):
        with open('details.json', 'rb') as f:
            all_details = json.loads(f.read())
    else:
        all_details = []
    if all_details:
        all_details.extend(details)
    print all_details
    with open('details.json', 'wb') as f:
        f.write(json.dumps(all_details))
    return 'woot'



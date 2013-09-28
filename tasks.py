import os
import json
from celery import Celery
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import requests
from urlparse import urlparse
from operator import itemgetter
from itertools import groupby

celery = Celery('tasks')
celery.config_from_object('celeryconfig')

GITHUB = 'https://api.github.com'
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
AWS_KEY = os.environ['AWS_ACCESS_KEY']
AWS_SECRET = os.environ['AWS_SECRET_KEY']
S3_BUCKET = os.environ['S3_BUCKET']

@celery.task
def update_projects():
    conn = S3Connection(AWS_KEY, AWS_SECRET)
    bucket = conn.get_bucket(S3_BUCKET)
    k = Key(bucket)
    k.key = 'projects.json'
    project_list = json.loads(k.get_contents_as_string())
    k.close()
    details = []
    k.close()
    for project_url in project_list:
        pj_details = update_project(project_url)
        if pj_details:
            details.append(pj_details)
        else:
            # if we get a non-200 back from Github, chances are we are being
            # throttled. Return nothing and let the next attempt pick it up. 
            return 'Github is throttling. Pick it up again on the next hour.'
    k.key = 'project_details.json'
    k.set_metadata('Content-Type', 'application/json')
    k.set_contents_from_string(json.dumps(details))
    k.set_acl('public-read')
    k.close()
    k.key = 'people.json'
    k.set_metadata('Content-Type', 'application/json')
    k.set_contents_from_string(json.dumps(get_people_totals(details)))
    k.set_acl('public-read')
    k.close()
    orgs = [d for d in details if d['owner']['type'] == 'Organization']
    k.key = 'organizations.json'
    k.set_metadata('Content-Type', 'application/json')
    k.set_contents_from_string(json.dumps(get_org_totals(orgs)))
    k.set_acl('public-read')
    k.close()
    return 'Updated'

def build_user(user):
    user_info = {}
    user_info['login'] = user.keys()[0]
    repos = user.values()[0]
    user_info['repositories'] = len(repos)
    try:
        user_info['contributions'] = sum([c['contributions'] for c in repos])
    except KeyError:
        pass
    user_info['avatar_url'] = repos[0]['avatar_url']
    user_info['html_url'] = repos[0]['html_url']
    headers = {'Authorization': 'token %s' % GITHUB_TOKEN}
    user_details = requests.get('%s/users/%s' % (GITHUB, user_info['login']), headers=headers)
    if user_details.status_code == 200:
        user_info['name'] = user_details.json().get('name')
        user_info['company'] = user_details.json().get('company')
        user_info['blog'] = user_details.json().get('blog')
        user_info['location'] = user_details.json().get('location')
    return user_info

def get_org_totals(details):
    all_orgs = []
    for project in details:
      all_orgs.append({'login': project['owner']['login'], 'repo': project})
    sorted_orgs = sorted(all_orgs, key=itemgetter('login'))
    grouped_orgs = []
    for k,g in groupby(sorted_orgs, key=itemgetter('login')):
        grouped_orgs.append({k:[r['repo']['owner'] for r in g]})
    org_totals = []
    for org in grouped_orgs:
        org_totals.append(build_user(org))
    return org_totals

def get_people_totals(details):
    all_users = []
    for project in details:
        all_users.extend(project['contributors'])
    sorted_users = sorted(all_users, key=itemgetter('login'))
    grouped_users = []
    for k, g in groupby(sorted_users, key=itemgetter('login')):
        grouped_users.append({k:list(g)})
    user_totals = []
    for user in grouped_users:
        user_totals.append(build_user(user))
    return user_totals

@celery.task
def update_project(project_url):
    full_name = '/'.join(urlparse(project_url).path.split('/')[1:3])
    url = '%s/repos/%s' % (GITHUB, full_name)
    headers = {'Authorization': 'token %s' % GITHUB_TOKEN}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        conn = S3Connection(AWS_KEY, AWS_SECRET)
        bucket = conn.get_bucket(S3_BUCKET)
        k = Key(bucket)
        k.key = 'projects.json'
        inp_list = list(set(json.loads(k.get_contents_as_string())))
        inp = [l.rstrip('/') for l in inp_list]
        k.close()
        if not project_url in inp:
            inp.append(project_url)
            k.set_metadata('Content-Type', 'application/json')
            k.set_contents_from_string(json.dumps(inp))
            k.set_acl('public-read')
            k.close()
        repo = r.json()
        owner = repo.get('owner')
        detail = {
            'id': repo.get('id'),
            'name': repo.get('name'),
            'description': repo.get('description'),
            'homepage': repo.get('homepage'),
            'html_url': repo.get('html_url'),
            'language': repo.get('language'),
            'watchers_count': repo.get('watchers_count'),
            'contributors_url': repo.get('contributors_url'),
            'forks_count': repo.get('forks_count'),
            'open_issues': repo.get('open_issues'),
            'created_at': repo.get('created_at'),
            'updated_at': repo.get('updated_at'),
        }
        detail['owner'] = {
            'login': owner.get('login'),
            'html_url': owner.get('html_url'),
            'avatar_url': owner.get('avatar_url'),
            'type': owner.get('type'),
        }
        detail['contributors'] = []
        if detail.get('contributors_url'):
            r = requests.get(detail.get('contributors_url'), headers=headers)
            if r.status_code == 200:
                for contributor in r.json():
                    cont = {}
                    login = contributor.get('login')
                    cont['owner'] = False
                    if login == owner.get('login'):
                        cont['owner'] = True
                    cont['login'] = login
                    cont['avatar_url'] = contributor.get('avatar_url')
                    cont['html_url'] = contributor.get('html_url')
                    cont['contributions'] = contributor.get('contributions')
                    detail['contributors'].append(cont)
        return detail
    else:
        # if it returns an error, well, that's OK for now.
        return None

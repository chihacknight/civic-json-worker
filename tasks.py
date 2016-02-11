import os
import json
from celery import Celery
import requests
from urllib.parse import urlparse
from operator import itemgetter
from itertools import groupby
from git import Repo, GitCommandError
from datetime import datetime

from app_config import GITHUB_TOKEN

celery = Celery('tasks')
celery.config_from_object('celeryconfig')

GITHUB = 'https://api.github.com'

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))

@celery.task
def update_projects():
    with open('{}/projects.json'.format(DATA_PATH), 'r') as f:
        project_list = json.loads(f.read())
    details = []
    for project_url in project_list:
        try:
            pj_details = update_project(project_url)
        except IOError:
            return 'Github is throttling. Just gonna try again after limit is reset.'
        if pj_details:
            details.append(pj_details)
    
    with open('{}/project_details.json'.format(DATA_PATH), 'w') as f:
        f.write(json.dumps(details, indent=4))
    
    update_people()
    update_orgs()
    
    return 'Updated projects'

@celery.task
def backup_data():
    os.setuid(1001)
    repo = Repo(DATA_PATH)
    g = repo.git
    g.add(repo_path)
    g.commit(message="Backed up at %s" % datetime.now().isoformat(), author="eric.vanzanten@gmail.com")
    g.push()
    return None

def update_people():
    with open('{}/project_details.json'.format(DATA_PATH), 'r') as f:
        details = json.loads(f.read())
    
    with open('{}/people.json'.format(DATA_PATH), 'w') as f:
        f.write(json.dumps(get_people_totals(details), indent=4))
    
    return 'Updated people'

def update_orgs():
    with open('{}/project_details.json'.format(DATA_PATH), 'r') as f:
        details = json.loads(f.read())
    
    orgs = [d for d in details if d['owner']['type'] == 'Organization']
    with open('{}/organizations.json'.format(DATA_PATH), 'w') as f:
        f.write(json.dumps(get_org_totals(orgs), indent=4))
    
    return 'Updated orgs'

def build_user(user):
    user_info = {}
    user_info['login'] = list(user.keys())[0]
    repos = list(user.values())[0]
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

def update_issues(project_url):
    full_name = '/'.join(urlparse(project_url).path.split('/')[1:3])
    url = '%s/repos/%s/issues' % (GITHUB, full_name)
    headers = {'Authorization': 'token %s' % GITHUB_TOKEN}
    params = {'labels': 'project-needs'}
    r = requests.get(url, headers=headers, params=params)
    all_issues = []
    if r.status_code == 200:
        for issue in r.json():
            all_issues.append({
                'title': issue.get('title'),
                'issue_url': issue.get('html_url'),
            })
        return all_issues
    else:
        return []

def update_project(project_url):
    full_name = '/'.join(urlparse(project_url).path.split('/')[1:3])
    url = '%s/repos/%s' % (GITHUB, full_name)
    headers = {'Authorization': 'token %s' % GITHUB_TOKEN}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        
        with open('{}/projects.json'.format(DATA_PATH), 'r') as f:
            inp_list = list(set(json.loads(f.read())))
        
        inp = [l.rstrip('/') for l in inp_list]
        
        if not project_url in inp:
            inp.append(project_url)
            
            with open('{}/projects.json'.format(DATA_PATH), 'w') as f:
                f.write(json.dumps(inp, indent=4))

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
            'pushed_at': repo.get('pushed_at'),
        }
        detail['owner'] = {
            'login': owner.get('login'),
            'html_url': owner.get('html_url'),
            'avatar_url': owner.get('avatar_url'),
            'type': owner.get('type'),
        }
        detail['project_needs'] = update_issues(project_url)
        detail['contributors'] = []
        if detail.get('contributors_url'):
            r = requests.get(detail.get('contributors_url'), headers=headers)
            if r.status_code == 200:
                for contributor in r.json():
                    cont = {}
                    login = contributor.get('login')
                    if login == 'invalid-email-address':
                        continue
                    cont['owner'] = False
                    if login == owner.get('login'):
                        cont['owner'] = True
                    cont['login'] = login
                    cont['avatar_url'] = contributor.get('avatar_url')
                    cont['html_url'] = contributor.get('html_url')
                    cont['contributions'] = contributor.get('contributions')
                    detail['contributors'].append(cont)
        part = requests.get('%s/stats/participation' % url, headers=headers)
        if part.status_code == 200:
            detail['participation'] = part.json()['all']
        return detail
    elif r.status_code == 404:
        # Can't find the project on gitub so scrub it from the list
        with open('{}/projects.json'.format(DATA_PATH), 'r') as f:
            projects = json.loads(f.read())

        projects.remove(project_url)
        
        with open('{}/projects.json'.format(DATA_PATH), 'w') as f:
            f.write(json.dumps(projects, indent=4))

        return None
    elif r.status_code == 403: 
        raise IOError('Over rate limit')

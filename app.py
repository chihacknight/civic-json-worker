from flask import Flask, make_response, request, current_app, abort
from datetime import timedelta
from functools import update_wrapper
import json
import os
import requests
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from urlparse import urlparse

THE_KEY = os.environ['FLASK_KEY']
GITHUB = 'https://api.github.com'
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
AWS_KEY = os.environ['AWS_ACCESS_KEY']
AWS_SECRET = os.environ['AWS_SECRET_KEY']

app = Flask(__name__)

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@app.route('/add-project/', methods=['POST'])
@crossdomain(origin="*")
def submit_project():
    project_url = request.form.get('project_url')
    project_details = update_project(project_url)
    if project_details:
        resp = make_response(json.dumps(project_details))
        resp.headers['Content-Type'] = 'application/json'
        return resp
    else:
        return make_response('The URL you submitted, %s, does not appear to be a valid Github repo' % project_url, 401)

@app.route('/update-projects/', methods=['GET'])
def update_projects():
    conn = S3Connection(AWS_KEY, AWS_SECRET)
    bucket = conn.get_bucket('civic-json')
    k = Key(bucket)
    k.key = 'projects.json'
    project_list = json.loads(k.get_contents_as_string())
    k.close()
    details = []
    k.close()
    for project_url in project_list:
        # Call task below as normal function so processing
        # is not delayed.
        pj_details = update_project(project_url)
        if pj_details:
            details.append(pj_details)
    k.key = 'project_details.json'
    k.set_contents_from_string(json.dumps(details))
    k.set_acl('public-read')
    k.set_metadata('Content-Type', 'application/json')
    k.close()
    resp = make_response('woot')
    return resp

@app.route('/delete-project/', methods=['POST'])
def delete_project():
    if request.form.get('the_key') == THE_KEY:
        project_url = request.form.get('project_url')
        conn = S3Connection(AWS_KEY, AWS_SECRET)
        bucket = conn.get_bucket('civic-json')
        k = Key(bucket)
        k.key = 'projects.json'
        projects = json.loads(k.get_contents_as_string())
        k.close()
        try:
            projects.remove(project_url)
            k.set_contents_from_string(json.dumps(projects))
            k.set_acl('public-read')
            k.set_metadata('Content-Type', 'application/json')
            k.close()
            resp = make_response('Deleted %s' % project_url)
        except ValueError:
            resp = make_response('%s is not in the registry', 400)
    else:
        resp = make_response("I can't do that Dave", 401)
    return resp

def update_project(project_url):
    full_name = '/'.join(urlparse(project_url).path.split('/')[1:])
    url = '%s/repos/%s' % (GITHUB, full_name)
    headers = {'Authorization': 'token %s' % GITHUB_TOKEN}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        conn = S3Connection(AWS_KEY, AWS_SECRET)
        bucket = conn.get_bucket('civic-json')
        k = Key(bucket)
        k.key = 'projects.json'
        inp = list(set(json.loads(k.get_contents_as_string())))
        k.close()
        if not project_url in inp:
            inp.append(project_url)
            k.set_contents_from_string(json.dumps(inp))
            k.set_acl('public-read')
            k.set_metadata('Content-Type', 'application/json')
            k.close()
        return r.json()
    else:
        # if it returns an error, well, that's OK for now.
        return None

if __name__ == "__main__":
    app.run(debug=True, port=7777)

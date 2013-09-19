from flask import Flask, make_response, request, current_app, abort
from datetime import timedelta
from functools import update_wrapper
import json
import os
import requests
from urlparse import urlparse

THE_KEY = os.environ['FLASK_KEY']
GITHUB = 'https://api.github.com'

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

@app.route('/projects/', methods=['GET'])
@crossdomain(origin="*")
def get_projects():
    pjs = []
    with open('project_details.json', 'rb') as f:
        pjs = f.read()
    resp = make_response(pjs)
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route('/update-projects/', methods=['GET'])
def update_projects():
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
    resp = make_response('woot')
    return resp

@app.route('/delete-project/', methods=['POST'])
def delete_project():
    if request.form.get('the_key') == THE_KEY:
        project_url = request.form.get('project_url')
        f = open('projects.json', 'rb')
        projects = json.load(f.read())
        f.close()
        try:
            projects.remove(project_url)
            f = open('projects.json', 'wb')
            f.write(json.dumps(projects))
            f.close()
            resp = make_response('Deleted %s' % project_url)
        except ValueError:
            resp = make_response('%s is not in the registry', 400)
    else:
        resp = make_response("I can't do that Dave", 401)
    return resp

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

if __name__ == "__main__":
    app.run(debug=True, port=7777)

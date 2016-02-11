from flask import Flask, make_response, request, current_app
from flask_cors import cross_origin
from datetime import timedelta
from functools import update_wrapper
import json
import os
import requests
from tasks import update_project, update_projects as update_pjs_task

from app_config import THE_KEY

app = Flask(__name__)

@app.route('/add-project/', methods=['POST'])
@cross_origin()
def submit_project():
    project_url = request.form.get('project_url')
    project_details = update_project(project_url)
    if project_details:
        resp = make_response(json.dumps(project_details))
        resp.headers['Content-Type'] = 'application/json'
        return resp
    else:
        return make_response('The URL you submitted, %s, does not appear to be a valid Github repo' % project_url, 400)

@app.route('/delete-project/', methods=['POST'])
def delete_project():
    if request.form.get('the_key') == THE_KEY:
        project_url = request.form.get('project_url')
        f = open('data/projects.json', 'rb')
        projects = json.loads(f.read())
        f.close()
        try:
            projects.remove(project_url)
            f = open('data/projects.json', 'wb')
            f.write(json.dumps(projects))
            f.close()
            resp = make_response('Deleted %s' % project_url)
        except ValueError:
            resp = make_response('%s is not in the registry', 400)
    else:
        resp = make_response("I can't do that Dave", 400)
    return resp

@app.route('/update-projects/', methods=['GET'])
def update_projects():
    update_pjs_task.delay()
    resp = make_response('Executed update task')
    return resp

if __name__ == "__main__":
    app.run(debug=True, port=6666)

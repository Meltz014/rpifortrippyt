import sys
import os
import AquariumLights
from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify
from sqlalchemy.orm import sessionmaker
from tabledef import *
import logging

logger = logging.getLogger("AquariumLights")

lights_control = AquariumLights.LightControl()

engine = create_engine('sqlite:///tutorial.db', echo=True)

app = Flask('Flask')
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(logger)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

def require_login(func):
    """
    Decorator to require login
    """
    def login_wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return render_template('login.html')
        else:
            return func(*args, **kwargs)

    return login_wrapper

@app.route("/")
@require_login
def main():
    app.logger.debug('hello')
    templateData = {
        'config_state': lights_control.get_config_state()
    }
    # Pass the template data into the template main.html and return it to the user
    return render_template('main.html', **templateData)

# The function below is executed when someone requests a URL with the pin number and action in it:
@app.route("/<key>", methods=["GET", "POST"])
@require_login
def handleattr(key):
    value = ''

    if key == 'favicon.ico':
        return 'None'

    if not hasattr(lights_control, key):
        raise InvalidUsage( 'Invalid attribute name {}'.format(key) )

    if request.method == "GET":
        value = lights_control.get_config_state().get(key,'Unknown')
        return jsonify({'value': value})

    elif request.method == "POST":
        if len(request.form.getlist('value[]')) > 0:
            new_val = [i for i in request.form.getlist('value[]')]
        else:
            new_val = request.form.get('value',None)
        setattr(lights_control, key, new_val)
        return jsonify('success')

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return main()

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=443, debug=True, ssl_context='adhoc')
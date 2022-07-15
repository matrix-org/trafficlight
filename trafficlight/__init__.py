# vim: expandtab ts=4:
import os
from datetime import datetime, timedelta

from flask import Flask
from trafficlight.store import add_test, get_tests, get_clients, add_client
from trafficlight.test_builder import TestCase

# Format in "2 hours" / "2 minutes" etc.
def format_delaytime(value):
    if value is None:
        return "N/A"
    now = datetime.now()
    interval = now - value
    return "%s min %s sec ago" % ( interval // timedelta(minutes=1), int((interval % timedelta(minutes=1)).total_seconds()))
                                    

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import client, status

    app.register_blueprint(client.bp)
    app.register_blueprint(status.bp)
    app.jinja_env.filters['delaytime'] = format_delaytime

    android_matcher = lambda x: x.registration['type'] == "element-android"
    web_matcher = lambda x: x.registration['type'] == "element-web"

    # Expand out the four test cases so far:
    add_test(TestCase("android, web", [android_matcher, web_matcher], client.generate_model))
    add_test(TestCase("web, android", [web_matcher, android_matcher], client.generate_model))
    add_test(TestCase("web, web", [web_matcher, web_matcher], client.generate_model))
    add_test(TestCase("android, android", [android_matcher, android_matcher], client.generate_model))
 
    # Maybe even write them to a report afterwards
    return app


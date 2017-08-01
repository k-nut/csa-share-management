import os
import sys
import logging

from datetime import date
from flask import Flask
from flask.json import JSONEncoder
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from raven.contrib.flask import Sentry


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:////home/knut/solawi.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'verysecret')
app.debug = os.environ.get("DEBUG", False)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

sentry = Sentry(app)


CORS(app, supports_credentials=True)


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, date):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)

app.json_encoder = CustomJSONEncoder

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


import solawi.views
import solawi.api
import solawi.old_app
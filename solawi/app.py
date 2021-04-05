import os
import sys
import logging

from datetime import date
from flask import Flask
from flask.json import JSONEncoder
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from raven.contrib.flask import Sentry


secret_key = os.environ.get('SECRET_KEY')
if secret_key is None:
    raise Exception("You must supply the `SECRET_KEY` environment variable.")

db_url = os.environ.get('DATABASE_URL')
if db_url is None:
    raise Exception("You must supply the `DATABASE_URL` environment variable.")
if "postgres://" in db_url:
    # The new SQLAlchemy versions expect the database name to be `postgresql`
    # and not just `postgres`. Heroku will only provide `postgres` here though
    # which is why we re-write it to match what SQLAlchemy expects.
    db_url = db_url.replace("postgres://", "postgresql://")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secret_key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 60 * 60
app.debug = os.environ.get("DEBUG", False)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
jwt = JWTManager(app)

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
migrate = Migrate(app, db)


import solawi.api
import solawi.commands

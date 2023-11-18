import logging
import os
import sys
from datetime import date, datetime
from decimal import Decimal

import sentry_sdk
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

secret_key = os.environ.get("SECRET_KEY")
if secret_key is None:
    raise Exception("You must supply the `SECRET_KEY` environment variable.")

db_url = os.environ.get("DATABASE_URL")
if db_url is None:
    raise Exception("You must supply the `DATABASE_URL` environment variable.")
if "postgres://" in db_url:
    # The new SQLAlchemy versions expect the database name to be `postgresql`
    # and not just `postgres`. Heroku will only provide `postgres` here though
    # which is why we re-write it to match what SQLAlchemy expects.
    db_url = db_url.replace("postgres://", "postgresql://")

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[FlaskIntegration(), SqlalchemyIntegration()],
    traces_sample_rate=0.6,
)


class CustomJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, date) or isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = secret_key
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 60 * 60
app.debug = os.environ.get("DEBUG", False)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
app.json = CustomJSONProvider(app)

jwt = JWTManager(app)


CORS(app, supports_credentials=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)


import solawi.api  # noqa:E402,F401
import solawi.commands  # noqa:E402,F401

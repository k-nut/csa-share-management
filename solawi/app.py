import os

from datetime import date
from flask import Flask, request
from flask.json import JSONEncoder
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:////home/knut/solawi.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'verysecret')
app.debug = os.environ.get("DEBUG", False)

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


@app.before_request
def debug():
    print(request.cookies)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


import solawi.views
import solawi.api
import solawi.old_app
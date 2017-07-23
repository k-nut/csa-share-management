import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:////home/knut/solawi.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'verysecret')
app.debug = os.environ.get("DEBUG", False)

CORS(app, supports_credentials=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


import solawi.views
import solawi.api
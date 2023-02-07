import os
import unittest

import decorator
from flask_jwt_extended import create_access_token
from flask_migrate import upgrade

from solawi.app import app, db
from test_factories import UserFactory


def with_app_context(func):
    def wrapper(func, *args, **kwargs):
        with app.app_context():
            return func(*args, **kwargs)

    return decorator.decorator(wrapper, func)


class DBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL_TEST")
        app.config["TESTING"] = True
        with app.app_context():
            upgrade()

    @classmethod
    def tearDownClass(cls):
        db.drop_all()
        db.engine.execute("DROP TABLE alembic_version")

    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        for table in reversed(db.metadata.sorted_tables):
            db.engine.execute(table.delete())
        db.session.commit()
        db.session.remove()


class AuthorizedTest(DBTest):
    def setUp(self):
        self.app = app.test_client()
        user = UserFactory.create()
        with app.app_context():
            self.app.environ_base[
                "HTTP_AUTHORIZATION"
            ] = f"Bearer {create_access_token(identity=user.email)}"

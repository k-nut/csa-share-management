import os
import unittest

import pytest
from flask_jwt_extended import create_access_token
from sqlalchemy import text

from solawi.app import app, db
from test_factories import UserFactory


class DBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL_TEST")
        app.config["TESTING"] = True
        with app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()

    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        with app.app_context():
            with db.engine.connect() as connection:
                for table in reversed(db.metadata.sorted_tables):
                    connection.execute(table.delete())
                db.session.commit()
                db.session.remove()


class AuthorizedTest(DBTest):
    @pytest.mark.usefixtures("app_ctx")
    def setUp(self):
        super().setUp()
        self.app = app.test_client()
        user = UserFactory.create()
        with app.app_context():
            self.app.environ_base[
                "HTTP_AUTHORIZATION"
            ] = f"Bearer {create_access_token(identity=user.email)}"

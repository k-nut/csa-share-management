import unittest
import os

from flask_migrate import upgrade

from solawi.app import app, db


class DBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL_TEST")
        app.config['TESTING'] = True
        with app.app_context():
            upgrade()

    @classmethod
    def tearDownClass(cls):
        db.drop_all()
        db.engine.execute("DROP TABLE alembic_version")

    def setUp(self):
        app.config["LOGIN_DISABLED"] = False
        app.login_manager.init_app(app)
        self.app = app.test_client()

    def tearDown(self):
        for table in reversed(db.metadata.sorted_tables):
            db.engine.execute(table.delete())
        db.session.commit()
        db.session.remove()


class AuthorizedTest(DBTest):
    def setUp(self):
        app.config["LOGIN_DISABLED"] = True
        app.login_manager.init_app(app)
        self.app = app.test_client()

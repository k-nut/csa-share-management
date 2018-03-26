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
        self.app = app.test_client()

    def tearDown(self):
        for tbl in reversed(db.metadata.sorted_tables):
            db.engine.execute(tbl.delete())
        db.session.commit()
        db.session.remove()

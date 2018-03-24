import unittest
import os

from flask_migrate import upgrade

from solawi.app import app, db
from solawi.models import Bet, Share, Deposit, Person


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
        db.session.query(Deposit).delete()
        db.session.query(Person).delete()
        db.session.query(Bet).delete()
        db.session.query(Share).delete()
        db.session.commit()
        db.session.remove()

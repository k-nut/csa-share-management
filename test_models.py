from flask.ext.testing import TestCase
from flask import Flask

from app import db

class MyTest(TestCase):
    def create_app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_person(self):
        from models import Person, Deposit
        from datetime import date

        p = Person("Knut Huehne")

        timestamp = date(2016, 1, 2)
        title = "Solawi Ratibor Knut Huehne"
        amount = 63.0

        d = Deposit(title=title,
                   person=p,
                   amount=amount,
                   timestamp=timestamp)

        d.save()
        assert p.number_of_deposits == 1
        assert p.total_deposits == 63
        assert len(Deposit.query.all()) == 1

        d.save()

    def test_other(self):
        from models import Deposit
        assert len(Deposit.query.all()) == 0

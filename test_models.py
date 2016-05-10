import unittest
import tempfile
import os

from solawi import app, db


class MyTest(unittest.TestCase):
    def setUp(self):
        # next line needed so that db.create_all knows what to create
        from models import Deposit, Share, Person

        self.db_fd, self.temp_filepath = tempfile.mkstemp()
        database_path = 'sqlite:///{}'.format(self.temp_filepath)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_path
        app.config['TESTING'] = True
        self.app = app.test_client()

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.remove(self.temp_filepath)

    def test_person(self):
        from models import Person, Deposit, Share
        from datetime import date

        person = Person.get_or_create("Knut Huehne")

        timestamp = date(2016, 1, 2)
        title = "Solawi Ratibor Knut Huehne"
        amount = 63.0

        deposit = Deposit(title=title,
                          person=person,
                          amount=amount,
                          timestamp=timestamp)

        deposit.save()

        share = Share("Share number one")
        share.people.append(person)
        share.save()
        assert share.number_of_deposits == 1
        assert share.total_deposits == 63
        assert len(Deposit.query.all()) == 1

    def test_other(self):
        from models import Deposit
        print Deposit.query.all()
        assert len(Deposit.query.all()) == 0

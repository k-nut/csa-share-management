import unittest
import tempfile
import os

from freezegun import freeze_time

from solawi.api import expected_today
from solawi.app import app, db


class MyTest(unittest.TestCase):
    def setUp(self):
        # next line needed so that db.create_all knows what to create
        from solawi.models import Deposit, Share, Person

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
        from datetime import date
        from solawi.models import Person, Deposit, Share

        person = Person.get_or_create("Firstname Lastname")

        timestamp = date(2016, 1, 2)
        title = "CSA 123 - June payment for Firstname Lastname and Other One"
        amount = 63.0

        deposit = Deposit(title=title,
                          person=person,
                          amount=amount,
                          timestamp=timestamp)

        deposit.save()

        share = Share(name="Firstname Lastname and Other One")
        share.people.append(person)
        share.save()
        assert share.number_of_deposits == 1
        assert share.total_deposits == 63
        assert len(Deposit.query.all()) == 1

    def test_other(self):
        from solawi.models import Deposit
        assert len(Deposit.query.all()) == 0

    def test_ignore_deposits(self):
        from solawi.models import Person, Deposit, Share
        from datetime import date

        person = Person.get_or_create("Firstname Lastname")

        timestamp = date(2016, 1, 24)
        title = "CSA 123 - February payment for Firstname Lastname and Other One"
        amount = 63.0

        deposit = Deposit(title=title,
                          person=person,
                          amount=amount,
                          timestamp=timestamp)

        deposit.save()

        share = Share(name="Firstname Lastname and Other One")
        share.people.append(person)
        share.save()
        assert share.number_of_deposits == 1
        assert share.total_deposits == 63
        assert len(Deposit.query.all()) == 1

        deposit.ignore = True
        deposit.save()
        assert share.number_of_deposits == 0
        assert share.total_deposits == 0
        assert len(Deposit.query.all()) == 1

    def test_expected_amount_wiht_custom_start_date(self):
        from solawi.models import Person, Deposit, Share
        from datetime import date

        person = Person.get_or_create("Firstname Lastname")

        timestamp = date(2016, 3, 25)
        title = "CSA 123 - March payment for Firstname Lastname and Other One"
        amount = 63.0

        deposit = Deposit(title=title,
                          person=person,
                          amount=amount,
                          timestamp=timestamp)

        deposit.save()

        share = Share(name="Firstname Lastname and Other One")
        share.people.append(person)
        share.save()
        assert share.number_of_deposits == 1
        assert share.total_deposits == 63
        assert len(Deposit.query.all()) == 1

        deposit.ignore = True
        deposit.save()
        assert share.number_of_deposits == 0
        assert share.total_deposits == 0
        assert len(Deposit.query.all()) == 1


class TestShare(unittest.TestCase):
    def test_expected_today_full_month(self):
        from solawi.models import Share
        import datetime
        share = Share(name="Good Share", bet_value=80)
        share.start_date = datetime.date(2017, 1, 1)
        with freeze_time("2017-03-28"):
            self.assertEqual(expected_today(share), 320)
from datetime import datetime, date
from decimal import Decimal

from solawi.models import Bet, Deposit, Share, Station
from test_factories import ShareFactory, BetFactory, PersonFactory
from test_helpers import DBTest


class DepositTest(DBTest):
    def test_jsonify(self):
        deposit = Deposit(title="June Payment John Doe",
                          timestamp=datetime(2018, 1, 1, 12, 0),
                          amount=80.21)
        deposit.save()

        expected = {'added_by': None,
                    'amount': Decimal('80.21'),
                    'id': deposit.id,
                    'ignore': False,
                    'is_security': False,
                    'person_id': None,
                    'timestamp': datetime(2018, 1, 1, 12, 0),
                    'title': 'June Payment John Doe'}
        assert deposit.json == expected


class BetTest(DBTest):
    def test_jsonify(self):
        share = ShareFactory.create()
        bet = BetFactory(share=share)

        expected = {'start_date': datetime(2018, 1, 1, 0, 0),
                    'end_date': None,
                    'id': bet.id,
                    'value': Decimal('90'),
                    'share_id': share.id
                    }
        assert bet.json == expected


class ShareTest(DBTest):
    def test_jsonify(self):
        share = ShareFactory(name="John Doe & Sabrina Doe",
                             email="john@example.com")

        expected = {
            "id": share.id,
            "name": "John Doe & Sabrina Doe",
            "archived": False,
            "bets": [],
            "station_id": share.station.id,
            "note": None,
            "email": "john@example.com"
        }

        assert share.json == expected

class PersonTest(DBTest):
    def test_jsonify(self):
        share = ShareFactory.create()
        person = PersonFactory(name="Misses Cash", share=share)

        expected = {
            "id": person.id,
            "name": "Misses Cash",
            "share_id": share.id
        }

        assert person.json == expected



class ModelTest(DBTest):
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

        share = ShareFactory.create(people=[person])
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

        share = ShareFactory.create(people=[person])
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

        share = ShareFactory.create(people=[person])
        assert share.number_of_deposits == 1
        assert share.total_deposits == 63
        assert len(Deposit.query.all()) == 1

        deposit.ignore = True
        deposit.save()
        assert share.number_of_deposits == 0
        assert share.total_deposits == 0
        assert len(Deposit.query.all()) == 1

    def test_expected_today_full_month(self):
        import datetime
        share = ShareFactory.create()
        bet = Bet(start_date=datetime.date(2017, 1, 1),
                  end_date=datetime.date(2017, 3, 31),
                  value=100,
                  share_id=share.id
                  )
        bet.save()
        assert share.expected_today == 300

    def test_expected_today_is_decimal(self):
        import datetime
        share = ShareFactory.create()
        bet = Bet(start_date=datetime.date(2017, 1, 1),
                  end_date=datetime.date(2017, 3, 31),
                  value=97.17,
                  share_id=share.id
                  )
        bet.save()
        assert share.expected_today == Decimal('291.51')

    def test_expected_today_across_years(self):
        import datetime
        share = ShareFactory.create()
        bet = Bet(start_date=datetime.date(2016, 1, 1),
                  end_date=datetime.date(2017, 3, 31),
                  value=10,
                  share_id=share.id
                  )
        bet.save()
        assert share.expected_today == 150

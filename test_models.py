from datetime import datetime, date
from decimal import Decimal

from unittest.mock import MagicMock, patch
from solawi.models import Bet, Deposit, Share, Station, User
from test_factories import ShareFactory, BetFactory, PersonFactory, MemberFactory, DepositFactory, UserFactory
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

    def test_latest(self):
        DepositFactory.create(timestamp=datetime(2018, 1, 1, 12, 0))
        DepositFactory.create(timestamp=datetime(2019, 1, 1, 12, 0))

        assert Deposit.latest_import() == datetime(2019, 1, 1, 12, 0)

    def test_latest_with_manual(self):
        user = UserFactory.create()
        DepositFactory.create(timestamp=datetime(2018, 1, 1, 12, 0))
        DepositFactory.create(timestamp=datetime(2019, 1, 1, 12, 0), added_by=user.id)

        assert Deposit.latest_import() == datetime(2018, 1, 1, 12, 0)


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

    def test_expected_today(self):
        bet = BetFactory.create(start_date=date(2017, 1, 1),
                                end_date=date(2017, 3, 31),
                                value=100,
                                )
        assert bet.expected_today == 300


class ShareTest(DBTest):
    def test_jsonify(self):
        share = ShareFactory()
        MemberFactory(name="John Doe", share=share)
        MemberFactory(name="Sabrina Doe", share=share)

        expected = {
            "id": share.id,
            "name": "John Doe & Sabrina Doe",
            "archived": False,
            "bets": [],
            "station_id": share.station.id,
            "note": None,
        }

        assert share.json == expected

    def test_name(self):
        share = ShareFactory()
        MemberFactory(name="Bob", share=share)
        MemberFactory(name="Anna", share=share)

        assert share.name == "Anna & Bob"

    def test_name_no_members(self):
        share = ShareFactory()

        assert share.name == ""

    def test_join_date(self):
        share = ShareFactory()
        BetFactory(share=share, start_date=date(2019, 1, 1))
        BetFactory(share=share, start_date=date(2018, 1, 1), end_date=date(2018, 12, 31))

        assert share.join_date == datetime(2018, 1, 1)


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


class MemberTest(DBTest):
    def test_jsonify(self):
        share = ShareFactory.create()
        member = MemberFactory(name="Mister Member",
                               email="paul.member@example.com",
                               phone="+49012345",
                               share=share)

        expected = {
            "id": member.id,
            "name": "Mister Member",
            "email": "paul.member@example.com",
            "phone": "+49012345",
            "share_id": share.id
        }

        assert member.json == expected


class UserTest(DBTest):
    def test_get_by_email(self):
        UserFactory.create(email='user1@example.org')
        UserFactory.create(active=False, email='user2@example.org')

        emails = User.get_all_emails()

        assert emails == [('user1@example.org',)]

    def test_authenticate_and_get_success(self):
        user = UserFactory.create(email='user1@example.org', password='hunter2')

        fetched_user = User.authenticate_and_get('user1@example.org', 'hunter2')

        assert fetched_user == user

    def test_authenticate_and_get_wrong_password(self):
        UserFactory.create(email='user1@example.org', password='hunter2')

        fetched_user = User.authenticate_and_get('user1@example.org', 'supersecret')

        assert fetched_user is None

    def test_authenticate_and_get_wrong_no_longer_active(self):
        UserFactory.create(email='user1@example.org', password='hunter2', active=False)

        fetched_user = User.authenticate_and_get('user1@example.org', 'hunter2')

        assert fetched_user is None


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

    def test_expected_today_without_end_date(self):
        import datetime
        share = ShareFactory.create()
        bet = Bet(start_date=datetime.date(2017, 1, 1),
                  value=100,
                  share_id=share.id
                  )
        bet.save()
        assert bet.expected_at(datetime.date(2017, 3, 31)) == 400

    def test_expected_today_without_end_date_future(self):
        import datetime
        share = ShareFactory.create()
        bet = Bet(start_date=datetime.date(2019, 6, 1),
                  value=100,
                  share_id=share.id
                  )
        bet.save()
        assert bet.expected_at(datetime.date(2019, 5, 20)) == 0

    def test_expected_today_without_end_date_mid_month(self):
        import datetime
        share = ShareFactory.create()
        bet = Bet(start_date=datetime.date(2017, 1, 1),
                  value=100,
                  share_id=share.id
                  )
        bet.save()
        assert bet.expected_at(datetime.date(2017, 3, 15)) == 300

    def test_expected_today_without_end_date_begin_month(self):
        import datetime
        share = ShareFactory.create()
        bet = Bet(start_date=datetime.date(2017, 1, 1),
                  value=100,
                  share_id=share.id
                  )
        bet.save()
        assert bet.expected_at(datetime.date(2017, 4, 1)) == 400

    def test_expected_today_half_month(self):
        import datetime
        share = ShareFactory.create()
        bet = Bet(start_date=datetime.date(2017, 1, 15),
                  end_date=datetime.date(2017, 3, 31),
                  value=100,
                  share_id=share.id
                  )
        bet.save()
        assert share.expected_today == 250

    def test_expected_today_half_month_mocked_today(self):
        import datetime
        share = ShareFactory.create()
        bet = Bet(start_date=datetime.date(2017, 1, 15),
                  value=100,
                  share_id=share.id
                  )
        bet.save()
        assert bet.expected_at(datetime.date(2017, 1, 17)) == 50

    def test_expected_today_half_month_mocked_today_half_delta(self):
        import datetime
        share = ShareFactory.create()
        bet = Bet(start_date=datetime.date(2019, 3, 15),
                  value=100,
                  share_id=share.id
                  )
        bet.save()
        assert bet.expected_at(datetime.date(2019, 7, 6)) == 450

    def test_expected_today_half_month_mocked_today_month_end(self):
        import datetime
        share = ShareFactory.create()
        bet = Bet(start_date=datetime.date(2017, 1, 15),
                  value=100,
                  share_id=share.id
                  )
        bet.save()
        assert bet.expected_at(datetime.date(2017, 1, 31)) == 150

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

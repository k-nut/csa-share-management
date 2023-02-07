from datetime import date, datetime
from decimal import Decimal

from solawi.models import Bet, Deposit, Person, User
from test_factories import (
    BetFactory,
    DepositFactory,
    MemberFactory,
    PersonFactory,
    ShareFactory,
    UserFactory,
)
from test_helpers import DBTest, with_app_context


class DepositTest(DBTest):
    @with_app_context
    def test_jsonify(self):
        deposit = Deposit(
            title="June Payment John Doe", timestamp=datetime(2018, 1, 1, 12, 0), amount=80.21
        )
        deposit.save()

        expected = {
            "added_by": None,
            "amount": Decimal("80.21"),
            "id": deposit.id,
            "ignore": False,
            "is_security": False,
            "person_id": None,
            "timestamp": datetime(2018, 1, 1, 12, 0),
            "title": "June Payment John Doe",
        }
        assert deposit.json == expected

    @with_app_context
    def test_latest(self):
        DepositFactory.create(timestamp=datetime(2018, 1, 1, 12, 0))
        DepositFactory.create(timestamp=datetime(2019, 1, 1, 12, 0))

        assert Deposit.latest_import() == datetime(2019, 1, 1, 12, 0)

    @with_app_context
    def test_latest_with_manual(self):
        user = UserFactory.create()
        DepositFactory.create(timestamp=datetime(2018, 1, 1, 12, 0))
        DepositFactory.create(timestamp=datetime(2019, 1, 1, 12, 0), added_by=user.id)

        assert Deposit.latest_import() == datetime(2018, 1, 1, 12, 0)


class BetTest(DBTest):
    @with_app_context
    def test_jsonify(self):
        share = ShareFactory.create()
        bet = BetFactory(share=share)

        expected = {
            "start_date": datetime(2018, 1, 1, 0, 0),
            "end_date": None,
            "id": bet.id,
            "value": Decimal("90"),
            "share_id": share.id,
        }
        assert bet.json == expected

    @with_app_context
    def test_expected_today(self):
        bet = BetFactory.create(
            start_date=date(2017, 1, 1),
            end_date=date(2017, 3, 31),
            value=100,
        )
        assert bet.expected_today == 300


class ShareTest(DBTest):
    @with_app_context
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

    @with_app_context
    def test_name(self):
        share = ShareFactory()
        MemberFactory(name="Bob", share=share)
        MemberFactory(name="Anna", share=share)

        assert share.name == "Anna & Bob"

    @with_app_context
    def test_name_no_members(self):
        share = ShareFactory()

        assert share.name == ""

    @with_app_context
    def test_join_date(self):
        share = ShareFactory()
        BetFactory(share=share, start_date=date(2019, 1, 1))
        BetFactory(share=share, start_date=date(2018, 1, 1), end_date=date(2018, 12, 31))

        assert share.join_date == datetime(2018, 1, 1)


class PersonTest(DBTest):
    @with_app_context
    def test_jsonify(self):
        share = ShareFactory.create()
        person = PersonFactory(name="Misses Cash", share=share)

        expected = {"id": person.id, "name": "Misses Cash", "share_id": share.id}

        assert person.json == expected


class MemberTest(DBTest):
    @with_app_context
    def test_jsonify(self):
        share = ShareFactory.create()
        member = MemberFactory(
            name="Mister Member", email="paul.member@example.com", phone="+49012345", share=share
        )

        expected = {
            "id": member.id,
            "name": "Mister Member",
            "email": "paul.member@example.com",
            "phone": "+49012345",
            "share_id": share.id,
        }

        assert member.json == expected


class UserTest(DBTest):
    @with_app_context
    def test_get_by_email(self):
        UserFactory.create(email="user1@example.org")
        UserFactory.create(active=False, email="user2@example.org")

        emails = User.get_all_emails()

        assert emails == [("user1@example.org",)]

    @with_app_context
    def test_authenticate_and_get_success(self):
        user = UserFactory.create(email="user1@example.org", password="hunter2")

        fetched_user = User.authenticate_and_get("user1@example.org", "hunter2")

        assert fetched_user == user

    @with_app_context
    def test_authenticate_and_get_wrong_password(self):
        UserFactory.create(email="user1@example.org", password="hunter2")

        fetched_user = User.authenticate_and_get("user1@example.org", "supersecret")

        assert fetched_user is None

    @with_app_context
    def test_authenticate_and_get_wrong_no_longer_active(self):
        UserFactory.create(email="user1@example.org", password="hunter2", active=False)

        fetched_user = User.authenticate_and_get("user1@example.org", "hunter2")

        assert fetched_user is None


class ModelTest(DBTest):
    @with_app_context
    def test_person(self):
        person = Person.get_or_create("Firstname Lastname")

        timestamp = date(2016, 1, 2)
        title = "CSA 123 - June payment for Firstname Lastname and Other One"
        amount = 63.0

        deposit = Deposit(title=title, person=person, amount=amount, timestamp=timestamp)

        deposit.save()

        share = ShareFactory.create(people=[person])
        assert share.number_of_deposits == 1
        assert share.total_deposits == 63
        assert len(Deposit.query.all()) == 1

    @with_app_context
    def test_other(self):
        assert len(Deposit.query.all()) == 0

    @with_app_context
    def test_ignore_deposits(self):
        person = Person.get_or_create("Firstname Lastname")

        timestamp = date(2016, 1, 24)
        title = "CSA 123 - February payment for Firstname Lastname and Other One"
        amount = 63.0

        deposit = Deposit(title=title, person=person, amount=amount, timestamp=timestamp)

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

    @with_app_context
    def test_expected_amount_wiht_custom_start_date(self):
        person = Person.get_or_create("Firstname Lastname")

        timestamp = date(2016, 3, 25)
        title = "CSA 123 - March payment for Firstname Lastname and Other One"
        amount = 63.0

        deposit = Deposit(title=title, person=person, amount=amount, timestamp=timestamp)

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

    @with_app_context
    def test_expected_today_full_month(self):
        share = ShareFactory.create()
        bet = Bet(
            start_date=date(2017, 1, 1),
            end_date=date(2017, 3, 31),
            value=100,
            share_id=share.id,
        )
        bet.save()
        assert share.expected_today == 300

    @with_app_context
    def test_expected_today_without_end_date(self):
        share = ShareFactory.create()
        bet = Bet(start_date=date(2017, 1, 1), value=100, share_id=share.id)
        bet.save()
        assert bet.expected_at(date(2017, 3, 31)) == 400

    @with_app_context
    def test_expected_today_without_end_date_future(self):
        share = ShareFactory.create()
        bet = Bet(start_date=date(2019, 6, 1), value=100, share_id=share.id)
        bet.save()
        assert bet.expected_at(date(2019, 5, 20)) == 0

    @with_app_context
    def test_expected_today_without_end_date_mid_month(self):
        share = ShareFactory.create()
        bet = Bet(start_date=date(2017, 1, 1), value=100, share_id=share.id)
        bet.save()
        assert bet.expected_at(date(2017, 3, 15)) == 300

    @with_app_context
    def test_expected_today_without_end_date_begin_month(self):
        share = ShareFactory.create()
        bet = Bet(start_date=date(2017, 1, 1), value=100, share_id=share.id)
        bet.save()
        assert bet.expected_at(date(2017, 4, 1)) == 400

    @with_app_context
    def test_expected_today_half_month(self):
        share = ShareFactory.create()
        bet = Bet(
            start_date=date(2017, 1, 15),
            end_date=date(2017, 3, 31),
            value=100,
            share_id=share.id,
        )
        bet.save()
        assert share.expected_today == 250

    @with_app_context
    def test_expected_today_half_month_mocked_today(self):
        share = ShareFactory.create()
        bet = Bet(start_date=date(2017, 1, 15), value=100, share_id=share.id)
        bet.save()
        assert bet.expected_at(date(2017, 1, 17)) == 50

    @with_app_context
    def test_expected_today_half_month_mocked_today_half_delta(self):
        share = ShareFactory.create()
        bet = Bet(start_date=date(2019, 3, 15), value=100, share_id=share.id)
        bet.save()
        assert bet.expected_at(date(2019, 7, 6)) == 450

    @with_app_context
    def test_expected_today_half_month_mocked_today_month_end(self):
        share = ShareFactory.create()
        bet = Bet(start_date=date(2017, 1, 15), value=100, share_id=share.id)
        bet.save()
        assert bet.expected_at(date(2017, 1, 31)) == 150

    @with_app_context
    def test_expected_today_is_decimal(self):
        share = ShareFactory.create()
        bet = Bet(
            start_date=date(2017, 1, 1),
            end_date=date(2017, 3, 31),
            value=97.17,
            share_id=share.id,
        )
        bet.save()
        assert share.expected_today == Decimal("291.51")

    @with_app_context
    def test_expected_today_across_years(self):
        share = ShareFactory.create()
        bet = Bet(
            start_date=date(2016, 1, 1),
            end_date=date(2017, 3, 31),
            value=10,
            share_id=share.id,
        )
        bet.save()
        assert share.expected_today == 150

    @with_app_context
    def test_expected_at_a_time_before_the_bets_end_time(self):
        share = ShareFactory.create()
        bet = Bet(
            start_date=date(2017, 1, 1),
            end_date=date(2017, 12, 31),
            value=100,
            share_id=share.id,
        )
        bet.save()
        assert bet.expected_at(date(2017, 3, 31)) == 300

    @with_app_context
    def test_expected_before_the_bet_starts(self):
        share = ShareFactory.create()
        bet = Bet(
            start_date=date(2023, 1, 1),
            value=100,
            share_id=share.id,
        )
        bet.save()
        self.assertEqual(bet.expected_at(date(2022, 12, 18)), 0)

    @with_app_context
    def test_expected_before_the_bet_starts_but_close_enough_to_count(self):
        share = ShareFactory.create()
        bet = Bet(
            start_date=date(2023, 1, 1),
            value=100,
            share_id=share.id,
        )
        bet.save()
        self.assertEqual(bet.expected_at(date(2022, 12, 28)), 100)

    @with_app_context
    def test_expected_in_the_starting_month(self):
        share = ShareFactory.create()
        bet = Bet(
            start_date=date(2023, 1, 1),
            value=100,
            share_id=share.id,
        )
        bet.save()
        self.assertEqual(bet.expected_at(date(2023, 1, 28)), 200)

    @with_app_context
    def test_expected_before_the_bet_starts_but_in_the_same_year(self):
        share = ShareFactory.create()
        bet = Bet(
            start_date=date(2023, 3, 1),
            value=100,
            share_id=share.id,
        )
        bet.save()
        self.assertEqual(bet.expected_at(date(2023, 2, 28)), 100)

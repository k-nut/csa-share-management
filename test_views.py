from datetime import date, datetime, timedelta
from unittest.mock import patch

from flask import Response
from solawi.app import db, app
from solawi.models import Member, Share, Bet
from test_factories import ShareFactory, BetFactory, MemberFactory, StationFactory, UserFactory, DepositFactory, \
    PersonFactory
from test_helpers import DBTest, AuthorizedTest
from flask_jwt_extended import create_access_token


class AuthorizedViewsTests(AuthorizedTest):
    def test_delete_bet(self):
        from solawi.models import Bet, Share

        bet = BetFactory.create()
        share = bet.share

        self.assertEqual(db.session.query(Bet).count(), 1)

        response = self.app.delete(f"/api/v1/shares/{share.id}/bets/{bet.id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(db.session.query(Bet).count(), 0)

    def test_delete_bet_unkown_bet(self):
        from solawi.models import Bet, Share

        bet = BetFactory.create()
        share = bet.share

        self.assertEqual(db.session.query(Bet).count(), 1)

        response = self.app.delete(f"/api/v1/shares/{share.id}/bets/{bet.id + 1}")

        self.assertEqual(response.status_code, 404)

    def test_add_share(self):
        from solawi.models import Share

        self.assertEqual(db.session.query(Share).count(), 0)

        response = self.app.post(f"/api/v1/shares", json={"note": "my note"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(db.session.query(Share).count(), 1)
        self.assertEqual(response.get_json()["share"]["note"], "my note")

    def test_share_emails_empty(self):
        share = ShareFactory.create()

        response: Response = self.app.get(f"/api/v1/shares/{share.id}/emails")

        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.json, {"emails": []})

    def test_share_emails(self):
        member = MemberFactory.create(email="test@example.org")
        share = ShareFactory.create(members=[member])

        response: Response = self.app.get(f"/api/v1/shares/{share.id}/emails")
        expected = ["test@example.org"]

        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.json, {"emails": expected})

    def test_members(self):
        member1 = MemberFactory.create(email="peter@example.org",
                                       name="Peter Farmer",
                                       phone="001234")
        member2 = MemberFactory.create(email="paula@example.org",
                                       name="Paula Farmer",
                                       phone="001234")
        member3 = MemberFactory.create(email="jane@example.org",
                                       name="Jane Doe",
                                       phone="0055689")

        station1 = StationFactory.create(name="Station 1")
        station2 = StationFactory.create(name="Station 2")

        share1 = ShareFactory.create(members=[member1, member2], station=station1)
        share2 = ShareFactory.create(members=[member3], station=station2)

        BetFactory.create(share=share1, start_date=date(2018, 1, 1), end_date=date(2018, 12, 1))
        BetFactory.create(share=share1, start_date=date(2019, 1, 1))
        BetFactory.create(share=share2, start_date=date(2019, 1, 15))

        expected = [
            {
                "email": "peter@example.org",
                "id": member1.id,
                "name": "Peter Farmer",
                "phone": "001234",
                "share_id": share1.id,
                "station_name": "Station 1",
                "join_date": "2018-01-01T00:00:00"
            },
            {
                "email": "paula@example.org",
                "id": member2.id,
                "name": "Paula Farmer",
                "phone": "001234",
                "share_id": share1.id,
                "station_name": "Station 1",
                "join_date": "2018-01-01T00:00:00"
            },
            {
                "email": "jane@example.org",
                "id": member3.id,
                "name": "Jane Doe",
                "phone": "0055689",
                "share_id": share2.id,
                "station_name": "Station 2",
                "join_date": "2019-01-15T00:00:00"
            }
        ]

        response: Response = self.app.get(f"/api/v1/members")

        self.assertEqual(response.status_code, 200)
        self.maxDiff = None
        self.assertEqual(response.json, {"members": expected})

    def test_members_expired(self):
        member1 = MemberFactory.create()
        member2 = MemberFactory.create()

        station1 = StationFactory.create()
        station2 = StationFactory.create()

        valid_bet = BetFactory.create()
        expired_bet = BetFactory.create(end_date=date(2016, 1, 1))

        ShareFactory.create(members=[member1], station=station1, bets=[expired_bet])
        ShareFactory.create(members=[member2], station=station2, bets=[valid_bet])

        response: Response = self.app.get(f"/api/v1/members?active=true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["members"]), 1)

    def test_create_member(self):
        member1 = MemberFactory.create(name="Paul Wild / Paula Wilder")
        share = ShareFactory.create(members=[member1])

        self.assertEqual(len(share.members), 1)

        new_member_json = {"name": "Paul Wild", "share_id": share.id}
        response: Response = self.app.post(f"/api/v1/members", json=new_member_json)

        updated_share = Share.get(share.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(updated_share.members), 2)

    def test_create_member_without_share(self):
        self.assertEqual(Member.query.count(), 0)
        self.assertEqual(Share.query.count(), 0)

        new_member_json = {"name": "Paul Wild", "email": "paul@example.org", "phone": "0123"}
        response: Response = self.app.post(f"/api/v1/members", json=new_member_json)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Member.query.count(), 1)
        self.assertEqual(Share.query.count(), 1)

    def test_change_member(self):
        member = MemberFactory.create(name="Paul Wild / Paula Wilder")

        new_member_json = {"name": "Paul Wild"}
        response: Response = self.app.patch(f"/api/v1/members/{member.id}", json=new_member_json)

        updated_member = Member.get(member.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated_member.name, "Paul Wild")
        self.assertEqual(response.json["member"]["name"], "Paul Wild")

    def test_delete_member(self):
        member = MemberFactory.create(name="Paul Wild")

        self.assertEqual(Member.query.count(), 1)

        response: Response = self.app.delete(f"/api/v1/members/{member.id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Member.query.count(), 0)


class UnAuthorizedViewsTests(DBTest):
    def test_delete_bet_required_auth(self):
        from solawi.models import Bet, Share

        bet: Bet = BetFactory.create()
        share = bet.share

        self.assertEqual(db.session.query(Bet).count(), 1)

        response = self.app.delete(f"/api/v1/shares/{share.id}/bets/{bet.id}")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(db.session.query(Bet).count(), 1)

    def test_add_share_unauthorized(self):
        from solawi.models import Share

        self.assertEqual(db.session.query(Share).count(), 0)

        response = self.app.post(f"/api/v1/shares", json={"note": "my note"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(db.session.query(Share).count(), 0)

    def test_login_success(self):
        UserFactory.create(email='user@example.org', password="supersecret")

        response = self.app.post(f"/api/v1/login", json={"email": "user@example.org", "password": "supersecret"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json['access_token']) > 1)

    def test_login_no_user(self):
        response = self.app.post(f"/api/v1/login", json={"email": "myuser@example.org", "password": "hunter2"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "login failed"})

    def test_login_wrong_password(self):
        UserFactory.create(email='user@example.org', password="supersecret")

        response = self.app.post(f"/api/v1/login", json={"email": "user@example.org", "password": "hunter2"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "login failed"})

    def test_login_not_active(self):
        UserFactory.create(email='user@example.org', password="supersecret", active=False)

        response = self.app.post(f"/api/v1/login", json={"email": "user@example.org", "password": "supersecret"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "login failed"})


class UserManagementViewsTests(DBTest):
    def _login_as_user(self, user):
        self.app = app.test_client()
        with app.app_context():
            self.app.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {create_access_token(identity=user.email)}'

    def test_modify_user(self):
        from solawi.models import User

        user: User = UserFactory.create(password='hunter2')
        self._login_as_user(user)
        response = self.app.patch(f"/api/v1/users/{user.id}", json={"password": "a-password-of-appropriate-length"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"user": user.json})
        updated_user = User.get(user.id)
        self.assertTrue(updated_user.check_password('a-password-of-appropriate-length'))

    def test_modify_user_requires_password(self):
        from solawi.models import User

        user: User = UserFactory.create(password='hunter2')
        self._login_as_user(user)

        response = self.app.patch(f"/api/v1/users/{user.id}")

        self.assertEqual(response.status_code, 400)

    def test_modify_fails_if_too_short(self):
        from solawi.models import User

        user: User = UserFactory.create(email='user@example.org', password='hunter2')
        self._login_as_user(user)

        response = self.app.patch(f"/api/v1/users/{user.id}", json={"password": "tooshort"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'message': 'Password must be at least 14 characters long'})

        updated_user = User.get(user.id)
        self.assertTrue(updated_user.check_password('hunter2'))  # did not change own user

    def test_modify_other_user_fails(self):
        from solawi.models import User

        user: User = UserFactory.create(email='user@example.org', password='hunter2')
        another_user: User = UserFactory.create(password='supersecret', email='other@example.org')
        another_user_id = another_user.id
        self._login_as_user(user)

        response = self.app.patch(f"/api/v1/users/{another_user_id}",
                                  json={"password": "a-password-of-appropriate-length"})

        self.assertEqual(response.status_code, 403)

        updated_user = User.get(user.id)
        self.assertTrue(updated_user.check_password('hunter2'))  # did not change own user
        updated_other_user = User.get(another_user_id)
        self.assertTrue(updated_other_user.check_password('supersecret'))  # did not change other user

    def test_modify_user_fails_for_unknown_user(self):
        from solawi.models import User

        user: User = UserFactory.create(password='hunter2')
        self._login_as_user(user)

        response = self.app.patch(f"/api/v1/users/9001", json={"password": "a-password-of-appropriate-length"})

        self.assertEqual(response.status_code, 403)

    def test_modify_user_updates_last_changed_date(self):
        from solawi.models import User

        user: User = UserFactory.create(password='hunter2')
        self._login_as_user(user)

        with patch('solawi.models.date') as mock_date:
            mock_date.today.return_value = date(2017, 3, 31)
            response = self.app.patch(f"/api/v1/users/{user.id}", json={"password": "a-password-of-appropriate-length"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"user": user.json})
        updated_user = User.get(user.id)
        self.assertEqual(updated_user.password_changed_at, date(2017, 3, 31))


class SharesTests(AuthorizedTest):
    def test_get_shares(self):
        bet = BetFactory.create(value=99)
        MemberFactory.create(share=bet.share, name="Tom Doe")
        MemberFactory.create(share=bet.share, name="Sarah Foe")

        BetFactory.create(value=102)

        response = self.app.get(f"/api/v1/shares")

        expected = {'shares': [{'archived': False,
                                'bets': [{'end_date': None,
                                          'id': 1,
                                          'share_id': 1,
                                          'start_date': '2018-01-01T00:00:00',
                                          'value': 99}],
                                'id': 1,
                                'name': 'Sarah Foe & Tom Doe',
                                'note': None,
                                'station_id': 1},
                               {'archived': False,
                                'bets': [{'end_date': None,
                                          'id': 2,
                                          'share_id': 2,
                                          'start_date': '2018-01-01T00:00:00',
                                          'value': 102}],
                                'id': 2,
                                'name': '',
                                'note': None,
                                'station_id': 2}]}

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json, expected)


class PaymentStatusTests(AuthorizedTest):
    def test_get_shares(self):
        # The tests for making sure that the right amout is calculated for the
        # expected value are in test_models
        # This should only be for the api
        station = StationFactory.create(name="Our Station")
        share = ShareFactory.create(station=station)
        bet = BetFactory.create(value=99, start_date=date(2019, 1, 1), end_date=date(2019, 2, 1), share=share)
        person = PersonFactory.create(share=bet.share)
        DepositFactory.create(person=person, amount=99)

        response = self.app.get(f"/api/v1/shares/payment_status")

        expected = {'shares': [{'archived': False,
                                'difference_today': 0,
                                'expected_today': 99,
                                'id': 1,
                                'name': '',
                                'note': None,
                                'number_of_deposits': 1,
                                'station_name': "Our Station",
                                'total_deposits': 99.0}]}

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json, expected)


class ShareDetailsTests(AuthorizedTest):
    def test_get_share_details(self):
        share = ShareFactory.create()

        response = self.app.get(f"/api/v1/shares/{share.id}")

        expected = {'share': {'archived': False,
                              'bets': [],
                              'difference_today': 0,
                              'expected_today': 0,
                              'id': 1,
                              'name': '',
                              'note': None,
                              'station_id': 1,
                              'total_deposits': 0}}

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, expected)


class BetDetailsTests(AuthorizedTest):
    def test_create_bet(self):
        share = ShareFactory.create()
        self.assertEqual(db.session.query(Bet).count(), 0)

        response = self.app.post(f"/api/v1/shares/{share.id}/bets", json={"value": "99", "start_date": "2019-01-01"})

        bet = db.session.query(Bet).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(db.session.query(Bet).count(), 1)
        self.assertEqual(bet.value, 99)
        self.assertEqual(bet.start_date, datetime(2019, 1, 1, 0, 0))
        self.assertEqual(bet.end_date, None)

    def test_edit_bet(self):
        bet = BetFactory.create(value=20)

        response = self.app.post(f"/api/v1/shares/{bet.share.id}/bets", json={"id": bet.id, "value": "99"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(db.session.query(Bet).count(), 1)
        updated_bet = db.session.query(Bet).first()
        self.assertEqual(updated_bet.value, 99)
        self.assertEqual(updated_bet.start_date, bet.start_date)
        self.assertEqual(updated_bet.end_date, bet.end_date)

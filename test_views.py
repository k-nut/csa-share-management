from datetime import date
from unittest.mock import patch

import pytest
from flask_jwt_extended import create_access_token

from solawi.app import app, db
from solawi.models import Bet, Deposit, Member, Share, User
from test_factories import (
    BetFactory,
    DepositFactory,
    MemberFactory,
    PersonFactory,
    ShareFactory,
    StationFactory,
    UserFactory,
)
from test_helpers import AuthorizedTest, DBTest


class AuthorizedViewsTests(AuthorizedTest):
    @pytest.mark.usefixtures("app_ctx")
    def test_share_emails_empty(self):
        share = ShareFactory.create()

        response = self.app.get(f"/api/v1/shares/{share.id}/emails")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"emails": []})

    @pytest.mark.usefixtures("app_ctx")
    def test_share_emails(self):
        member = MemberFactory.create(email="test@example.org")
        share = ShareFactory.create(members=[member])

        response = self.app.get(f"/api/v1/shares/{share.id}/emails")
        expected = ["test@example.org"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"emails": expected})

    @pytest.mark.usefixtures("app_ctx")
    def test_members(self):
        member1 = MemberFactory.create(
            email="peter@example.org", name="Peter Farmer", phone="001234"
        )
        member2 = MemberFactory.create(
            email="paula@example.org", name="Paula Farmer", phone="001234"
        )
        member3 = MemberFactory.create(email="jane@example.org", name="Jane Doe", phone="0055689")

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
                "join_date": "2018-01-01",
            },
            {
                "email": "paula@example.org",
                "id": member2.id,
                "name": "Paula Farmer",
                "phone": "001234",
                "share_id": share1.id,
                "station_name": "Station 1",
                "join_date": "2018-01-01",
            },
            {
                "email": "jane@example.org",
                "id": member3.id,
                "name": "Jane Doe",
                "phone": "0055689",
                "share_id": share2.id,
                "station_name": "Station 2",
                "join_date": "2019-01-15",
            },
        ]

        response = self.app.get("/api/v1/members")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"members": expected})

    @pytest.mark.usefixtures("app_ctx")
    def test_members_expired(self):
        member1 = MemberFactory.create()
        member2 = MemberFactory.create()

        station1 = StationFactory.create()
        station2 = StationFactory.create()

        valid_bet = BetFactory.create()
        expired_bet = BetFactory.create(end_date=date(2016, 1, 1))

        ShareFactory.create(members=[member1], station=station1, bets=[expired_bet])
        ShareFactory.create(members=[member2], station=station2, bets=[valid_bet])

        response = self.app.get("/api/v1/members?active=true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["members"]), 1)

    @pytest.mark.usefixtures("app_ctx")
    def test_create_member(self):
        member1 = MemberFactory.create(name="Paul Wild / Paula Wilder")
        share = ShareFactory.create(members=[member1])
        share_id = share.id

        self.assertEqual(len(share.members), 1)

        new_member_json = {"name": "Paul Wild", "share_id": share_id}
        response = self.app.post("/api/v1/members", json=new_member_json)

        updated_share = Share.get(share_id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(updated_share.members), 2)

    @pytest.mark.usefixtures("app_ctx")
    def test_create_member_without_share(self):
        self.assertEqual(Member.query.count(), 0)
        self.assertEqual(Share.query.count(), 0)

        new_member_json = {"name": "Paul Wild", "email": "paul@example.org", "phone": "0123"}
        response = self.app.post("/api/v1/members", json=new_member_json)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Member.query.count(), 1)
        self.assertEqual(Share.query.count(), 1)

    @pytest.mark.usefixtures("app_ctx")
    def test_change_member(self):
        member = MemberFactory.create(name="Paul Wild / Paula Wilder")

        new_member_json = {"name": "Paul Wild"}
        response = self.app.patch(f"/api/v1/members/{member.id}", json=new_member_json)

        updated_member = Member.get(member.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated_member.name, "Paul Wild")
        self.assertEqual(response.json["member"]["name"], "Paul Wild")

    @pytest.mark.usefixtures("app_ctx")
    def test_cannot_change_member_id(self):
        member = MemberFactory.create(name="Paul Wild / Paula Wilder")

        new_member_json = {"id": 100}
        response = self.app.patch(f"/api/v1/members/{member.id}", json=new_member_json)

        self.assertEqual(response.status_code, 400)

    @pytest.mark.usefixtures("app_ctx")
    def test_delete_member(self):
        member = MemberFactory.create(name="Paul Wild")

        self.assertEqual(Member.query.count(), 1)

        response = self.app.delete(f"/api/v1/members/{member.id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Member.query.count(), 0)


class UnAuthorizedViewsTests(DBTest):
    @pytest.mark.usefixtures("app_ctx")
    def test_delete_bet_required_auth(self):
        bet: Bet = BetFactory.create()
        share = bet.share

        self.assertEqual(db.session.query(Bet).count(), 1)

        response = self.app.delete(f"/api/v1/shares/{share.id}/bets/{bet.id}")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(db.session.query(Bet).count(), 1)

    @pytest.mark.usefixtures("app_ctx")
    def test_login_success(self):
        UserFactory.create(email="user@example.org", password="supersecret")

        response = self.app.post(
            "/api/v1/login", json={"email": "user@example.org", "password": "supersecret"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json["access_token"]) > 1)

    @pytest.mark.usefixtures("app_ctx")
    def test_login_no_user(self):
        response = self.app.post(
            "/api/v1/login", json={"email": "myuser@example.org", "password": "hunter2"}
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "login failed"})

    @pytest.mark.usefixtures("app_ctx")
    def test_login_wrong_password(self):
        UserFactory.create(email="user@example.org", password="supersecret")

        response = self.app.post(
            "/api/v1/login", json={"email": "user@example.org", "password": "hunter2"}
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "login failed"})

    @pytest.mark.usefixtures("app_ctx")
    def test_login_not_active(self):
        UserFactory.create(email="user@example.org", password="supersecret", active=False)

        response = self.app.post(
            "/api/v1/login", json={"email": "user@example.org", "password": "supersecret"}
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"message": "login failed"})


class UserManagementViewsTests(DBTest):
    def _login_as_user(self, user):
        self.app = app.test_client()
        with app.app_context():
            self.app.environ_base["HTTP_AUTHORIZATION"] = (
                f"Bearer {create_access_token(identity=user.email)}"
            )

    @pytest.mark.usefixtures("app_ctx")
    def test_modify_user(self):
        user: User = UserFactory.create(password="hunter2")
        self._login_as_user(user)
        response = self.app.patch(
            f"/api/v1/users/{user.id}", json={"password": "a-password-of-appropriate-length"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"user": user.json})
        updated_user = User.get(user.id)
        self.assertTrue(updated_user.check_password("a-password-of-appropriate-length"))

    @pytest.mark.usefixtures("app_ctx")
    def test_modify_user_requires_password(self):
        user: User = UserFactory.create(password="hunter2")
        self._login_as_user(user)

        response = self.app.patch(f"/api/v1/users/{user.id}", json={})

        self.assertEqual(response.status_code, 400)

    @pytest.mark.usefixtures("app_ctx")
    def test_modify_fails_if_too_short(self):
        user: User = UserFactory.create(email="user@example.org", password="hunter2")
        self._login_as_user(user)

        response = self.app.patch(f"/api/v1/users/{user.id}", json={"password": "tooshort"})

        self.assertEqual(response.status_code, 400)
        self.assertTrue("validation_error" in response.json)

        updated_user = User.get(user.id)
        self.assertTrue(updated_user.check_password("hunter2"))  # did not change own user

    @pytest.mark.usefixtures("app_ctx")
    def test_modify_other_user_fails(self):
        user: User = UserFactory.create(email="user@example.org", password="hunter2")
        another_user: User = UserFactory.create(password="supersecret", email="other@example.org")
        another_user_id = another_user.id
        self._login_as_user(user)

        response = self.app.patch(
            f"/api/v1/users/{another_user_id}",
            json={"password": "a-password-of-appropriate-length"},
        )

        self.assertEqual(response.status_code, 403)

        updated_user = User.get(user.id)
        self.assertTrue(updated_user.check_password("hunter2"))  # did not change own user
        updated_other_user = User.get(another_user_id)
        self.assertTrue(
            updated_other_user.check_password("supersecret")
        )  # did not change other user

    @pytest.mark.usefixtures("app_ctx")
    def test_modify_user_fails_for_unknown_user(self):
        user: User = UserFactory.create(password="hunter2")
        self._login_as_user(user)

        response = self.app.patch(
            "/api/v1/users/9001", json={"password": "a-password-of-appropriate-length"}
        )

        self.assertEqual(response.status_code, 403)

    @pytest.mark.usefixtures("app_ctx")
    def test_modify_user_updates_last_changed_date(self):
        user: User = UserFactory.create(password="hunter2")
        self._login_as_user(user)

        with patch("solawi.models.date") as mock_date:
            mock_date.today.return_value = date(2017, 3, 31)
            response = self.app.patch(
                f"/api/v1/users/{user.id}", json={"password": "a-password-of-appropriate-length"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"user": user.json})
        updated_user = User.get(user.id)
        self.assertEqual(updated_user.password_changed_at, date(2017, 3, 31))

    @pytest.mark.usefixtures("app_ctx")
    def test_get_shares_fails_if_user_has_expired_password(self):
        user: User = UserFactory.create(password="hunter2")
        user.password_changed_at = None
        user.save()
        self._login_as_user(user)

        response = self.app.get("/api/v1/shares")

        self.assertEqual(response.status_code, 403)

    @pytest.mark.usefixtures("app_ctx")
    def test_list_users(self):
        user: User = UserFactory.create(password="hunter2", email="my.user@example.org")
        self._login_as_user(user)
        response = self.app.get("/api/v1/users")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"users": ["my.user@example.org"]})


class SharesTests(AuthorizedTest):
    @pytest.mark.usefixtures("app_ctx")
    def test_get_shares(self):
        bet = BetFactory.create(value=99)
        MemberFactory.create(share=bet.share, name="Tom Doe")
        MemberFactory.create(share=bet.share, name="Sarah Foe")

        BetFactory.create(value=102)

        response = self.app.get("/api/v1/shares")

        expected = {
            "shares": [
                {
                    "archived": False,
                    "bets": [
                        {
                            "end_date": None,
                            "id": 1,
                            "share_id": 1,
                            "start_date": "2018-01-01",
                            "value": 99,
                        }
                    ],
                    "id": 1,
                    "name": "Sarah Foe & Tom Doe",
                    "note": None,
                    "station_id": 1,
                },
                {
                    "archived": False,
                    "bets": [
                        {
                            "end_date": None,
                            "id": 2,
                            "share_id": 2,
                            "start_date": "2018-01-01",
                            "value": 102,
                        }
                    ],
                    "id": 2,
                    "name": "",
                    "note": None,
                    "station_id": 2,
                },
            ]
        }

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json, expected)


class PaymentStatusTests(AuthorizedTest):
    @pytest.mark.usefixtures("app_ctx")
    def test_get_shares(self):
        # The tests for making sure that the right amount is calculated for the
        # expected value are in test_models
        # This should only be for the api
        station = StationFactory.create(name="Our Station")
        share = ShareFactory.create(station=station)
        bet = BetFactory.create(
            value=99, start_date=date(2019, 1, 1), end_date=date(2019, 2, 1), share=share
        )
        person = PersonFactory.create(share=bet.share)
        DepositFactory.create(person=person, amount=99)
        DepositFactory.create(person=person, amount=120, is_security=True)

        response = self.app.get("/api/v1/shares/payment_status")

        expected = {
            "shares": [
                {
                    "archived": False,
                    "difference_today": 0,
                    "expected_today": 99,
                    "id": 1,
                    "name": "",
                    "note": None,
                    "number_of_deposits": 2,
                    "station_name": "Our Station",
                    "total_deposits": 99.0,
                    "total_security": 120.0,
                }
            ]
        }

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json, expected)


class ShareDetailsTests(AuthorizedTest):
    @pytest.mark.usefixtures("app_ctx")
    def test_get_share_details(self):
        share = ShareFactory.create()

        response = self.app.get(f"/api/v1/shares/{share.id}")

        expected = {
            "share": {
                "archived": False,
                "bets": [],
                "difference_today": 0,
                "expected_today": 0,
                "id": 1,
                "name": "",
                "note": None,
                "station_id": 1,
                "total_deposits": 0,
            }
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, expected)

    @pytest.mark.usefixtures("app_ctx")
    def test_get_share_details_404(self):
        response = self.app.get("/api/v1/shares/1337")

        self.assertEqual(response.status_code, 404)

    @pytest.mark.usefixtures("app_ctx")
    def test_patch_share(self):
        original_note = "My little note"
        share = ShareFactory.create(archived=False, note=original_note)

        response = self.app.patch(f"/api/v1/shares/{share.id}", json={"archived": True})

        updated_share = Share.get(share.id)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(updated_share.archived)
        self.assertEqual(updated_share.note, original_note)

    @pytest.mark.usefixtures("app_ctx")
    def test_patch_share_validates_request(self):
        share = ShareFactory.create()

        # `id` is not a field that can be changed
        response = self.app.patch(f"/api/v1/shares/{share.id}", json={"id": 10})

        self.assertEqual(response.status_code, 400)


class BetDetailsTests(AuthorizedTest):
    @pytest.mark.usefixtures("app_ctx")
    def test_delete_bet(self):
        bet = BetFactory.create()
        share = bet.share

        self.assertEqual(db.session.query(Bet).count(), 1)

        response = self.app.delete(f"/api/v1/shares/{share.id}/bets/{bet.id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(db.session.query(Bet).count(), 0)

    @pytest.mark.usefixtures("app_ctx")
    def test_delete_bet_unknown_bet(self):
        bet = BetFactory.create()
        share = bet.share

        self.assertEqual(db.session.query(Bet).count(), 1)

        response = self.app.delete(f"/api/v1/shares/{share.id}/bets/{bet.id + 1}")

        self.assertEqual(response.status_code, 404)

    @pytest.mark.usefixtures("app_ctx")
    def test_post_bet_fails_on_additional_args(self):
        bet = BetFactory.create()

        payload = {
            "value": 99,
            "start_date": bet.start_date,
            "share_id": 12,  # this is not allowed and should trigger a 400
        }

        self.assertEqual(db.session.query(Bet).count(), 1)

        response = self.app.put(f"/api/v1/bets/{bet.id}", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json,
            {
                "validation_error": {
                    "body_params": [
                        {
                            "input": 12,
                            "loc": ["share_id"],
                            "msg": "Extra inputs are not permitted",
                            "type": "extra_forbidden",
                            "url": "https://errors.pydantic.dev/2.5/v/extra_forbidden",
                        }
                    ]
                }
            },
        )

    @pytest.mark.usefixtures("app_ctx")
    def test_create_bet(self):
        share = ShareFactory.create()
        self.assertEqual(db.session.query(Bet).count(), 0)

        response = self.app.post(
            f"/api/v1/shares/{share.id}/bets", json={"value": "99", "start_date": "2019-01-01"}
        )

        bet = db.session.query(Bet).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(db.session.query(Bet).count(), 1)
        self.assertEqual(bet.value, 99)
        self.assertEqual(bet.start_date, date(2019, 1, 1))
        self.assertEqual(bet.end_date, None)

    @pytest.mark.usefixtures("app_ctx")
    def test_edit_bet(self):
        bet = BetFactory.create(value=20)

        payload = {
            "value": 99.50,
            "start_date": bet.start_date.strftime("%Y-%m-%d"),
        }
        response = self.app.put(f"/api/v1/bets/{bet.id}", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(db.session.query(Bet).count(), 1)
        updated_bet = db.session.query(Bet).first()
        self.assertEqual(updated_bet.value, 99.50)
        self.assertEqual(updated_bet.start_date, bet.start_date)
        self.assertEqual(updated_bet.end_date, bet.end_date)


class DepositTest(AuthorizedTest):
    @pytest.mark.usefixtures("app_ctx")
    def test_patch_deposit_success(self):
        deposit = DepositFactory.create(ignore=False)

        response = self.app.patch(f"/api/v1/deposits/{deposit.id}", json={"ignore": True})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["deposit"]["is_security"], False)
        updated_deposit = Deposit.get(deposit.id)
        self.assertTrue(updated_deposit.ignore)
        self.assertIs(updated_deposit.is_security, False)

    @pytest.mark.usefixtures("app_ctx")
    def test_patch_validates_payload(self):
        deposit = DepositFactory.create(ignore=False)

        response = self.app.patch(f"/api/v1/deposits/{deposit.id}", json={"amount": 200})

        self.assertEqual(response.status_code, 400)

    @pytest.mark.usefixtures("app_ctx")
    def test_post_creates_new_entry(self):
        person = PersonFactory.create()

        new_deposit = {
            "amount": 200,
            "title": "Missing Deposit",
            "timestamp": "2022-04-07T00:00:00",
            "person_id": person.id,
        }

        response = self.app.post("/api/v1/deposits/", json=new_deposit)

        self.assertEqual(response.status_code, 200)
        new_deposit = Deposit.get(response.json["deposit"]["id"])
        self.assertEqual(new_deposit.amount, 200)

from solawi.app import db
from test_helpers import DBTest, AuthorizedTest


class AuthorizedViewsTests(AuthorizedTest):
    def test_delete_bet(self):
        from solawi.models import Bet, Share

        share = Share(name="test share")
        share.save()
        bet = Bet(share_id=share.id)
        bet.save()

        self.assertEqual(db.session.query(Bet).count(), 1)

        response = self.app.delete(f"/api/v1/shares/{share.id}/bets/{bet.id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(db.session.query(Bet).count(), 0)

    def test_delete_bet_unkown_bet(self):
        from solawi.models import Bet, Share

        share = Share(name="test share")
        share.save()
        bet = Bet(share_id=share.id)
        bet.save()

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


class UnAuthorizedViewsTests(DBTest):
    def test_delete_bet_required_auth(self):
        from solawi.models import Bet, Share

        share = Share(name="test share")
        share.save()
        bet = Bet(share_id=share.id)
        bet.save()

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

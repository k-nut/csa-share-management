from solawi.app import db
from test_helpers import DBTest


class TestController(DBTest):
    def test_merge_one_way(self):
        from solawi.models import Share
        from solawi.controller import merge

        share_1 = Share(name="With bet")
        share_2 = Share(name="Without bet")

        share_1.save()
        share_2.save()

        assert db.session.query(Share).count() == 2

        merge(share_1.id, share_2.id)

        # assert db.session.query(Share).one().bet_value == 100
        assert db.session.query(Share).count() == 1


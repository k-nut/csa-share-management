from solawi.app import db
from test_factories import ShareFactory
from test_helpers import DBTest


class TestController(DBTest):
    def test_merge_one_way(self):
        from solawi.models import Share
        from solawi.controller import merge

        share_1 = ShareFactory.create()
        share_2 = ShareFactory.create()

        assert db.session.query(Share).count() == 2

        merge(share_1.id, share_2.id)

        # assert db.session.query(Share).one().bet_value == 100
        assert db.session.query(Share).count() == 1


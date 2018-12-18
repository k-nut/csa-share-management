from solawi.app import db
from test_factories import ShareFactory, MemberFactory
from test_helpers import DBTest

from solawi.models import Share
from solawi.controller import merge

class TestController(DBTest):
    def test_merge_one_way(self):
        share1 = ShareFactory.create()
        share2 = ShareFactory.create()

        MemberFactory.create(share=share1)
        MemberFactory.create(share=share2)

        assert db.session.query(Share).count() == 2

        merge(share1.id, share2.id)

        updated_share = db.session.query(Share).first()
        assert db.session.query(Share).count() == 1
        assert len(updated_share.members) == 2

    def test_merge_other_way(self):
        share1 = ShareFactory.create()
        share2 = ShareFactory.create()

        MemberFactory.create(share=share1)
        MemberFactory.create(share=share2)

        assert db.session.query(Share).count() == 2

        merge(share2.id, share1.id)

        updated_share = db.session.query(Share).first()
        assert db.session.query(Share).count() == 1
        assert len(updated_share.members) == 2

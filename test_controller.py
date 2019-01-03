from solawi.app import db
from test_factories import ShareFactory, MemberFactory, BetFactory
from test_helpers import DBTest

from solawi.models import Share, Bet, Member
from solawi.controller import merge


class TestController(DBTest):
    def test_merge_one_way(self):
        share1 = ShareFactory.create()
        share2 = ShareFactory.create()

        MemberFactory.create(share=share1)
        MemberFactory.create(share=share2)
        MemberFactory.create(share=share2)

        BetFactory.create(share=share1)
        BetFactory.create(share=share1)
        BetFactory.create(share=share2)

        assert Share.query.count() == 2
        assert Bet.query.count() == 3

        merge(share1.id, share2.id)

        updated_share = Share.query.one()

        assert Share.query.count() == 1
        assert len(updated_share.members) == 3
        assert len(updated_share.bets) == 3
        assert Member.query.count() == 3
        assert Bet.query.count() == 3

    def test_merge_other_way(self):
        share1 = ShareFactory.create()
        share2 = ShareFactory.create()

        MemberFactory.create(share=share1)
        MemberFactory.create(share=share2)
        MemberFactory.create(share=share2)

        BetFactory.create(share=share1)
        BetFactory.create(share=share1)
        BetFactory.create(share=share2)


        assert Share.query.count() == 2
        assert Bet.query.count() == 3

        merge(share2.id, share1.id)

        updated_share = Share.query.one()

        assert Share.query.count() == 1
        assert len(updated_share.members) == 3
        assert len(updated_share.bets) == 3
        assert Member.query.count() == 3
        assert Bet.query.count() == 3

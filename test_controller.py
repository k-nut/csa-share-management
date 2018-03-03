import unittest
import tempfile
import os

from solawi.app import app, db


class TestController(unittest.TestCase):
    def setUp(self):
        # next line needed so that db.create_all knows what to create
        from solawi.models import Deposit, Share, Person

        self.db_fd, self.temp_filepath = tempfile.mkstemp()
        database_path = 'sqlite:///{}'.format(self.temp_filepath)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_path
        app.config['TESTING'] = True
        self.app = app.test_client()

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        os.close(self.db_fd)
        os.remove(self.temp_filepath)

    def test_merge_one_way(self):
        from solawi.models import Share
        from solawi.controller import merge

        share_1 = Share(name="With bet", bet_value=100.0)
        share_2 = Share(name="Without bet")

        share_1.save()
        share_2.save()

        merge(share_1.id, share_2.id)

        assert db.session.query(Share).one().bet_value == 100
        assert db.session.query(Share).count() == 1

    def test_merge_other_way(self):
        from solawi.models import Share
        from solawi.controller import merge

        share_1 = Share(name="Without bet")
        share_2 = Share(name="With bet", bet_value=100.0)

        share_1.save()
        share_2.save()

        merge(share_1.id, share_2.id)

        assert db.session.query(Share).one().bet_value == 100
        assert db.session.query(Share).count() == 1


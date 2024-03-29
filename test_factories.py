import datetime

import factory

from solawi.app import db
from solawi.models import Bet, Deposit, Member, Person, Share, Station, User


class StationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Station
        sqlalchemy_session = db.session  # the SQLAlchemy session object
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: "Station %d" % n)


class ShareFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Share
        sqlalchemy_session = db.session  # the SQLAlchemy session object
        sqlalchemy_session_persistence = "commit"

    station = factory.SubFactory(StationFactory)


class BetFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Bet
        sqlalchemy_session = db.session  # the SQLAlchemy session object
        sqlalchemy_session_persistence = "commit"

    start_date = datetime.date(2018, 1, 1)
    end_date = None
    share = factory.SubFactory(ShareFactory)
    value = 90


class PersonFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Person
        sqlalchemy_session = db.session  # the SQLAlchemy session object
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("name")
    share = factory.SubFactory(ShareFactory)


class DepositFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Deposit
        sqlalchemy_session = db.session  # the SQLAlchemy session object
        sqlalchemy_session_persistence = "commit"

    amount = 100
    title = "My Deposit Title"
    person = factory.SubFactory(PersonFactory)


class MemberFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Member
        sqlalchemy_session = db.session  # the SQLAlchemy session object
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("name")
    phone = factory.Faker("phone_number")
    email = factory.Faker("safe_email")
    share = factory.SubFactory(ShareFactory)


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session  # the SQLAlchemy session object
        sqlalchemy_session_persistence = "commit"

    email = factory.Faker("safe_email")
    password = factory.Faker("password")
    active = True
    password_changed_at = datetime.date(2016, 1, 1)

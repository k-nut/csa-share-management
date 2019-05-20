""" the models """
import datetime
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import UniqueConstraint, func
from flask_login import UserMixin

from solawi.app import db, app, bcrypt


class BaseModel():
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError as e:
            print("failing")
            print(e)
            db.session.rollback()
            app.logger.debug(e)
            return None
        return self

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()

    @classmethod
    def get(cls, id):
        return db.session.query(cls).get(id)

    @property
    def json(self):
        d = {}
        columns = class_mapper(self.__class__).columns
        for c in columns:
            name = c.name
            d[name] = getattr(self, name)
        return d


class Member(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String)
    name = db.Column(db.String)
    email = db.Column(db.String)
    share_id = db.Column(db.Integer, db.ForeignKey('share.id'))


class Deposit(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    amount = db.Column(db.Numeric)
    timestamp = db.Column(db.DateTime)
    is_security = db.Column(db.Boolean, default=False)
    title = db.Column(db.Text)
    ignore = db.Column(db.Boolean, default=False)
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))


    __table_args__ = (UniqueConstraint('timestamp',
                                       'amount',
                                       'title',
                                       'person_id',
                                       name='_all_fields'),
                      )

    def __repr__(self):
        return '<Deposit %i %r %s>' % (self.amount, self.timestamp, self.person.name)


class Bet(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    value = db.Column(db.Numeric)
    start_date = db.Column(db.DateTime, default=datetime.date(2017, 5, 1))
    end_date = db.Column(db.DateTime)
    share_id = db.Column(db.Integer, db.ForeignKey('share.id'))

    @property
    def currently_active(self):
        return (not self.end_date) or (self.end_date.date() > datetime.date.today())

    @property
    def expected_today(self):
        NEW_PAYMENY_REQUIRED_DAY = 27
        end_date = self.end_date or date.today()
        delta = relativedelta(end_date, self.start_date)
        months = delta.months + delta.years * 12

        if end_date.day >= NEW_PAYMENY_REQUIRED_DAY:
            months += 1

        if datetime.datetime.now() > self.start_date and not self.end_date:
            # if this bet is still active, we expect them to have payed
            # for the following month already
            months += 1

        if self.start_date.day >= 15:
            # If the Bet was started at mid-month, subtract half
            # a month from the expected amount
            months -= Decimal('0.5')

        return months * (self.value or 0)


class Share(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    people = db.relationship('Person',
                             backref="share",
                             cascade="all, delete-orphan")
    bets = db.relationship('Bet',
                           backref="share",
                           cascade="all, delete-orphan")
    members = db.relationship('Member',
                              backref="share",
                              cascade="all, delete-orphan")
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'))
    note = db.Column(db.Text)
    archived = db.Column(db.Boolean, default=False)

    @property
    def json(self):
        bets = [bet.json for bet in self.bets]
        return {
            "id": self.id,
            "name": self.name,
            "archived": self.archived,
            "bets": bets,
            "station_id": self.station_id,
            "note": self.note,
        }

    @property
    def name(self):
        return " & ".join(sorted([member.name for member in self.members]))

    @property
    def join_date(self):
        start_dates = [bet.start_date for bet in self.bets]
        return min(start_dates) if start_dates else None

    @staticmethod
    def get_deposits(share_id):
        res = db.session.query(Deposit, Person.name, Person.id, User.email) \
            .join(Person) \
            .outerjoin(User, User.id == Deposit.added_by) \
            .filter(Person.share_id == share_id) \
            .all()
        result = []
        for deposit, person_name, person_id, adder_email in res:
            result.append(dict(
                id=deposit.id,
                timestamp=deposit.timestamp,
                amount=deposit.amount,
                title=deposit.title,
                added_by_email=adder_email,
                person_id=person_id,
                person_name=person_name,
                ignore=deposit.ignore,
                is_security=deposit.is_security
            ))
        return (result)

    @staticmethod
    def get_bets(share_id):
        res = db.session.query(Bet) \
            .filter(Bet.share_id == share_id) \
            .all()
        return [bet.json for bet in res]

    @property
    def deposits(self):
        deposits = []
        for person in self.people:
            deposits += person.deposits
        return deposits

    @property
    def valid_deposits(self):
        return [deposit for deposit in self.deposits
                if not (deposit.ignore or deposit.is_security)]

    @property
    def station_name(self):
        return self.station.name if self.station else None

    @property
    def total_deposits(self):
        return sum(deposit.amount for deposit in self.valid_deposits)

    @property
    def number_of_deposits(self):
        return len(self.valid_deposits)

    @property
    def expected_today(self):
        return sum([bet.expected_today for bet in self.bets])

    @property
    def currently_active(self):
        return any([bet.currently_active for bet in self.bets])



class Station(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    name = db.Column(db.String(120), unique=True)
    shares = db.relationship('Share', backref='station', lazy='dynamic')

    @staticmethod
    def get_by_name(name):
        return db.session.query(Station).filter_by(name=name).first()


class Person(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    name = db.Column(db.String(120), unique=True)
    share_id = db.Column(db.Integer, db.ForeignKey('share.id'))
    deposits = db.relationship('Deposit',
                               backref='person')

    def __repr__(self):
        string = '<Person %s (id %i)>' % (self.name, self.id)
        return string.encode("utf-8")

    @staticmethod
    def get_or_create(name):
        try:
            exisiting = Person.query.filter_by(name=name).one()
            return exisiting
        except NoResultFound:
            new_person = Person(name=name)
            db.session.add(new_person)
            db.session.commit()
            return new_person


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    _password = db.Column(db.Binary(128), nullable=False)

    def __init__(self, email, password):
        self.email = email.lower()
        self.password = password

    def check_password(self, password):
        return bcrypt.check_password_hash(self._password, password)

    @staticmethod
    def get_all_emails():
        return db.session.query(User.email).all()

    @staticmethod
    def get(id):
        return db.session.query(User).get(id)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)

    @staticmethod
    def authenticate_and_get(email, password):
        email = email.lower()
        user = db.session.query(User).filter(User.email == email).one_or_none()
        if user is not None and user.check_password(password):
            return user
        else:
            return None

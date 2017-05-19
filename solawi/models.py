""" the models """
import datetime

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import UniqueConstraint
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

from solawi import db, app

bcrypt = Bcrypt(app)

class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime)
    is_security = db.Column(db.Boolean)
    title = db.Column(db.Text)
    ignore = db.Column(db.Boolean)

    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    person = db.relationship('Person',
                             backref=db.backref('deposit', lazy='dynamic'))

    __table_args__ = (UniqueConstraint('timestamp',
                                       'amount',
                                       'title',
                                       'person_id',
                                       name='_all_fields'),
                     )

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            app.logger.debug("Skipping existing Deposit for %s", self)

    def __repr__(self):
        return '<Deposit %i %r %s>' % (self.amount, self.timestamp, self.person.name)


class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    name = db.Column(db.String)
    bet_value = db.Column(db.Float)
    people = db.relationship('Person',
                             backref="share",
                             cascade="all, delete-orphan",
                             lazy='dynamic')
    start_date = db.Column(db.DateTime, default=datetime.date(2017, 5, 1))
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'))

    def __init__(self, name, station=None, bet_value=None):
        self.name = name
        if station:
            self.station = station
        if bet_value:
            self.bet_value = bet_value

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            db.session.rollback()

    @property
    def deposits(self):
        deposits = []
        for person in self.people:
            deposits += person.deposits
        return deposits

    @property
    def valid_deposits(self):
        return [deposit for deposit in self.deposits if not deposit.ignore]

    @property
    def start_month(self):
        return self.start_date.month

    @property
    def station_name(self):
        if self.station:
            return self.station.name
        else:
            return ""

    @property
    def total_deposits(self):
        return sum(deposit.amount for deposit in self.valid_deposits)

    def expected_today(self):
        def diff_months(start, today):
            start -= datetime.timedelta(days=30)
            next_month = 0
            if today.day > 24:
                next_month = 1
            return (today.year - start.year)*12 + today.month - start.month + next_month
        today = datetime.date.today()

        start_date = self.start_date or datetime.date(2016, 5, 1)

        number_of_months_expected = diff_months(start_date, today)
        expected = self.bet_value * number_of_months_expected
        return expected

    @property
    def number_of_deposits(self):
        return len(self.valid_deposits)

    @staticmethod
    def set_value_for_id(bet_value, share_id):
        share = Share.query.get(share_id)
        share.bet_value = bet_value
        share.save()

    @staticmethod
    def set_station_for_id(station_id, share_id):
        share = Share.query.get(share_id)
        share.station_id = station_id
        share.save()

    def difference_today(self):
        return self.total_deposits - self.expected_today()


class Station(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    name = db.Column(db.String(120), unique=True)
    shares = db.relationship('Share', backref='station', lazy='dynamic')

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    @staticmethod
    def get_by_name(name):
        return db.session.query(Station).filter_by(name=name).first()


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    name = db.Column(db.String(120), unique=True)
    share_id = db.Column(db.Integer, db.ForeignKey('share.id'))

    def __init__(self, name):
        self.name = name

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    @property
    def deposits(self):
        deposits = Deposit.query.filter_by(person=self).all()
        return deposits


    def __repr__(self):
        string = '<Person %s (id %i)>' % (self.name, self.id)
        return string.encode("utf-8")

    @staticmethod
    def get_or_create(name):
        try:
            exisiting = Person.query.filter_by(name=name).one()
            return exisiting
        except NoResultFound:
            new_person = Person(name)
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
    def get(id):
        print(id)
        return db.session.query(User).get(id)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)

    @staticmethod
    def authenticate_and_get(email, password):
        email = email.lower()
        user = db.session.query(User).filter(User.email==email).one_or_none()
        if user is not None and user.check_password(password):
            return user
        else:
            return None

""" the models """
import datetime

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import UniqueConstraint, func
from flask_login import UserMixin

from solawi.app import db, app, bcrypt


class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    amount = db.Column(db.Numeric)
    timestamp = db.Column(db.DateTime)
    is_security = db.Column(db.Boolean, default=False)
    title = db.Column(db.Text)
    ignore = db.Column(db.Boolean, default=False)

    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    person = db.relationship('Person',
                             backref=db.backref('deposit', lazy='dynamic'))

    __table_args__ = (UniqueConstraint('timestamp',
                                       'amount',
                                       'title',
                                       'person_id',
                                       name='_all_fields'),
                      )

    @staticmethod
    def get(id):
        return db.session.query(Deposit).get(id)

    @property
    def json(self):
        d = {}
        columns = class_mapper(self.__class__).columns
        for c in columns:
            name = c.name
            d[name] = getattr(self, name)
        return d

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            app.logger.debug("Skipping existing Deposit for %s", self)

    def __repr__(self):
        return '<Deposit %i %r %s>' % (self.amount, self.timestamp, self.person.name)


class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    value = db.Column(db.Numeric)
    start_date = db.Column(db.DateTime, default=datetime.date(2017, 5, 1))
    end_date = db.Column(db.DateTime, default=datetime.date(2017, 12, 31))
    share_id = db.Column(db.Integer, db.ForeignKey('share.id'))

    @staticmethod
    def get(id):
        return db.session.query(Bet).get(id)

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()

    def to_json(self):
        return dict(start_date=self.start_date,
                    end_date=self.end_date,
                    value=self.value,
                    id=self.id)


class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    name = db.Column(db.String)
    people = db.relationship('Person',
                             backref="share",
                             cascade="all, delete-orphan",
                             lazy='dynamic')
    bets = db.relationship('Bet',
                           backref="share",
                           cascade="all, delete-orphan")
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'))
    note = db.Column(db.Text)
    archived = db.Column(db.Boolean, default=False)
    email = db.Column(db.String)

    @property
    def json(self):
        bets = [bet.to_json() for bet in self.bets]
        return {
            "id": self.id,
            "name": self.name,
            "archived": self.archived,
            "bets": bets,
            "station_id": self.station_id,
            "note": self.note,
            "email": self.email
        }

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()

    @staticmethod
    def get(share_id):
        return db.session.query(Share).get(share_id)

    @staticmethod
    def get_deposits(share_id):
        res = db.session.query(Deposit, Person.name, Person.id) \
            .join(Person) \
            .filter(Person.share_id == share_id) \
            .all()
        result = []
        for deposit, person_name, person_id in res:
            result.append(dict(
                id=deposit.id,
                timestamp=deposit.timestamp,
                amount=deposit.amount,
                title=deposit.title,
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
        return [bet.to_json() for bet in res]

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

    @property
    def number_of_deposits(self):
        return len(self.valid_deposits)

    @property
    def expected_today(self):
        return db.session.query(func.expected_today(self.id)).one_or_none()[0] or 0


class Station(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    name = db.Column(db.String(120), unique=True)
    shares = db.relationship('Share', backref='station', lazy='dynamic')

    @property
    def json(self):
        return {"name": self.name,
                "id": self.id}

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

    @staticmethod
    def get(person_id):
        return db.session.query(Person).get(person_id)

    @property
    def json(self):
        d = {}
        columns = class_mapper(self.__class__).columns
        for c in columns:
            name = c.name
            d[name] = getattr(self, name)
        return d

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

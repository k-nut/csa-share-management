""" the models """
import datetime

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import UniqueConstraint

from solawi import db, app

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
    start_date = db.Column(db.DateTime, default=datetime.date(2016, 5, 1))

    def __init__(self, name):
        self.name = name

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError:
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

    def difference_today(self):
        return self.total_deposits - self.expected_today()


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


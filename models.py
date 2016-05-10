""" the models """
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
    def total_deposits(self):
        return sum(deposit.amount for deposit in self.deposits)

    def expected_today(self, number_of_months_expected):
        expected = self.bet_value * number_of_months_expected
        return expected

    @property
    def number_of_deposits(self):
        return len(self.deposits)

    @staticmethod
    def set_value_for_id(bet_value, share_id):
        share = Share.query.get(share_id)
        share.bet_value = bet_value
        share.save()

    def difference_today(self, number_of_months_expected):
        return self.total_deposits - self.expected_today(number_of_months_expected)


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


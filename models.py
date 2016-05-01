from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import UniqueConstraint

from solawi import db, app

class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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
            print("Skipping existing Deposit for %s" % self)
            app.logger.debug("Skipping existing Deposit for %s", self)

    def __repr__(self):
        return '<Deposit %i %r %s>' % (self.amount, self.timestamp, self.person.name)


class MonthlyBet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), unique=True)
    person = db.relationship('Person',
        backref=db.backref('monthlybet', lazy='dynamic'))

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            
    @staticmethod
    def set_value_for_id(bet_value, person_id):
        person = Person.query.get(person_id)
        bet = MonthlyBet.query.filter_by(person=person).one()
        bet.value = bet_value
        bet.save()


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)

    def __init__(self, name):
        self.name = name

    @property
    def total_deposits(self):
        return sum(deposit.amount for deposit in self.deposits)

    @property
    def deposits(self):
        deposits = Deposit.query.filter_by(person=self).all()
        return deposits

    @property
    def monthly_bet_value(self):
        monthly_bet = MonthlyBet.query.filter_by(person=self).one()
        return monthly_bet.value

    @property
    def number_of_deposits(self):
        return len(self.deposits)

    def difference_today(self, number_of_months_expected):
        return self.total_deposits - self.expected_today(number_of_months_expected)

    def expected_today(self, number_of_months_expected):
        monthly_bet = MonthlyBet.query.filter_by(person=self).one()
        expected = monthly_bet.value * number_of_months_expected
        return expected

    @staticmethod
    def get_or_create(name):
        try:
            exisiting = Person.query.filter_by(name = name).one()
            return exisiting
        except NoResultFound:
            new_person = Person(name)
            # db.session.add(new_person)
            # db.session.commit()
            return new_person


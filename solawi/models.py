""" the models """
import datetime
from datetime import date
from decimal import Decimal

from sqlalchemy import UniqueConstraint, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.exc import NoResultFound

from solawi.app import app, bcrypt, db


class BaseModel:
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
        except IntegrityError:
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
    share_id = db.Column(db.Integer, db.ForeignKey("share.id"))


class Deposit(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    amount = db.Column(db.Numeric)
    timestamp = db.Column(db.DateTime)
    is_security = db.Column(db.Boolean, default=False)
    title = db.Column(db.Text)
    ignore = db.Column(db.Boolean, default=False)
    added_by = db.Column(db.Integer, db.ForeignKey("user.id"))

    person_id = db.Column(db.Integer, db.ForeignKey("person.id"))

    __table_args__ = (
        UniqueConstraint("timestamp", "amount", "title", "person_id", name="_all_fields"),
    )

    def __repr__(self):
        return "<Deposit %i %r %s>" % (self.amount, self.timestamp, self.person.name)

    @classmethod
    def latest_import(cls):
        return (
            db.session.query(func.max(Deposit.timestamp))
            .filter(Deposit.added_by.is_(None))
            .scalar()
        )


class Bet(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    value = db.Column(db.Numeric, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    share_id = db.Column(db.Integer, db.ForeignKey("share.id"), nullable=False)

    @property
    def currently_active(self):
        return (not self.end_date) or (self.end_date.date() > datetime.date.today())

    def expected_at(self, date):
        if date:
            return db.engine.execute(
                text(
                    """
              SELECT get_expected_today(bet.start_date::date,
                                        bet.end_date::date,
                                        bet.value,
                                        :date
                                       )
              from bet
              where bet.id = :id
              """
                ),
                {"date": date, "id": self.id},
            ).scalar()

        return db.engine.execute(
            text(
                """
          SELECT get_expected_today(bet.start_date::date,
                                    bet.end_date::date,
                                    bet.value
                                   )
          from bet
          where bet.id = :id
          """
            ),
            {"id": self.id},
        ).scalar()

    @property
    def expected_today(self):
        return self.expected_at(None)


class Share(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    people = db.relationship("Person", backref="share", cascade="all, delete-orphan")
    bets = db.relationship("Bet", backref="share", cascade="all, delete-orphan")
    members = db.relationship("Member", backref="share", cascade="all, delete-orphan")
    station_id = db.Column(db.Integer, db.ForeignKey("station.id"))
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
        return " & ".join(sorted(member.name for member in self.members if member.name))

    @property
    def join_date(self):
        start_dates = [bet.start_date for bet in self.bets]
        return min(start_dates) if start_dates else None

    @staticmethod
    def get_deposits(share_id):
        res = (
            db.session.query(Deposit, Person.name, Person.id, User.email)
            .join(Person)
            .outerjoin(User, User.id == Deposit.added_by)
            .filter(Person.share_id == share_id)
            .all()
        )
        result = []
        for deposit, person_name, person_id, adder_email in res:
            result.append(
                dict(
                    id=deposit.id,
                    timestamp=deposit.timestamp,
                    amount=deposit.amount,
                    title=deposit.title,
                    added_by_email=adder_email,
                    person_id=person_id,
                    person_name=person_name,
                    ignore=deposit.ignore,
                    is_security=deposit.is_security,
                )
            )
        return result

    @staticmethod
    def get_bets(share_id):
        res = db.session.query(Bet).filter(Bet.share_id == share_id).all()
        return [bet.json for bet in res]

    @property
    def deposits(self):
        deposits = []
        for person in self.people:
            deposits += person.deposits
        return deposits

    @property
    def valid_deposits(self):
        return [deposit for deposit in self.deposits if not (deposit.ignore or deposit.is_security)]

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
        return sum(bet.expected_today for bet in self.bets)

    @property
    def currently_active(self):
        return any([bet.currently_active for bet in self.bets])

    @staticmethod
    def get_deposit_map() -> dict[int, dict[str, str]]:
        """
        returns a dictionary in the form
        ```
        {
          <share_id>: {
           "total_deposits": <decimal>
           "number_of_deposits": <decimal>
          }
        }
        ```

        The goal of this method is to push these aggregations
        to the database to reduce the amount of data that gets
        transferred between database and client in order to speed
        up the overall performance of the API.
        """
        result = db.engine.execute(
            """
        select person.share_id,
               sum(amount) as total_deposits,
               count(*) as number_of_deposits
        from deposit
        join person on person.id = deposit.person_id
        where not (deposit.is_security or deposit.ignore)
        group by person.share_id
"""
        )
        return {
            row.share_id: {
                "number_of_deposits": row.number_of_deposits,
                "total_deposits": row.total_deposits,
            }
            for row in result
        }

    @staticmethod
    def get_expected_amount_map() -> dict[int, (Decimal or None)]:
        """
        returns a dictionary in the form
        ```
        {
          <share_id>: <decimal>
        }
        ```
        where the dictionary value is the amount of money that we
        expect this share to have paid by today.
        """
        result = db.engine.execute(
            """
        SELECT share_id,
          SUM(
            get_expected_today(bet.start_date::date,
                               bet.end_date::date,
                               bet.value
                               )
          ) as expected_today from bet
        group by share_id;
        """
        )
        return {row.share_id: row.expected_today for row in result}


class Station(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    name = db.Column(db.String(120), unique=True)
    shares = db.relationship("Share", backref="station", lazy="dynamic")

    @staticmethod
    def get_by_name(name):
        return db.session.query(Station).filter_by(name=name).first()


class Person(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=invalid-name
    name = db.Column(db.String(120), unique=True)
    share_id = db.Column(db.Integer, db.ForeignKey("share.id"))
    deposits = db.relationship("Deposit", backref="person")

    def __repr__(self):
        string = "<Person %s (id %i)>" % (self.name, self.id)
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


class User(db.Model, BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    _password = db.Column(db.LargeBinary(128), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    password_changed_at = db.Column(db.Date)

    def __init__(self, email, password, active=True, **kwargs):
        self.email = email.lower()
        self.password = password
        self.active = active

    def check_password(self, password):
        return bcrypt.check_password_hash(self._password, password)

    @property
    def json(self):
        return {
            "email": self.email,
            "active": self.active,
        }

    @staticmethod
    def get_all_emails():
        return db.session.query(User.email).filter(User.active).all()

    @staticmethod
    def get(id):
        return db.session.query(User).get(id)

    @staticmethod
    def get_by_email(email):
        email = email.lower()
        return db.session.query(User).filter(User.email == email).filter(User.active).one_or_none()

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)
        self.password_changed_at = date.today()

    @staticmethod
    def authenticate_and_get(email, password):
        user = User.get_by_email(email)
        if user is not None and user.check_password(password):
            return user
        else:
            return None

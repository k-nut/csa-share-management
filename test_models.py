from decimal import Decimal

from solawi.models import Bet
from test_helpers import DBTest


class ModelTest(DBTest):
    def test_person(self):
        from datetime import date
        from solawi.models import Person, Deposit, Share

        person = Person.get_or_create("Firstname Lastname")

        timestamp = date(2016, 1, 2)
        title = "CSA 123 - June payment for Firstname Lastname and Other One"
        amount = 63.0

        deposit = Deposit(title=title,
                          person=person,
                          amount=amount,
                          timestamp=timestamp)

        deposit.save()

        share = Share(name="Firstname Lastname and Other One")
        share.people.append(person)
        share.save()
        assert share.number_of_deposits == 1
        assert share.total_deposits == 63
        assert len(Deposit.query.all()) == 1

    def test_other(self):
        from solawi.models import Deposit
        assert len(Deposit.query.all()) == 0

    def test_ignore_deposits(self):
        from solawi.models import Person, Deposit, Share
        from datetime import date

        person = Person.get_or_create("Firstname Lastname")

        timestamp = date(2016, 1, 24)
        title = "CSA 123 - February payment for Firstname Lastname and Other One"
        amount = 63.0

        deposit = Deposit(title=title,
                          person=person,
                          amount=amount,
                          timestamp=timestamp)

        deposit.save()

        share = Share(name="Firstname Lastname and Other One")
        share.people.append(person)
        share.save()
        assert share.number_of_deposits == 1
        assert share.total_deposits == 63
        assert len(Deposit.query.all()) == 1

        deposit.ignore = True
        deposit.save()
        assert share.number_of_deposits == 0
        assert share.total_deposits == 0
        assert len(Deposit.query.all()) == 1

    def test_expected_amount_wiht_custom_start_date(self):
        from solawi.models import Person, Deposit, Share
        from datetime import date

        person = Person.get_or_create("Firstname Lastname")

        timestamp = date(2016, 3, 25)
        title = "CSA 123 - March payment for Firstname Lastname and Other One"
        amount = 63.0

        deposit = Deposit(title=title,
                          person=person,
                          amount=amount,
                          timestamp=timestamp)

        deposit.save()

        share = Share(name="Firstname Lastname and Other One")
        share.people.append(person)
        share.save()
        assert share.number_of_deposits == 1
        assert share.total_deposits == 63
        assert len(Deposit.query.all()) == 1

        deposit.ignore = True
        deposit.save()
        assert share.number_of_deposits == 0
        assert share.total_deposits == 0
        assert len(Deposit.query.all()) == 1

    def test_expected_today_full_month(self):
        from solawi.models import Share
        import datetime
        share = Share(name="Good Share")
        share.save()
        bet = Bet(start_date=datetime.date(2017, 1, 1),
                  end_date=datetime.date(2017, 3, 31),
                  value=100,
                  share_id=share.id
                  )
        bet.save()
        assert share.expected_today == 300

    def test_expected_today_is_decimal(self):
        from solawi.models import Share
        import datetime
        share = Share(name="Good Share")
        share.save()
        bet = Bet(start_date=datetime.date(2017, 1, 1),
                  end_date=datetime.date(2017, 3, 31),
                  value=97.17,
                  share_id=share.id
                  )
        bet.save()
        assert share.expected_today == Decimal('291.51')

    def test_expected_today_across_years(self):
        from solawi.models import Share
        import datetime
        share = Share(name="Good Share")
        share.save()
        bet = Bet(start_date=datetime.date(2016, 1, 1),
                  end_date=datetime.date(2017, 3, 31),
                  value=10,
                  share_id=share.id
                  )
        bet.save()
        assert share.expected_today == 150

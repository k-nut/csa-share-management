import datetime

from solawi.commands import _split_deposits
from solawi.models import Deposit, Person
from test_factories import DepositFactory, PersonFactory, ShareFactory
from test_helpers import DBTest, with_app_context


class TestCommands(DBTest):
    @with_app_context
    def test_split_deposits(self):
        # Arrange
        share1 = ShareFactory.create()
        share2 = ShareFactory.create()

        person = PersonFactory.create(share=share1)

        for i in range(10):
            DepositFactory.create(
                amount=10,
                person=person,
                timestamp=datetime.date(2020, 1, 1) + datetime.timedelta(weeks=i),
            )

        self.assertEqual(Deposit.query.filter(Deposit.person_id == person.id).count(), 10)
        self.assertEqual(Person.query.count(), 1)

        # Act
        _split_deposits(person.id, share2.id, "2020-01-28")

        # Assert
        self.assertEqual(Person.query.count(), 2)

        new_virtual_legacy_person = Person.query.filter(Person.id != person.id).one()

        # Old deposits now belong to the legacy person
        self.assertEqual(
            Deposit.query.filter(Deposit.person_id == new_virtual_legacy_person.id).count(), 4
        )
        # Newer deposits still belong to the original person
        self.assertEqual(Deposit.query.filter(Deposit.person_id == person.id).count(), 6)

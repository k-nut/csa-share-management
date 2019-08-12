import logging
import os
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from fints.client import FinTS3PinTanClient

from solawi.models import Person, Deposit, Member, Share


def clean_title(title):
    for word in ["IBAN", "EREF:", "Dauerauftrag-Gutschrift"]:
        if word in title:
            title = title.split(word)[0]
    return title.strip()


def import_fin_ts():
    logging.basicConfig(level=logging.WARN)
    f = FinTS3PinTanClient(
        os.environ.get('CSA_ACCOUNT_BLZ'),
        os.environ.get('CSA_ACCOUNT_USERNAME'),
        os.environ.get('CSA_ACCOUNT_PASSWORD'),
        'https://hbci-pintan.gad.de/cgi-bin/hbciservlet',
        # product_id=os.environ.get('CSA_HBCI_PRODUT_ID', None)
    )

    accounts = f.get_sepa_accounts()

    account = next(account for account in accounts if account.iban==os.environ.get('CSA_ACCOUNT_IBAN'))

    last_data = Deposit.latest_import()
    import_start = last_data - relativedelta(days=2)

    print(f"Latest import is from {last_data}, importing from {import_start}")

    for transaction in f.get_transactions(account, import_start):
        title = transaction.data.get('purpose')
        name = transaction.data.get('applicant_name')
        date = transaction.data.get('date')
        amount = transaction.data.get('amount')
        value = Decimal(amount.amount)

        if value > 0:
            person = Person.get_or_create(name)
            deposit = Deposit(amount=value,
                              timestamp=date,
                              person=person,
                              title=clean_title(title))
            deposit.save()

            if person.share_id is None:
                member = Member(name=name)
                member.save()

                share = Share()
                share.people.append(person)
                share.members.append(member)
                share.save()


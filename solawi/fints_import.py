import logging
import os
from decimal import Decimal
from typing import Optional

from dateutil.relativedelta import relativedelta
from fints.client import (
    FinTS3PinTanClient,
    FinTSClientMode,
    NeedTANResponse,
)
from fints.utils import minimal_interactive_cli_bootstrap

from solawi.models import Deposit, Member, Person, Share


def clean_title(title: Optional[str]):
    if title is None:
        return None
    for word in ["IBAN", "EREF:", "Dauerauftrag-Gutschrift"]:
        if word in title:
            title = title.split(word)[0]
    return title.strip()


def import_fin_ts(is_interactive):
    logging.basicConfig(level=logging.WARN)
    f = FinTS3PinTanClient(
        os.environ.get("CSA_ACCOUNT_BLZ"),
        os.environ.get("CSA_ACCOUNT_USERNAME"),
        os.environ.get("CSA_ACCOUNT_PASSWORD"),
        os.environ.get("CSA_HBCI_ADDRESS"),
        mode=FinTSClientMode.INTERACTIVE,
        product_id=os.environ.get("CSA_HBCI_PRODUCT_ID", None),
    )
    f.fetch_tan_mechanisms()
    minimal_interactive_cli_bootstrap(f)

    with f:
        if f.init_tan_response:
            if not is_interactive:
                raise Exception("Bank requires a TAN but the session is non-interactive")
            print(f.init_tan_response.challenge)
            tan = input("Please enter TAN:")
            f.send_tan(f.init_tan_response, tan)

        res = get_new_transactions(f)

        while isinstance(res, NeedTANResponse):
            print(res.challenge)

            tan = input("Please enter TAN:")
            res = f.send_tan(res, tan)

        print("No more challenges to complete")

        for transaction in res:
            save_transaction(transaction)
        print(f"Imported {len(res)} transactions")
        if is_interactive:
            print("Press Enter to close the window")
            input()


def get_new_transactions(f):
    accounts = f.get_sepa_accounts()
    account = next(
        account for account in accounts if account.iban == os.environ.get("CSA_ACCOUNT_IBAN")
    )
    last_data = Deposit.latest_import()
    import_start = last_data - relativedelta(days=2)
    print(f"Latest import is from {last_data}, importing from {import_start}")
    res = f.get_transactions(account, import_start)
    return res


def save_transaction(transaction):
    title = transaction.data.get("purpose")
    name = transaction.data.get("applicant_name")
    date = transaction.data.get("date")
    amount = transaction.data.get("amount")
    value = Decimal(amount.amount)
    if value > 0:
        person = Person.get_or_create(name)
        deposit = Deposit(amount=value, timestamp=date, person=person, title=clean_title(title))
        deposit.save()

        if person.share_id is None:
            member = Member(name=name)
            member.save()

            share = Share()
            share.people.append(person)
            share.members.append(member)
            share.save()

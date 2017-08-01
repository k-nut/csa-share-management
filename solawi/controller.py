import csv
from datetime import datetime

from solawi import models
from solawi.models import Share


def merge(first_share_id, second_share_id):
    if not first_share_id or not second_share_id:
        return None

    first_share = Share.query.get(first_share_id)
    second_share = Share.query.get(second_share_id)

    if first_share.bet_value and not second_share.bet_value:
        merge_into = first_share
        take_from = second_share
    else:
        merge_into = second_share
        take_from = first_share
    for person in take_from.people:
        merge_into.people.append(person)

    merge_into.save()
    take_from.delete()
    return merge_into.id


def get_data(filepath):
    with open(filepath) as infile:
        content = csv.DictReader(infile, delimiter=";")
        return [line for line in content]


def import_deposits(data):
    for line in data:
        value = float(line["Betrag"].replace(".", "").replace(",", "."))
        date = datetime.strptime(line["Buchungstag"], "%d.%m.%Y")
        keys = ["VWZ%i" % i for i in range(1, 15)]
        title = "".join([line[key] for key in keys])
        name = line["Auftraggeber/Empf\xe4nger"]
        if value > 0:
            person = models.Person.get_or_create(name)
            deposit = models.Deposit(amount=value,
                                     timestamp=date,
                                     person=person,
                                     title=title)
            deposit.save()

            if person.share_id is None:
                share = Share(person.name)
                share.people.append(person)
                share.bet_value = 0
                share.save()

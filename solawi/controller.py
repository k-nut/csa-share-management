import csv
from datetime import datetime

from solawi.models import Share, Member, Person, Deposit


def without_nones(listlike):
    return [element for element in listlike if element is not None]


def merge(first_share_id, second_share_id):
    if not first_share_id or not second_share_id:
        return None

    first_share = Share.query.get(first_share_id)
    second_share = Share.query.get(second_share_id)

    first_share.people += list(second_share.people)
    first_share.members += list(second_share.members)
    first_share.bets += list(second_share.bets)
    first_share.station_id = first_share.station_id or second_share.station_id
    first_share.note = " \n --- \n ".join(without_nones([first_share.note, second_share.note]))

    first_share.save()
    second_share.delete()
    return first_share.id


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
            person = Person.get_or_create(name)
            deposit = Deposit(amount=value,
                                     timestamp=date,
                                     person=person,
                                     title=title)
            deposit.save()

            if person.share_id is None:
                member = Member(name=name)
                member.save()

                share = Share()
                share.people.append(person)
                share.members.append(member)
                share.save()

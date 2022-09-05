from solawi.app import db
from solawi.models import Share


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

    db.session.add(first_share)
    db.session.delete(second_share)
    db.session.commit()
    return first_share.id

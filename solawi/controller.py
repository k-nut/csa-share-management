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
import csv

import datetime
from flask import request, jsonify, Blueprint
from flask_login import login_user, logout_user, login_required

from solawi import models
from solawi.controller import merge, import_deposits
from solawi.models import Share, Deposit, Person

from solawi.app import app, db
from solawi.old_app import allowed_file

api = Blueprint('api', __name__)


def expected_today(share):
    def diff_months(start, today):
        start -= datetime.timedelta(days=30)
        next_month = 0
        if today.day > 24:
            next_month = 1
        return (today.year - start.year) * 12 + today.month - start.month + next_month

    today = datetime.date.today()

    number_of_months_expected = diff_months(share.start_date, today)
    expected = share.bet_value * number_of_months_expected
    return expected

@api.route("/login", methods=["POST"])
def api_login():
    email = request.json.get('email')
    password = request.json.get('password')
    user = models.User.authenticate_and_get(email, password)
    if user:
        login_user(user)
        return jsonify({"message": "login successful"})
    else:
        return jsonify({"message": "login failed"}), 401


@api.route("/logout")
def api_logout():
    logout_user()
    return jsonify({"message": "logout successful"}), 200


@api.route("/shares")
@login_required
def shares_list():
    shares = [share.json for share in Share.query.all()]
    return jsonify(shares=shares)


@api.route("/shares/payment_status", methods=["GET"])
@login_required
def get_payment_list():
    query = """
SELECT share.id,
       share.name,
       sum(
        CASE WHEN (NOT deposit.is_security OR deposit.is_security IS NULL)
              AND (NOT deposit.ignore OR deposit.ignore IS NULL)
              THEN amount
              ELSE 0 END
       ) AS total_deposits, 
       count(deposit.amount) filter (where
                                    (NOT deposit.ignore OR deposit.ignore IS NULL) 
                                    AND (NOT deposit.ignore OR deposit.ignore IS NULL))
       AS number_of_deposits,
       station.name AS station_name,
       share.bet_value,
       share.start_date,
       share.archived
FROM share 
LEFT JOIN person ON share.id = person.share_id
LEFT JOIN deposit ON deposit.person_id = person.id
LEFT JOIN station ON share.station_id = station.id
GROUP BY share.id, station.name, share.bet_value, share.start_date, share.name, share.archived
    """
    result = db.engine.execute(query)
    res = []
    for share in result:
        dict_share = dict(share)
        dict_share['expected_today'] = expected_today(share)
        dict_share['total_deposits'] = share.total_deposits or 0
        dict_share['difference_today'] = - (dict_share['expected_today'] - dict_share['total_deposits'])
        res.append(dict_share)
    return jsonify(shares=res)


@api.route("/stations")
@login_required
def bets_list():
    stations = [station.json for station in models.Station.query.all()]
    return jsonify(stations=stations)


@api.route("/shares/<int:share_id>", methods=["GET"])
@login_required
def shares_details(share_id):
    share = Share.get(share_id)
    resp = share.json
    resp['deposits'] = [deposit.json for deposit in share.deposits]
    return jsonify(share=resp)


@api.route("/shares/<int:share_id>", methods=["POST"])
@login_required
def post_shares_details(share_id):
    share = Share.get(share_id)
    json = request.get_json()
    for field in ["bet_value", "start_date", "station_id", "note", "email", "archived"]:
        if field in json:
            setattr(share, field, json.get(field))
    share.save()
    resp = share.json
    return jsonify(share=resp)


@api.route("/deposits/<int:deposit_id>", methods=["POST"])
@login_required
def post_deposit(deposit_id):
    deposit = Deposit.get(deposit_id)
    json = request.get_json()
    json.pop("id")
    for field in json:
        setattr(deposit, field, json.get(field))
    deposit.save()
    return jsonify(deposit=deposit.json)


@api.route("/deposits/", methods=["PUT"])
@login_required
def put_deposit():
    deposit = Deposit()
    json = request.get_json()
    json.pop("id", None)
    for field in json:
        setattr(deposit, field, json.get(field))
    deposit.save()
    return jsonify(deposit=deposit.json)


@api.route("/shares/merge", methods=["POST"])
@login_required
def merge_shares():
    json = request.get_json()
    share1 = json.get("share1")
    share2 = json.get("share2")
    if not share1 or not share2:
        return jsonify(message='You need to supply share1 and share2'), 400
    merge(share1, share2)
    return jsonify(message='success')


@api.route("/deposits/upload", methods=["POST"])
@login_required
def upload_file():
    sent_file = request.files['file']
    if sent_file and allowed_file(sent_file.filename):
        decoded = [a.decode("windows-1252") for a in sent_file.readlines()]
        content = csv.DictReader(decoded, delimiter=";")
        import_deposits([line for line in content])
        return jsonify(message='success!')


@api.route("/person/<int:person_id>", methods=["GET"])
@login_required
def get_person(person_id):
    return jsonify(Person.get(person_id).json)

app.register_blueprint(api, url_prefix='/api/v1')

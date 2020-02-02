import csv
from http import HTTPStatus

from decimal import Decimal
from flask import request, jsonify, Blueprint
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload

from solawi import models
from solawi.controller import merge, import_deposits
from solawi.models import Share, Deposit, Person, User, Bet, Member

from solawi.app import app, db

api = Blueprint('api', __name__)


@api.route("/login", methods=["POST"])
def api_login():
    email = request.json.get('email')
    password = request.json.get('password')
    user = models.User.authenticate_and_get(email, password)
    if user:
        access_token = create_access_token(identity=email)
        return jsonify(access_token=access_token, id=user.id), 200
    else:
        return jsonify({"message": "login failed"}), 401


@api.route("/shares")
@jwt_required
def shares_list():
    shares = Share.query \
        .options(joinedload(Share.bets)) \
        .options(joinedload(Share.members)) \
        .all()
    shares = [share.json for share in shares]
    return jsonify(shares=shares)


@api.route("/shares/<int:share_id>/emails")
@jwt_required
def share_email_list(share_id):
    share = Share.get(share_id)
    return jsonify(emails=[member.email for member in share.members])


@api.route("/members", methods=["GET"])
@jwt_required
def member_list():
    members = db.session.query(Member)\
        .options(joinedload(Member.share)) \
        .all()
    result = []

    if request.args.get('active'):
        members = [member for member in members if member.share.currently_active]

    for member in members:
        json = member.json
        json['station_name'] = member.share.station_name if member.share else ""
        json['join_date'] = member.share.join_date if member.share else ""
        result.append(json)
    return jsonify(members=result)


@api.route("/members", methods=["POST"])
@jwt_required
def member_create():
    json = request.get_json()
    share_id = json.get("share_id")
    if not share_id:
        share = Share()
        share.save()
        share_id = share.id
    member = Member(name=json.get("name"),
                    email=json.get("email"),
                    phone=json.get("phone"),
                    share_id=share_id)
    member.save()
    return jsonify(member=member.json)


@api.route("/members/<int:member_id>", methods=["PUT", "PATCH"])
@jwt_required
def member_edit(member_id):
    member = Member.get(member_id)
    json = request.get_json()
    for field in ["name", "share_id", "email", "phone"]:
        if field in json:
            setattr(member, field, json.get(field))
    member.save()
    return jsonify(member=member.json)


@api.route("/members/<int:member_id>", methods=["DELETE"])
@jwt_required
def member_delete(member_id):
    member = Member.get(member_id)
    member.delete()
    return "", HTTPStatus.NO_CONTENT


@api.route("/shares/payment_status", methods=["GET"])
@jwt_required
def get_payment_list():
    shares = db.session.query(Share).options(joinedload(Share.members)) \
        .options(joinedload(Share.bets)) \
        .options(joinedload(Share.people)) \
        .options(joinedload(Share.people, Person.deposits)) \
        .options(joinedload(Share.station)) \
        .all()
    res = []
    for share in shares:
        share_payments = {
            'id': share.id,
            'name': share.name,
            'total_deposits': share.total_deposits,
            'number_of_deposits': share.number_of_deposits,
            'archived': share.archived,
            'note': share.note,
            'station_name': share.station.name if share.station else "",
            'expected_today': share.expected_today,
        }
        share_payments['difference_today'] = - (
                    Decimal(share_payments['expected_today'] or 0) - share_payments['total_deposits'])
        res.append(share_payments)
    return jsonify(shares=res)


@api.route("/stations")
@jwt_required
def bets_list():
    stations = [station.json for station in models.Station.query.all()]
    return jsonify(stations=stations)


@api.route("/shares/<int:share_id>", methods=["GET"])
@jwt_required
def shares_details(share_id):
    share = Share.get(share_id)
    dict_share = share.json
    dict_share['expected_today'] = share.expected_today
    dict_share['total_deposits'] = share.total_deposits or 0
    dict_share['difference_today'] = - (Decimal(dict_share['expected_today']) - dict_share['total_deposits'])
    return jsonify(share=dict_share)


@api.route("/shares/<int:share_id>/deposits", methods=["GET"])
@jwt_required
def share_deposits(share_id):
    deposits = Share.get_deposits(share_id)
    return jsonify(deposits=deposits)


@api.route("/shares/<int:share_id>/bets", methods=["GET"])
@jwt_required
def share_bets(share_id):
    bets = Share.get_bets(share_id)
    return jsonify(bets=bets)


@api.route("/shares/<int:share_id>/bets", methods=["POST", "PUT"])
@jwt_required
def bet_details(share_id):
    json = request.get_json()
    if json.get("id"):
        bet = Bet.get(json["id"])
    else:
        bet = Bet()
        bet.share_id = share_id

    for field in ["value", "start_date", "end_date"]:
        if field in json:
            setattr(bet, field, json.get(field))
    bet.save()

    return jsonify(bet=bet.json)


@api.route("/shares/<int:share_id>/bets/<int:bet_id>", methods=["DELETE"])
@jwt_required
def delete_bet(share_id, bet_id):
    bet = Bet.query.get_or_404(bet_id)
    bet.delete()
    return jsonify(), 204


@api.route("/shares/<int:share_id>", methods=["POST"])
@jwt_required
def post_shares_details(share_id):
    share = Share.get(share_id)
    json = request.get_json()
    for field in ["station_id", "note", "archived"]:
        if field in json:
            setattr(share, field, json.get(field))
    share.save()
    resp = share.json
    return jsonify(share=resp)


@api.route("/shares", methods=["POST"])
@jwt_required
def add_share():
    json = request.get_json()
    share = Share()
    for field in json:
        setattr(share, field, json.get(field))
    share.save()
    return jsonify(share=share.json), 201


@api.route("/deposits/<int:deposit_id>", methods=["POST"])
@jwt_required
def post_deposit(deposit_id):
    deposit = Deposit.get(deposit_id)
    json = request.get_json()
    json.pop("id")
    for field in json:
        setattr(deposit, field, json.get(field))
    deposit.save()
    return jsonify(deposit=deposit.json)


@api.route("/deposits/", methods=["PUT"])
@jwt_required
def put_deposit():
    current_user_email = get_jwt_identity()
    current_user = User.query.filter(User.email == current_user_email).one()
    deposit = Deposit(added_by=current_user.id)
    json = request.get_json()
    json.pop("id", None)
    for field in json:
        setattr(deposit, field, json.get(field))
    deposit.save()
    return jsonify(deposit=deposit.json)


@api.route("/shares/merge", methods=["POST"])
@jwt_required
def merge_shares():
    json = request.get_json()
    share1 = json.get("share1")
    share2 = json.get("share2")
    if not share1 or not share2:
        return jsonify(message='You need to supply share1 and share2'), 400
    merge(share1, share2)
    return jsonify(message='success')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ['csv', 'CSV']


@api.route("/deposits/upload", methods=["POST"])
@jwt_required
def upload_file():
    sent_file = request.files['file']
    if sent_file and allowed_file(sent_file.filename):
        decoded = [a.decode("windows-1252") for a in sent_file.readlines()]
        content = csv.DictReader(decoded, delimiter=";")
        import_deposits([line for line in content])
        return jsonify(message='success!')


@api.route("/person/<int:person_id>", methods=["GET"])
@jwt_required
def get_person(person_id):
    return jsonify(Person.get(person_id).json)


@api.route("/users", methods=["GET"])
@jwt_required
def user_list():
    users = User.get_all_emails()
    return jsonify(users=users)


@api.route("/users/<int:id>", methods=["PATCH"])
@jwt_required
def modify_user(id):
    user = User.get(id)

    payload = request.get_json()
    if not payload or not payload.get("password"):
        return jsonify({"message": "json body must contain password field"}), 400

    current_user_email = get_jwt_identity()
    if not user.email == current_user_email:
        return jsonify({"message": "you cannot change another users's password"}), 403

    user.password = payload.get("password")
    user.save()
    return jsonify(user=user.json)


app.register_blueprint(api, url_prefix='/api/v1')

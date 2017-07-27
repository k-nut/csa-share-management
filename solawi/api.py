from flask import request, jsonify, Blueprint
from flask_login import login_user, logout_user, login_required

from solawi import models
from solawi.models import Share, Deposit

from solawi.app import app
api = Blueprint('api', __name__)


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
    for field in ["bet_value", "start_date", "station_id", "note", "email"]:
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

app.register_blueprint(api, url_prefix='/api/v1')

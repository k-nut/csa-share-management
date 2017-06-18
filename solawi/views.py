""" The views """
from datetime import datetime
import csv
import locale

from flask import render_template, request, redirect, url_for, abort, Response
from flask_login import LoginManager, login_required, login_user, logout_user

from solawi import app
from solawi.models import Share, Deposit
import solawi.models as models

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = models.User.authenticate_and_get(email, password)
        if user:
            login_user(user)
            return redirect(request.args.get("next"))
        else:
            return abort(401)
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=email>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')


@app.route("/")
@login_required
def index():
    shares = Share.query.all()
    return render_template("index.html", shares=shares)


@app.route("/share/<int:share_id>/rename", methods=["POST"])
@login_required
def rename_share(share_id):
    share = Share.query.get(share_id)
    new_name = request.form.get('name')
    if new_name:
        share.name = new_name
        share.save()
    return redirect(url_for('share_details', share_id=share_id))


@app.route("/share/<int:share_id>")
@login_required
def share_details(share_id):
    share = Share.query.get(share_id)
    all_shares = Share.query.all()
    for a_share in all_shares:
        if a_share.id == share.id:
            all_shares.remove(a_share)
            break

    return render_template("share_details.html",
                           share=share,
                           all_shares=all_shares)


@app.route("/deposit/<int:deposit_id>/ignore")
@login_required
def ignore_deposit(deposit_id):
    deposit = Deposit.query.get(deposit_id)
    deposit.ignore = not deposit.ignore
    deposit.save()

    share_for_deposit = deposit.person.share_id
    return redirect(url_for('share_details', share_id=share_for_deposit))


@app.route("/merge_shares", methods=["POST"])
@login_required
def merge_shares():
    if request.method == 'POST':
        original_share_id = request.form.get("original_share")
        merge_share_id = request.form.get("merge_share")
        if not original_share_id or not merge_share_id:
            return redirect(url_for('index'))

        original_share = Share.query.get(original_share_id)
        merge_share = Share.query.get(merge_share_id)
        for person in merge_share.people:
            original_share.people.append(person)
        original_share.save()
        merge_share.delete()
        return redirect(url_for('share_details', share_id=original_share_id))
    else:
        return redirect(url_for('index'))


@app.route("/person/<int:person_id>")
@login_required
def person_details(person_id):
    person = models.Person.query.get(person_id)
    return render_template("details.html", person=person)


@app.route("/bets", methods=["GET", "POST"])
@login_required
def bets_overview():
    if request.method == 'POST':
        all_keys = [k for k in request.form.keys()]
        value_keys = [k for k in all_keys if k.startswith('value')]
        month_keys = [k for k in all_keys if k.startswith('month')]
        station_keys = [k for k in all_keys if k.startswith('station')]

        for share_id in value_keys:
            value = request.form[share_id]
            Share.set_value_for_id(value, share_id.split("-")[1])

        for share_id in station_keys:
            station_id = request.form[share_id]
            if station_id != "None":
                Share.set_station_for_id(station_id, share_id.split("-")[1])

        for share_id in month_keys:
            month = int(request.form[share_id])
            share = Share.query.get(share_id.split("-")[1])
            share.start_date = datetime(2017, month, 1)
            share.save()

        return redirect(url_for('bets_overview'))
    else:
        shares = Share.query.all()
        stations = models.Station.query.all()
        return render_template("bets.html", shares=shares, stations=stations)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ['csv', 'CSV']


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        sent_file = request.files['file']
        if sent_file and allowed_file(sent_file.filename):
            decoded = [a.decode("windows-1252") for a in sent_file.readlines()]
            content = csv.DictReader(decoded, delimiter=";")
            import_deposits([line for line in content])
            return redirect(url_for('index'))
    return render_template("upload.html")


def get_data(filepath):
    with open(filepath) as infile:
        content = csv.DictReader(infile, delimiter=";")
        return [line for line in content]


def import_deposits(data):
    for line in data:
        locale.setlocale(locale.LC_NUMERIC, "de_DE.UTF-8")
        print(line["Betrag"])
        value = locale.atof(line["Betrag"].replace(".", ""))
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


@app.errorhandler(401)
def unauthorized(_):
    return Response('<p>Login failed</p>')


@login_manager.user_loader
def load_user(user_id):
    return models.User.get(user_id)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == "__main__":
    app.debug = True
    app.run()

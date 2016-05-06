""" The views """
from datetime import datetime
import csv
import locale

from flask import render_template, request, redirect, url_for

from solawi import app
from models import MonthlyBet
import models


@app.route("/")
def index():
    people = models.Person.query.all()
    return render_template("index.html", people=people)

@app.route("/person/<int:person_id>")
def person_details(person_id):
    person = models.Person.query.get(person_id)
    return render_template("details.html", person=person)

@app.route("/bets", methods=["GET", "POST"])
def bets_overview():
    if request.method == 'POST':
        for key in request.form.keys():
            print key, request.form[key]
            MonthlyBet.set_value_for_id(request.form[key], key)
        return redirect(url_for('bets_overview'))
    else:
        people = models.Person.query.all()
        return render_template("bets.html", people=people)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ['csv', 'CSV']

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            content = csv.DictReader(file.stream, delimiter=";")
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
        value = locale.atof(line["Betrag"])
        date = datetime.strptime(line["Buchungstag"], "%d.%m.%Y")
        keys = ["VWZ%i" % i for i in range(1, 15)]
        title = ("".join([line[key] for key in keys])).decode("iso-8859-3")
        name = line["Auftraggeber/Empf\xe4nger"].decode("iso-8859-3")
        if value > 0:
            person = models.Person.get_or_create(name)
            deposit = models.Deposit(amount=value,
                                     timestamp=date,
                                     person=person,
                                     title=title)
            deposit.save()


if __name__ == "__main__":
    app.debug = True
    app.run()

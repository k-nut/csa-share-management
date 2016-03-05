from datetime import datetime
import csv
import locale

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

from solawi import app, db
import models


@app.route("/")
def index():
    people = models.Person.query.all()
    return render_template("index.html", people=people)

@app.route("/person/<int:person_id>")
def person_details(person_id):
    person = models.Person.query.get(person_id)
    return render_template("details.html", person=person)


def get_data(filepath):
    with open(filepath) as infile:
        content = csv.DictReader(infile, delimiter=";")
        return [line for line in content]


def import_deposits():
    data = get_data("/home/knut/Downloads/Umsaetze_01012016_bis_04032016_KTO35281500_04032016.csv")
    for line in data:
        locale.setlocale(locale.LC_NUMERIC, "de_DE.UTF-8")
        value = locale.atof(line["Betrag"])
        date = datetime.strptime(line["Buchungstag"], "%d.%m.%Y")
        keys = ["VWZ%i" % i for i in range(1,15)]
        title = ("".join([line[key] for key in keys])).decode("iso-8859-3")
        name = line["Auftraggeber/Empf\xe4nger"].decode("iso-8859-3")
        if value > 0:
            person = models.Person.get_or_create(name)
            deposit = models.Deposit(amount=value,
                                     timestamp=date,
                                     person=person,
                                     title=title)
            deposit.save()

def print_sums():
    people = models.Person.query.all()
    for person in people:
        difference = person.difference_today(2)
        if difference < 0:
            print person.name.encode("utf-8"), person.total_deposits, person.number_of_deposits
            print difference
            print "----"

def fake_deposits():
    people = models.Person.query.all()
    for person in people:
        bet = models.MonthlyBet(value=63,
                                person=person)
        bet.save()


if __name__ == "__main__":
    app.debug = True
    app.run()

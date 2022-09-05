from getpass import getpass

import click

from solawi.app import app, db
from solawi.fints_import import import_fin_ts
from solawi.models import User, Person, Deposit, Share


@app.cli.command()
@click.argument("email")
@click.password_option()
def createuser(email, password):
    """Create a new user"""
    user = User(email, password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Made user with address {user.email}")


@app.cli.command()
@click.argument("email")
def change_password(email):
    """Change a user's password"""
    user = User.get_by_email(email)
    if not user:
        raise click.UsageError(f'No user found for e-mail "{email}"')
    user.password = getpass()
    user.save()
    click.echo(f"Updated user {user}")


@app.cli.command()
@click.option("--interactive/--non-interactive", default=False)
def import_statements(interactive):
    import_fin_ts(interactive)


@app.cli.command()
@click.argument("person_id")
@click.argument("share_id")
@click.argument("date")
def split_deposits(person_id, share_id, date):
    """Takes deposits of a given person and creates a new virtual person where
       all deposits made before `date` are assigned to this person.
       The existing person is then assigned to deposit into `share_id`.
       This is to be used in case a person switches their share but continues to deposit money.
       """

    person = Person.get(person_id)

    virtual_person = Person(name=person.name + " [alt - vom Kontotool erstellt]", share_id=person.share_id)
    db.session.add(virtual_person)

    person.share_id = share_id
    db.session.add(person)

    deposits = Deposit.query\
        .filter(Deposit.person_id == person_id)\
        .filter(Deposit.timestamp < date)\
        .all()

    for deposit in deposits:
        deposit.person_id = virtual_person.id
        db.session.add(deposit)

    newly_assigned_share = Share.get(share_id)
    moved_deposits = Deposit.query.filter(Deposit.person_id == person.id).count()

    db.session.commit()
    click.echo(f"Moved {len(deposits)} deposits to new person with ID {virtual_person.id}."
               f" The existing person {person.name} ({person.id}) now deposits into account {newly_assigned_share.name}"
               f" and brought {moved_deposits} deposits with them.")

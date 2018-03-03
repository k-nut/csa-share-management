import click

from solawi.app import app, db
from solawi.models import User


@app.cli.command()
@click.argument('email')
@click.argument('password')
def createuser(email, password):
    """Create a new user"""
    user = User(email, password)
    db.session.add(user)
    db.session.commit()
    click.echo("Made user with address {}".format(user.email))
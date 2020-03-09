import click

from solawi.app import app, db
from solawi.models import User
from solawi.fints_import import import_fin_ts


@app.cli.command()
@click.argument('email')
@click.argument('password')
def createuser(email, password):
    """Create a new user"""
    user = User(email, password)
    db.session.add(user)
    db.session.commit()
    click.echo("Made user with address {}".format(user.email))


@app.cli.command()
@click.option('--interactive/--non-interactive', default=False)
def import_statements(interactive):
    import_fin_ts(interactive)

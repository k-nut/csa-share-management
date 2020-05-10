import click
from getpass import getpass

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
@click.argument('email')
def change_password(email):
    """Change a user's password"""
    user = User.get_by_email(email)
    if not user:
        raise click.UsageError("No user found for e-mail \"{}\"".format(email))
    user.password = getpass()
    user.save()
    click.echo("Updated user {}".format(user))


@app.cli.command()
@click.option('--interactive/--non-interactive', default=False)
def import_statements(interactive):
    import_fin_ts(interactive)

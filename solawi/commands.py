from getpass import getpass

import click

from solawi.app import app, db
from solawi.fints_import import import_fin_ts
from solawi.models import User


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

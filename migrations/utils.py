from pathlib import Path

from sqlalchemy import text


def get_sql(filename):
    path = Path(__file__).parent.joinpath('./sql').joinpath(filename).resolve()
    with open(path) as sql:
        return text(sql.read())
from pathlib import Path


def get_sql(filename):
    path = Path(__file__).parent.joinpath('./sql').joinpath(filename).resolve()
    with open(path) as sql:
        return sql.read()
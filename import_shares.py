import csv
import os

import click

from solawi.models import Share, Station

@click.command()
@click.argument('path', type=click.Path(exists=True))
def main(path):
    """ Reads all csv files in given path and creates `Share` entries
        in the database for them
    """
    files = os.listdir(path)
    for file in files:
        fullpath = os.path.join(path, file)
        with open(fullpath) as infile:
            data = csv.reader(infile, delimiter=';')
            next(data) # skip header
            for line in data:
                value = line[-1]
                station = line[-2]
                name = " & ".join([name for name in line[:-2] if name])

                db_station = Station.get_by_name(station)
                if db_station is None:
                    new_station = Station(name=station)
                    new_station.save()
                    db_station = new_station

                share = Share(name=name,
                              station=db_station,
                              bet_value=float(value.replace(",", ".")))
                share.save()

                print(value, station, name)


if __name__ == '__main__':
    main()

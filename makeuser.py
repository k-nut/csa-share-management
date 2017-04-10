#!/usr/bin/python

import sys

from solawi.models import User, db

u = User(sys.argv[1], sys.argv[2])
db.session.add(u)
db.session.commit()
print("Made user with address {}".format(u.email))
from solawi import db, user_datastore

user_datastore.create_user(email='knut@k-nut.eu', password='ganzgeheim')
db.session.commit()
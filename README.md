# CSA Share Management [![Build Status](https://travis-ci.org/k-nut/csa-share-management.svg?branch=master)](https://travis-ci.org/k-nut/csa-share-management)

Internal tool at our CSA (Community supported agriculture) group that helps manage finances.

## Setup
Make sure that all required environment variables are set.

mainly:
```
FLASK_APP=solawi/app.py
DATABASE_URL=postgres://<your_postgres_settings>
```

## Creating db/running migrations

```bash
flask db upgrade
```

## Creating users

```bash
flask createuser <email> <password>
```

## Running
```bash
flask run
```


## Testing

```bash
py.test test_*.py
```

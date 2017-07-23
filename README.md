# CSA Share Management

Internal tool at our CSA (Community supported agriculture) group that helps manage finances.

## Creating db/running migrations

```bash
DATABASE_URL=<postgres_path> python manage.py db upgrade
# eg. DATABASE_URL=postgres://postgres@0.0.0.0:32768  python manage.py db upgrade

```

## Running
```bash
DATABASE_URL=<postgres_path> python manage.py runserver
# eg. DATABASE_URL=postgres://postgres@0.0.0.0:32768 python manage.py runserver
```


## Testing

```bash
py.test test_*.py
```
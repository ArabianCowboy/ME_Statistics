# Migrations bootstrap

This project uses Flask-Migrate (Alembic) for schema versioning.

After installing dependencies, generate the initial migration set with:

```bash
flask --app run.py db init
flask --app run.py db migrate -m "Initial schema"
flask --app run.py db upgrade
```

Current environment note:
- Python package tooling (`pip`) is unavailable, so migration files could not be generated yet.

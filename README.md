# ME Statistics

> Medication Error Statistics & Performance Tracker — a bilingual (EN/AR) hospital staff performance management web application.

## Features

- **Authentication** — Login, registration with admin approval, role-based access (admin/staff)
- **Dashboard** — Admin overview with KPIs + staff personal dashboard
- **Monthly Reports** — SDR data entry with approval workflow
- **Goals & Tasks** — Annual goal tracking, ad-hoc task management
- **Export** — Excel and PDF report generation
- **Audit Log** — Immutable forensic trail of all system changes
- **Backup & Restore** — Manual/auto database backup with point-in-time restore
- **Notifications** — Bell badge + toast notifications
- **i18n** — Full Arabic (RTL) and English support
- **Health endpoint** — `GET /health` returns `{"status": "ok"}`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask 3.1, SQLAlchemy, Flask-Login |
| Database | SQLite (dev), PostgreSQL (prod ready) |
| Frontend | Jinja2, vanilla CSS, vanilla JS |
| Auth | bcrypt password hashing |
| Export | openpyxl (Excel), reportlab (PDF) |
| Server | Gunicorn + Nginx |

## Quick Start

```bash
# 1. Clone
git clone <repo-url> && cd ME_Statistics

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate   # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env — set SECRET_KEY to a random string

# 5. Initialize database
flask db upgrade

# 6. Run (development)
python run.py
```

Open http://localhost:5000 — default admin: `admin` / `admin123`

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## Production Deployment

```bash
# 1. Install Gunicorn (already in requirements.txt)
pip install -r requirements.txt

# 2. Start Gunicorn
gunicorn -c gunicorn.conf.py "app:create_app('production')"

# 3. Configure Nginx
sudo cp nginx.conf /etc/nginx/sites-available/me_statistics
sudo ln -s /etc/nginx/sites-available/me_statistics /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 4. (Optional) SSL with Let's Encrypt
sudo certbot --nginx -d me-statistics.example.com
```

## Project Structure

```
ME_Statistics/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration classes
│   ├── extensions.py        # Flask extensions
│   ├── models.py            # SQLAlchemy models (7 tables)
│   ├── auth/                # Login, register, logout
│   ├── dashboard/           # Admin + staff dashboards
│   ├── logs/                # Reports, goals, tasks CRUD
│   ├── users/               # User management (admin)
│   ├── settings/            # System config, audit log, backups
│   ├── notifications/       # Bell + toast notifications
│   ├── export/              # Excel/PDF generation
│   ├── static/              # CSS, JS, images
│   └── templates/           # Jinja2 HTML templates
├── tests/                   # Pytest test suite
├── gunicorn.conf.py         # Production WSGI config
├── nginx.conf               # Reverse proxy config
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
└── run.py                   # Development entry point
```

## License

Internal hospital use — not for public distribution.

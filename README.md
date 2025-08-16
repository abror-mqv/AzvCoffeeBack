# AZV Coffee Backend

Django REST API for AZV Coffee. Non-commercial; optimized for convenient CI/CD.

## Tech
- Django 4.2
- Django REST Framework
- Token auth
- SQLite (dev)

## Quickstart
```bash
# Python 3.11 recommended
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Environment (dev defaults in settings.py, no env vars required)
python manage.py migrate
python manage.py createsuperuser  # optional
python manage.py runserver 0.0.0.0:8000
```

## Apps
- core, menue, loyalty, cart, feedbacks, notifications

## API Entry
- Project urls: `backend/urls.py`
- Media served from `MEDIA_ROOT` during dev

## Notifications
- Endpoints under `/api/notifications/`
- Also included in `GET /api/client/info/` as `notifications`

## CI (GitHub Actions)
- Workflow at `.github/workflows/ci.yml`
- Steps: setup Python, install deps, run migrations check, flake8, run minimal Django checks

## Deploy (example)
You can deploy on any PaaS that supports Django. For simple hosting:
- Use Gunicorn + Whitenoise for static if needed
- Set `ALLOWED_HOSTS` and `DEBUG=False` in environment or override settings

## Development
- Formatting: black
- Lint: flake8

## License
MIT

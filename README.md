# Flormia Gift — catálogo floral (Django)

## Local (SQLite)
    python -m venv venv
    venv\Scripts\activate          # Linux/Mac: source venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py cargar_datos
    python manage.py createsuperuser
    python manage.py runserver

## Render
Build Command:
    pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python manage.py cargar_datos && (python manage.py createsuperuser --noinput || true)
Start Command:
    gunicorn config.wsgi:application
Variables: PYTHON_VERSION=3.12.8, SECRET_KEY, DATABASE_URL (Supabase, Session pooler),
DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD.

Después, en /admin/ → Contacto, escribe tu número de WhatsApp (con lada, solo dígitos).

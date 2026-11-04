# MERK Establishments Management System

A Django web application for **MERK Establishments Limited** to record sales, manage the product catalogue and stock, and control which staff have access.

![Sales overview](docs/screenshots/desktop-sales-overview.webp)

<sub>Screenshots use fictional demo data.</sub>

## Features

- **Sign-in and sign-up**, using Django's authentication. Logout is a POST form, protected against cross-site requests. The "Remember me" checkbox is shown but doesn't change session length yet.
- **Password reset by emailed code** in three steps (request a code, enter it, set a new password):
  - Codes are 6 digits and expire after 5 minutes. Requesting a new code cancels older ones.
  - The response is the same whether or not an account uses the email.
  - An email can request at most 3 codes per 15 minutes. After 5 wrong codes, the code is cancelled.
- **Sales overview:** total sales value, today's sales, product count and units in stock, plus every sale with its customer, quantity, unit price, total, payment method (cash, Mpesa or bank), agent and date.
- **Sales:** record, edit and delete (with confirmation).
- **Products:** add, edit and delete. Each product has a description, supplier, unit cost, unit price and quantity, and is marked when out of stock.
- **Profiles:** name, email, phone, bio and profile picture. Everyone can edit their own profile.
- **User management (staff only):** list users, edit their details, activate or deactivate accounts, grant or remove staff access, and delete accounts. Non-staff users get a 403 page and don't see the menu link.
- **Responsive layout:** a fixed sidebar on desktop becomes a slide-out menu on phones, and tables become cards.

## Technologies

- Python 3.12 and Django 5.1
- PostgreSQL in production (through `dj-database-url`), SQLite for local development
- django-crispy-forms with Bootstrap 5.3, IBM Plex Sans and Font Awesome
- WhiteNoise for static files and Gunicorn as the WSGI server
- GitHub Actions for CI (`.github/workflows/django.yml`)

## Project structure

```
merk/              settings, root URLs, WSGI/ASGI
home/              the app: models, views, forms, URLs, tests
  templates/       base.html (app shell), auth_base.html (sign-in screens), partials/, page templates
  static/css/      merk.css (design system on top of Bootstrap)
docs/screenshots/  screenshots for this README
```

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `SECRET_KEY` | **Yes** unless `DEBUG=True` | Django secret key. Without it and with `DEBUG` off, the app refuses to start. |
| `DEBUG` | No (default `False`) | `True` only for local development. |
| `ALLOWED_HOSTS` | Yes in production | Comma-separated host names, e.g. `merk.onrender.com`. Default `localhost`. |
| `DATABASE_URL` | Yes in production | e.g. `postgres://user:password@host:5432/merk`. Defaults to `db.sqlite3` in the project folder. |
| `CSRF_TRUSTED_ORIGINS` | Yes in production | Comma-separated origins, e.g. `https://merk.onrender.com`. |
| `EMAIL_BACKEND` | No | Defaults to the console backend, which prints emails (and reset codes) to the terminal. Use `django.core.mail.backends.smtp.EmailBackend` to send real email. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | With SMTP | SMTP settings. |
| `SECURE_SSL_REDIRECT` | No (default `True` when `DEBUG` is off) | Redirects HTTP to HTTPS in production. |
| `SECURE_HSTS_SECONDS` | No (default `0`) | Opt-in HSTS. Only enable it once the site is permanently on HTTPS. |

Never commit real values. Keep them in your host's settings or in a local `.env` file, which is git-ignored.

## Run locally

```bash
git clone https://github.com/PreciousAtwiine/MERK-Establishments.git
cd MERK-Establishments
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Use a local SQLite database and development settings:

```bash
# macOS/Linux
export DEBUG=True
export DATABASE_URL=sqlite:///dev.sqlite3
# Windows PowerShell
$env:DEBUG="True"; $env:DATABASE_URL="sqlite:///dev.sqlite3"
```

Then create the tables and an administrator, and start the server:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000 and sign in. Password-reset codes appear in the terminal running the server.

> Python 3.12 is recommended. `Pillow==11.2.1` has no build for Python 3.14, and Django 5.1 doesn't support 3.14.

## Testing

```bash
python manage.py test
```

There are 23 tests, run against a temporary database. They cover:
- sign-in, sign-up and logout
- login protection on every page
- sales and product create, edit and delete
- quantity validation and the sales summary figures
- the staff-only user-management rules, including that a member can't make themselves staff
- the full password-reset flow, including expiry, cancelling older codes, attempt limits and request limits

## Deployment (for example, Render)

1. Create a PostgreSQL database and a web service.
2. **Build command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
3. **Start command:** `gunicorn merk.wsgi`
4. Set `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `CSRF_TRUSTED_ORIGINS`, and SMTP settings so reset codes are actually emailed.
5. Create an administrator from the host's shell: `python manage.py createsuperuser`.

## ⚠️ Security notice: data in the repository

Earlier commits include `db.sqlite3` and `db.json`. They contain real-looking user accounts (emails and password hashes), sessions and reset codes. `.github/workflows/static.yml` also publishes the whole repository to GitHub Pages, which makes those files downloadable.

Recommended steps, in order:
1. Turn off GitHub Pages for this repository, or delete `.github/workflows/static.yml`. This repo is a Django app, which GitHub Pages can't run anyway.
2. Commit the removal of `db.sqlite3` and `db.json` from tracking. They're now listed in `.gitignore`.
3. Reset the passwords of the affected accounts and set a new `SECRET_KEY` wherever the app is deployed.
4. Optionally, remove the files from the git history with `git filter-repo`, then force-push. This rewrites history, so coordinate it first.

## Known limitations

- **Profile pictures** are saved inside `home/static/profile_pictures/` instead of `MEDIA_ROOT`. In production, files uploaded after `collectstatic` won't be served, and on hosts with temporary disks they're lost on redeploy. The storage path is also absolute, so `makemigrations` sees a change on every machine. Fixing this needs a small model change and migration.
- **Sales don't change stock quantities.** Recording a sale doesn't reduce the product's quantity.
- **Reset-code limits** use Django's cache. With the default in-memory cache, they apply per server process. Use a shared cache (e.g. Redis) when running several processes.
- **`staticfiles/`** (the output of `collectstatic`) is committed. It's normally rebuilt during deployment and could be removed from version control.
- **The `Staff` model** exists in the admin, but the app doesn't use it.

#!/usr/bin/env bash
# Render build command: bash build.sh
# Python version comes from .python-version (3.12).
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --no-input

# Run migrations over Neon's direct (unpooled) connection when it's provided:
# schema changes need a real session, which the pooled PgBouncer endpoint
# doesn't keep between transactions. The app itself uses the pooled DATABASE_URL.
DATABASE_URL="${DATABASE_URL_UNPOOLED:-$DATABASE_URL}" python manage.py migrate --no-input

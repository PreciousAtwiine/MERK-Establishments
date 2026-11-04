#!/usr/bin/env bash
# Render build command: ./build.sh
# Python version comes from .python-version (3.12).
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

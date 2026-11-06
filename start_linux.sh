#!/usr/bin/env bash
set -e
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
python manage.py makemigrations catalog
python manage.py migrate
python manage.py runserver 127.0.0.1:8000

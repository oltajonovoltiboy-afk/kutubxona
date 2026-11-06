@echo off
setlocal
where py >nul 2>nul
if errorlevel 1 (echo Python topilmadi. Python 3.11 yoki yangirog'ini o'rnating.& pause & exit /b 1)
if not exist .venv py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env
python manage.py makemigrations catalog
python manage.py migrate
python manage.py runserver

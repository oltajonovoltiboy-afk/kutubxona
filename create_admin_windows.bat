@echo off
if not exist .venv\Scripts\activate.bat (
  echo Avval start_windows.bat orqali loyihani sozlang.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python manage.py createsuperuser
pause

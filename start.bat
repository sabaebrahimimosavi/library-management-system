@echo off

REM ============================
REM Backend (same folder as manage.py)
REM ============================

cd /d D:\university\6\web\library_management

call venv\Scripts\activate

python manage.py send_due_date_reminders
python manage.py calculate_fines

start "Django" cmd /k "cd /d D:\university\6\web\library_management && call venv\Scripts\activate && python manage.py runserver"

timeout /t 2 >nul

REM ============================
REM Frontend
REM ============================

start "Frontend" cmd /k "cd /d D:\university\6\web\library_management\frontend && call D:\university\6\web\library_management\venv\Scripts\activate && python -m http.server 5500"



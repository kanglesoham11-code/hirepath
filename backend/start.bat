@echo off
echo HIREPATH - Starting up...

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo Installing dependencies...
pip install -q -r requirements.txt

if not exist .env (
    copy .env.example .env
    echo.
    echo Created .env from template.
    echo Please add your GROQ_API_KEY to backend\.env
    echo Get a free key at: https://console.groq.com
    echo.
    pause
)

echo Seeding demo data...
python seed.py

echo.
echo Starting HIREPATH on http://localhost:8000
echo API docs: http://localhost:8000/docs
echo Open frontend\index.html in your browser
echo.

python main.py
pause

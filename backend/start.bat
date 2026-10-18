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
    echo Please add GROQ_API_KEY, GITHUB_TOKEN, and API_SECRET_KEY to .env
    echo Get a free key at: https://console.groq.com
    echo.
    pause
)

for %%V in (GROQ_API_KEY GITHUB_TOKEN API_SECRET_KEY) do (
    findstr /R /C:"^%%V=." .env >nul
    if errorlevel 1 (
        echo [FAIL] %%V must be set in .env before starting HIREPATH.
        pause
        exit /b 1
    )
)

echo Applying database migrations...
python -m alembic upgrade head

echo Seeding role data...
python seed.py

echo.
echo Starting HIREPATH on http://localhost:8000
echo API docs: http://localhost:8000/docs
echo Open frontend\index.html in your browser
echo.

python main.py
pause

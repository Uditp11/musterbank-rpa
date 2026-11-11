@echo off
rem Startet das Musterbank Backoffice auf http://127.0.0.1:5000
rem Aufruf: run_app.bat [v2] [slow]
rem   v2    Version 2: der Knopf zum Speichern heisst "Uebernehmen"
rem   slow  die Bestaetigung kommt erst nach 45 Sekunden
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Erster Start: virtuelle Umgebung wird angelegt ...
    python -m venv .venv || exit /b 1
)
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt || exit /b 1

set "APP_VERSION=1"
set "SLOW_CONFIRM=0"
for %%A in (%*) do (
    if /i "%%~A"=="v2" set "APP_VERSION=2"
    if /i "%%~A"=="slow" set "SLOW_CONFIRM=1"
)

echo Musterbank Backoffice: http://127.0.0.1:5000  (APP_VERSION=%APP_VERSION%, SLOW_CONFIRM=%SLOW_CONFIRM%)
echo Beenden mit Strg+C
".venv\Scripts\python.exe" -m flask --app app run --host 127.0.0.1 --port 5000 --no-reload

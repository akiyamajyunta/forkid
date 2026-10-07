@echo off
cd /d "%~dp0"
set PY=C:\Users\akiyama\AppData\Local\Programs\Python\Python314\python.exe
if not exist "%PY%" (
  echo Python 3.14 not found at %PY%
  echo Install Python 3.14 or edit run.bat
  exit /b 1
)
"%PY%" -m pip install -e . -q
"%PY%" -m kidgame.main

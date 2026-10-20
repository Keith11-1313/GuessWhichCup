@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0.build-tools"
python -m PyInstaller --noconfirm --clean --onefile --windowed --name GuessWhichCup --add-data "assets;assets" what_the_cup.py
if errorlevel 1 exit /b 1
echo Finished: dist\GuessWhichCup.exe

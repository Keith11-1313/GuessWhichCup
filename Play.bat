@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    python what_the_cup.py
) else (
    py -3 what_the_cup.py
)
if errorlevel 1 pause

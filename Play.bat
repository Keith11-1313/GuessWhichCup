@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    python -c "import PIL" >nul 2>nul
    if errorlevel 1 (
        echo Install game dependencies: python -m pip install -r Requirements.txt
        pause
        exit /b 1
    )
    python WhatTheCup.py
) else (
    py -3 -c "import PIL" >nul 2>nul
    if errorlevel 1 (
        echo Install game dependencies: py -3 -m pip install -r Requirements.txt
        pause
        exit /b 1
    )
    py -3 WhatTheCup.py
)
if errorlevel 1 pause

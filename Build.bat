@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0.build-tools"
set /p APP_VERSION=<VERSION
if not defined APP_VERSION exit /b 1
set "RELEASE_DIR=dist\v%APP_VERSION%"
set "RELEASE_EXE=%RELEASE_DIR%\GuessWhichCup-v%APP_VERSION%.exe"
if exist "%RELEASE_EXE%" (
    echo Version %APP_VERSION% already exists. Update VERSION before building.
    exit /b 1
)
python -m PyInstaller --noconfirm --clean --distpath "%RELEASE_DIR%" GuessWhichCup.spec
if errorlevel 1 exit /b 1
echo Finished: %RELEASE_EXE%

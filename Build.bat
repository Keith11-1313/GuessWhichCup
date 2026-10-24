@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0.build-tools"
set /p AppVersion=<Version
if not defined AppVersion exit /b 1
set "ReleaseDir=dist\v%AppVersion%"
set "ReleaseExe=%ReleaseDir%\GuessWhichCup-v%AppVersion%.exe"
if exist "%ReleaseExe%" (
    echo Version %AppVersion% already exists. Update Version before building.
    exit /b 1
)
python -m PyInstaller --noconfirm --clean --distpath "%ReleaseDir%" GuessWhichCup.spec
if errorlevel 1 exit /b 1
echo Finished: %ReleaseExe%

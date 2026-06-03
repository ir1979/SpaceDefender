@echo off
REM Space Defender - Build Script for Windows
REM Run this script to build the Windows executable and optional NSIS installer

REM -- ensure execution under cmd.exe when invoked from PowerShell --
REM PowerShell will execute each batch line separately, causing syntax errors.
if defined PSModulePath (
    rem re‑invoke using cmd and forward any arguments
    cmd /c "%~f0" %*
    exit /b %errorlevel%
)

echo ============================================
echo Building Space Defender for Windows
echo ============================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not installed
    pause
    exit /b 1
)

REM Install required packages if not already installed
python -c "import pygame, PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages from installer\requirements.txt...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        echo If you are offline, install pygame and pyinstaller from local wheels first.
        pause
        exit /b 1
    )
)

REM Determine target architecture (default = system bitness)
set "ARCH=%1"
if "%ARCH%"=="" (
    for /f "tokens=2 delims== " %%a in ('wmic os get osarchitecture /value 2^>nul') do set "ARCH=%%a"
    REM wmic returns "64-bit" or "32-bit"
    if not "%ARCH%"=="" (
        if /i "%ARCH%"=="64-bit" set "ARCH=64" else set "ARCH=32"
    )
)

if /i "%ARCH%"=="32" (
    set "PYINSTALLER_ARCH=--arch=32"
    set "OUTDIR=dist\win32"
) else (
    set "PYINSTALLER_ARCH="
    set "OUTDIR=dist\win64"
)

REM create output directory if needed
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

REM Build the executable
echo Building executable for %ARCH%-bit Windows...
pyinstaller space_defender.spec --clean %PYINSTALLER_ARCH% --distpath "%OUTDIR%" --workpath "build" --noconfirm

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

REM Optionally create a simple NSIS-based installer if makensis is installed
set "NSIS_PATH="
where makensis >nul 2>&1
if %errorlevel%==0 (
    for /f "delims=" %%A in ('where makensis') do set "NSIS_PATH=%%A" & goto :FoundNSIS
)
if exist "%ProgramFiles%\NSIS\Bin\makensis.exe" set "NSIS_PATH=%ProgramFiles%\NSIS\Bin\makensis.exe"
if exist "%ProgramFiles(x86)%\NSIS\Bin\makensis.exe" set "NSIS_PATH=%ProgramFiles(x86)%\NSIS\Bin\makensis.exe"
:FoundNSIS
if defined NSIS_PATH (
    echo makensis found at %NSIS_PATH% – creating installer...
    "%NSIS_PATH%" /DARCH=%ARCH% "space_defender.nsi"
) else (
    echo makensis not found; skipping NSIS installer generation.
)

echo ============================================
echo Build complete!
echo ============================================
echo Executable location: %OUTDIR%\SpaceDefender\SpaceDefender.exe
if exist "%OUTDIR%\Space Defender-setup-%ARCH%.exe" echo Installer created: %OUTDIR%\Space Defender-setup-%ARCH%.exe
echo.
echo To run the game, copy the full folder and launch SpaceDefender.exe, or use the installer if generated.
if not defined SKIP_PAUSE pause

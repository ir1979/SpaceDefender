@echo off
REM Space Defender - Build Script for Windows
REM Run this script to build the Windows executable

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
echo Installing required packages...
pip install pygame pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: Failed to install required packages
    pause
    exit /b 1
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

REM Run PyInstaller
REM When passing an existing .spec file, --specpath is not permitted;
REM only set distpath/workpath to keep build artifacts separate.
echo Building executable for %ARCH%-bit Windows...
pyinstaller space_defender.spec --clean %PYINSTALLER_ARCH% --distpath "%OUTDIR%" --workpath "build"

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

REM Optionally create a simple NSIS-based installer if makensis is installed
where makensis >nul 2>&1
if %errorlevel%==0 (
    echo makensis found – creating installer...
    set "NSIS_SCRIPT=build\space_defender_%ARCH%.nsi"
    >"%NSIS_SCRIPT%" echo !define PRODUCT_NAME "Space Defender"
    >>"%NSIS_SCRIPT%" echo !define VERSION "2.1"
    >>"%NSIS_SCRIPT%" echo !define COMPANY_NAME "Ali Mortazavi"
    >>"%NSIS_SCRIPT%" echo !define EXE_NAME "SpaceDefender.exe"
    >>"%NSIS_SCRIPT%" echo !define ARCH "%ARCH%"
    >>"%NSIS_SCRIPT%" echo OutFile "..\dist\win%ARCH%\${PRODUCT_NAME}-setup-%ARCH%.exe"
    >>"%NSIS_SCRIPT%" echo InstallDir "$PROGRAMFILES\${PRODUCT_NAME}"
    >>"%NSIS_SCRIPT%" echo Page directory
    >>"%NSIS_SCRIPT%" echo Page instfiles
    >>"%NSIS_SCRIPT%" echo Section "Install"
    >>"%NSIS_SCRIPT%" echo   SetOutPath "$INSTDIR"
    >>"%NSIS_SCRIPT%" echo   File "..\dist\win%ARCH%\${EXE_NAME}"
    >>"%NSIS_SCRIPT%" echo   CreateShortcut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${EXE_NAME}"
    >>"%NSIS_SCRIPT%" echo SectionEnd
    makensis "%NSIS_SCRIPT%"
)

echo ============================================
echo Build complete!
echo ============================================
echo Executable location: %OUTDIR%\SpaceDefender.exe
if exist "%OUTDIR%\${PRODUCT_NAME}-setup-%ARCH%.exe" echo Installer created: %OUTDIR%\${PRODUCT_NAME}-setup-%ARCH%.exe
echo.
echo To run the game, double-click SpaceDefender.exe (or use the installer if generated)
pause

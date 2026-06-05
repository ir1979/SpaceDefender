@echo off
REM Space Defender - Build Script for Windows
REM Run this script to build the Windows executable and optional NSIS installer

setlocal EnableExtensions EnableDelayedExpansion

REM Batch files already run under cmd.exe when launched from PowerShell.
REM Avoid re-invocation wrappers here because nested cmd processes can cause
REM repeated Ctrl+C "Terminate batch job (Y/N)?" prompts.

set "VERBOSE=0"
if /I "%~2"=="verbose" set "VERBOSE=1"
if /I "%~2"=="--verbose" set "VERBOSE=1"
if /I "%~1"=="verbose" set "VERBOSE=1"
if /I "%~1"=="--verbose" set "VERBOSE=1"
if "%VERBOSE%"=="1" (
    echo [TRACE] Verbose mode enabled. Command echo is ON.
    echo on
) else (
    echo [INFO] Verbose mode disabled. Use: build.bat 64 --verbose
)

set "REQUIRED_CONDA_ENV=py311"
echo ============================================
echo Building Space Defender for Windows
echo ============================================
call :LogStep "Start build script"

echo Checking Conda environment...
if /I "%CONDA_DEFAULT_ENV%"=="%REQUIRED_CONDA_ENV%" (
    echo Conda environment %REQUIRED_CONDA_ENV% is already active.
) else (
    echo Activating conda environment %REQUIRED_CONDA_ENV%...
    call :LogStep "Checking conda availability"
    where conda >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Conda not found on PATH. Open an Anaconda/Miniconda prompt or run "conda init cmd.exe".
        pause
        exit /b 1
    )
    call :LogStep "Running: conda activate %REQUIRED_CONDA_ENV%"
    call conda activate %REQUIRED_CONDA_ENV%
    if errorlevel 1 (
        echo ERROR: Failed to activate conda environment %REQUIRED_CONDA_ENV%.
        echo Make sure the environment exists: conda env list
        pause
        exit /b 1
    )
)

REM Check if Python is installed
call :LogStep "Checking python availability"
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if pip is available
call :LogStep "Checking pip availability"
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not installed
    pause
    exit /b 1
)

REM Install required packages if not already installed
call :LogStep "Checking required packages: pygame, PyInstaller"
python -c "import pygame, PyInstaller" >nul 2>&1
if errorlevel 1 (
    call :LogStep "Installing requirements from installer\\requirements.txt"
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        echo If you are offline, install pygame and pyinstaller from local wheels first.
        pause
        exit /b 1
    )
    call :LogStep "Requirements installation finished"
)

if "%VERBOSE%"=="1" (
    call :LogStep "Python executable and environment details"
    where python
    python --version
    pip --version
)

REM Determine target architecture: 32, 64, or all
set "ARCH=%~1"
if "%ARCH%"=="" set "ARCH=auto"
if /I "%ARCH%"=="verbose" set "ARCH=auto"
if /I "%ARCH%"=="--verbose" set "ARCH=auto"

if /I "%ARCH%"=="auto" (
    for /f "tokens=2 delims== " %%a in ('wmic os get osarchitecture /value 2^>nul') do set "ARCH=%%a"
    if not "%ARCH%"=="" (
        if /i "%ARCH%"=="64-bit" set "ARCH=64" else set "ARCH=32"
    )
)

if /I "%ARCH%"=="all" (
    call :LogStep "Requested architecture: all"
    echo Building both 64-bit and 32-bit installers...
    call :BuildOne 64
    if errorlevel 1 exit /b 1
    call :BuildOne 32
    if errorlevel 1 exit /b 1
    goto :EOF
)

call :BuildOne %ARCH%
exit /b %ERRORLEVEL%

:BuildOne
set "ARCH=%~1"
call :LogStep "Entered BuildOne with ARCH=%ARCH%"
if /I "%ARCH%"=="64-bit" set "ARCH=64"
if /I "%ARCH%"=="32-bit" set "ARCH=32"

if not "%ARCH%"=="32" if not "%ARCH%"=="64" (
    echo ERROR: Invalid architecture "%ARCH%". Use 32, 64, or all.
    exit /b 1
)

for /f "delims=" %%a in ('python -c "import struct; print(struct.calcsize(\"P\")*8)"') do set "PY_BITS=%%a"
call :LogStep "Detected python bitness: %PY_BITS%"
if "%ARCH%"=="32" if "%PY_BITS%"=="64" (
    echo ERROR: Current Python is 64-bit; a 32-bit build requires 32-bit Python.
    exit /b 1
)
if "%ARCH%"=="64" if "%PY_BITS%"=="32" (
    echo ERROR: Current Python is 32-bit; a 64-bit build requires 64-bit Python.
    exit /b 1
)

if /i "%ARCH%"=="32" (
    set "OUTDIR=dist\win32"
) else (
    set "OUTDIR=dist\win64"
)

if not exist "%OUTDIR%" mkdir "%OUTDIR%"

echo --------------------------------------------
echo Building executable for %ARCH%-bit Windows...
echo Output folder: %OUTDIR%
echo --------------------------------------------
call :LogStep "Running PyInstaller (this may take several minutes)"
echo [CMD ] pyinstaller space_defender.spec --clean --distpath "%OUTDIR%" --workpath "build" --noconfirm

pyinstaller space_defender.spec --clean --distpath "%OUTDIR%" --workpath "build" --noconfirm
if errorlevel 1 (
    echo ERROR: Build failed for %ARCH%-bit target.
    exit /b 1
)
call :LogStep "PyInstaller finished for %ARCH%-bit"

REM Verify the produced bundle is sane before we declare success.
call :VerifyBundle "%OUTDIR%" "%ARCH%"
if errorlevel 1 (
    echo ERROR: Post-build verification failed for %ARCH%-bit target.
    exit /b 1
)

REM Optionally create a simple NSIS-based installer if makensis is installed
set "NSIS_PATH="
call :LogStep "Checking for NSIS (makensis)"
where makensis >nul 2>&1
if %errorlevel%==0 (
    for /f "delims=" %%A in ('where makensis') do set "NSIS_PATH=%%A" & goto :FoundNSIS
)
if exist "%ProgramFiles%\NSIS\Bin\makensis.exe" set "NSIS_PATH=%ProgramFiles%\NSIS\Bin\makensis.exe"
if exist "%ProgramFiles(x86)%\NSIS\Bin\makensis.exe" set "NSIS_PATH=%ProgramFiles(x86)%\NSIS\Bin\makensis.exe"
:FoundNSIS
if defined NSIS_PATH (
    call :LogStep "Running NSIS installer generation"
    echo makensis found at %NSIS_PATH% – creating installer...
    "%NSIS_PATH%" /DARCH=%ARCH% "space_defender.nsi"
    if errorlevel 1 (
        echo ERROR: NSIS installer generation failed for %ARCH%-bit.
        exit /b 1
    )
) else (
    echo makensis not found; skipping NSIS installer generation.
)

echo --------------------------------------------
echo Build complete for %ARCH%-bit target.
echo --------------------------------------------
echo Executable location: %OUTDIR%\SpaceDefender\SpaceDefender.exe
if exist "%OUTDIR%\Space Defender-setup-%ARCH%.exe" echo Installer created: %OUTDIR%\Space Defender-setup-%ARCH%.exe
echo.
exit /b 0

:LogStep
echo [STEP][%DATE% %TIME%] %~1
exit /b 0

:VerifyBundle
REM %~1 = dist folder, %~2 = arch (32 or 64)
set "VB_OUT=%~1"
set "VB_ARCH=%~2"
set "VB_EXE=%VB_OUT%\SpaceDefender\SpaceDefender.exe"
set "VB_PG=%VB_OUT%\SpaceDefender\_internal\pygame"
set "VB_OK=1"

if not exist "%VB_EXE%" (
    echo ERROR: %VB_EXE% not found after build.
    set "VB_OK=0"
)

if not exist "%VB_PG%\SDL2.dll" (
    echo ERROR: %VB_PG%\SDL2.dll is missing.
    echo This is the root cause of the "Failed loading SDL library" runtime error.
    echo The spec file must bundle pygame's dynamic libraries into _internal\pygame.
    set "VB_OK=0"
) else (
    for %%S in ("%VB_PG%\SDL2.dll") do set "VB_SDL_SIZE=%%~zS"
    if !VB_SDL_SIZE! LSS 1000000 (
        echo ERROR: %VB_PG%\SDL2.dll is only !VB_SDL_SIZE! bytes; the full pygame SDL2 DLL is ~2.4 MB.
        echo The bundled file looks like the PyInstaller bootloader stub, not pygame's runtime.
        set "VB_OK=0"
    )
)

REM Cross-check the produced EXE's PE machine against the requested arch.
if exist "%VB_EXE%" (
    for /f "usebackq delims=" %%M in (`powershell -NoProfile -Command "$b=[IO.File]::ReadAllBytes('%VB_EXE%');$o=[BitConverter]::ToInt32($b,0x3C);[BitConverter]::ToUInt16($b,$o+4)" 2^>nul`) do set "VB_MACHINE=%%M"
    if "%VB_ARCH%"=="32" if not "!VB_MACHINE!"=="332" (
        echo ERROR: Requested 32-bit build but the produced SpaceDefender.exe is not 32-bit (PE machine=!VB_MACHINE!, 332=x86).
        echo PyInstaller only packages the CPython interpreter of the active env; it cannot turn a 64-bit interpreter into a 32-bit one.
        echo Activate a 32-bit conda env (e.g. set CONDA_SUBDIR=win-32 then conda create -n py311-32 python=3.11) and re-run.
        set "VB_OK=0"
    )
    if "%VB_ARCH%"=="64" if not "!VB_MACHINE!"=="34404" (
        echo ERROR: Requested 64-bit build but the produced SpaceDefender.exe is not 64-bit (PE machine=!VB_MACHINE!, 34404=x64).
        set "VB_OK=0"
    )
)

if "%VB_OK%"=="1" (
    echo Post-build verification OK.
    echo   EXE      : %VB_EXE%
    echo   PE machine: !VB_MACHINE! ^(332=x86, 34404=x64^)
    if defined VB_SDL_SIZE echo   SDL2.dll : !VB_SDL_SIZE! bytes
) else (
    echo Post-build verification FAILED.
    exit /b 1
)
exit /b 0

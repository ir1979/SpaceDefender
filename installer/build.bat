@echo off
REM ============================================================================
REM Space Defender - Build Script for Windows
REM ----------------------------------------------------------------------------
REM Produces PyInstaller folder bundles and (optionally) NSIS setup .exe files
REM for 32-bit and/or 64-bit Windows targets.
REM
REM Usage:
REM   build.bat [arch] [options]
REM
REM Arch:
REM   32         Build 32-bit target. Default conda env: py3x_32bit
REM   64         Build 64-bit target. Default conda env: py311
REM   all        Build both 32-bit and 64-bit
REM   auto       Auto-detect host bitness (default if arch omitted)
REM
REM Options:
REM   --env NAME       Conda env to use for this build (overrides defaults)
REM   --env32 NAME     Conda env for the 32-bit pass (used with "all")
REM   --env64 NAME     Conda env for the 64-bit pass (used with "all")
REM   --clean          Wipe build/dist for the chosen arch(s) first (default ON)
REM   --no-clean       Skip wiping previous build/dist
REM   --verbose, -v    Verbose tracing (default ON)
REM   --quiet, -q      Disable verbose tracing
REM   --no-installer   Skip NSIS setup .exe generation
REM   --help, -h       Show this help and exit
REM
REM Examples:
REM   build.bat 32                       (uses py3x_32bit)
REM   build.bat 32 --env py3x_32bit      (explicit)
REM   build.bat 64 --env py311
REM   build.bat all --env32 py3x_32bit --env64 py311
REM   build.bat 32 --no-installer --quiet
REM ============================================================================

setlocal EnableExtensions EnableDelayedExpansion

REM ---- Anchor cwd to this script's directory ---------------------------------
REM All artifacts (space_defender.spec, space_defender.nsi, requirements.txt,
REM build/work/dist subfolders) live here, so we always run from this folder
REM regardless of where the user invoked build.bat from.
pushd "%~dp0" >nul
if errorlevel 1 (
    echo ERROR: Could not cd to script directory "%~dp0".
    exit /b 1
)

REM ---- Defaults --------------------------------------------------------------
set "ARCH="
set "ENV_OVERRIDE="
set "ENV_32_OVERRIDE="
set "ENV_64_OVERRIDE="
set "DEFAULT_ENV_32=py3x_32bit"
set "DEFAULT_ENV_64=py311"
set "VERBOSE=1"
set "CLEAN=1"
set "MAKE_INSTALLER=1"

REM ---- Parse arguments -------------------------------------------------------
:parse_args
if "%~1"=="" goto :after_args
set "ARG=%~1"

if /I "!ARG!"=="--help" goto :show_help
if /I "!ARG!"=="-h"     goto :show_help
if /I "!ARG!"=="/?"     goto :show_help

if /I "!ARG!"=="--verbose" ( set "VERBOSE=1" & shift & goto :parse_args )
if /I "!ARG!"=="-v"        ( set "VERBOSE=1" & shift & goto :parse_args )
if /I "!ARG!"=="verbose"   ( set "VERBOSE=1" & shift & goto :parse_args )
if /I "!ARG!"=="--quiet"   ( set "VERBOSE=0" & shift & goto :parse_args )
if /I "!ARG!"=="-q"        ( set "VERBOSE=0" & shift & goto :parse_args )

if /I "!ARG!"=="--clean"        ( set "CLEAN=1" & shift & goto :parse_args )
if /I "!ARG!"=="--no-clean"     ( set "CLEAN=0" & shift & goto :parse_args )
if /I "!ARG!"=="--no-installer" ( set "MAKE_INSTALLER=0" & shift & goto :parse_args )

if /I "!ARG!"=="--env" (
    if "%~2"=="" ( echo ERROR: --env requires a value & exit /b 2 )
    set "ENV_OVERRIDE=%~2"
    shift & shift & goto :parse_args
)
if /I "!ARG!"=="--env32" (
    if "%~2"=="" ( echo ERROR: --env32 requires a value & exit /b 2 )
    set "ENV_32_OVERRIDE=%~2"
    shift & shift & goto :parse_args
)
if /I "!ARG!"=="--env64" (
    if "%~2"=="" ( echo ERROR: --env64 requires a value & exit /b 2 )
    set "ENV_64_OVERRIDE=%~2"
    shift & shift & goto :parse_args
)

REM Anything else is treated as the architecture (positional)
if not defined ARCH (
    set "ARCH=!ARG!"
    shift & goto :parse_args
)

echo WARNING: ignoring unknown argument "!ARG!"
shift & goto :parse_args

:after_args
if not defined ARCH set "ARCH=auto"

REM ---- Normalize arch --------------------------------------------------------
if /I "%ARCH%"=="64-bit" set "ARCH=64"
if /I "%ARCH%"=="32-bit" set "ARCH=32"
if /I "%ARCH%"=="x64"    set "ARCH=64"
if /I "%ARCH%"=="x86"    set "ARCH=32"

if /I "%ARCH%"=="auto" (
    set "ARCH=64"
    for /f "tokens=2 delims== " %%a in ('wmic os get osarchitecture /value 2^>nul') do (
        if /I "%%a"=="32-bit" set "ARCH=32"
    )
)

if /I not "%ARCH%"=="32" if /I not "%ARCH%"=="64" if /I not "%ARCH%"=="all" (
    echo ERROR: Invalid architecture "%ARCH%". Use 32, 64, all, or auto.
    exit /b 2
)

REM ---- Header ----------------------------------------------------------------
if "%VERBOSE%"=="1" ( echo on ) else ( @echo off )

echo ============================================================
echo  Space Defender - Build
echo ------------------------------------------------------------
echo  Arch         : %ARCH%
if defined ENV_OVERRIDE      echo  --env        : %ENV_OVERRIDE%
if defined ENV_32_OVERRIDE   echo  --env32      : %ENV_32_OVERRIDE%
if defined ENV_64_OVERRIDE   echo  --env64      : %ENV_64_OVERRIDE%
echo  Default 32   : %DEFAULT_ENV_32%
echo  Default 64   : %DEFAULT_ENV_64%
echo  Clean        : %CLEAN%
echo  Verbose      : %VERBOSE%
echo  NSIS step    : %MAKE_INSTALLER%
echo ============================================================

call :LogStep "Start build script"

REM ---- Locate NSIS once (used per build) -------------------------------------
set "NSIS_PATH="
where makensis >nul 2>&1
if %errorlevel%==0 (
    for /f "delims=" %%A in ('where makensis') do (
        if not defined NSIS_PATH set "NSIS_PATH=%%A"
    )
)
if not defined NSIS_PATH if exist "%ProgramFiles%\NSIS\Bin\makensis.exe"      set "NSIS_PATH=%ProgramFiles%\NSIS\Bin\makensis.exe"
if not defined NSIS_PATH if exist "%ProgramFiles(x86)%\NSIS\Bin\makensis.exe" set "NSIS_PATH=%ProgramFiles(x86)%\NSIS\Bin\makensis.exe"
if defined NSIS_PATH (
    echo [INFO] NSIS found: !NSIS_PATH!
) else (
    if "%MAKE_INSTALLER%"=="1" (
        echo [WARN] NSIS ^(makensis^) not found - setup .exe will be skipped.
        echo [WARN] Install from https://nsis.sourceforge.io/Download or run:
        echo [WARN]     winget install NSIS.NSIS
    )
)

REM ---- Dispatch --------------------------------------------------------------
if /I "%ARCH%"=="all" (
    call :LogStep "Requested architecture: all"
    call :ResolveEnv 64 "%ENV_64_OVERRIDE%"
    call :BuildOne 64 "!RESOLVED_ENV!"
    if errorlevel 1 popd & exit /b 1
    call :ResolveEnv 32 "%ENV_32_OVERRIDE%"
    call :BuildOne 32 "!RESOLVED_ENV!"
    if errorlevel 1 popd & exit /b 1
    echo.
    echo ============================================================
    echo  All builds completed successfully.
    echo ============================================================
    popd
    exit /b 0
)

call :ResolveEnv %ARCH% "%ENV_OVERRIDE%"
call :BuildOne %ARCH% "!RESOLVED_ENV!"
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%

REM ============================================================================
REM Helpers
REM ============================================================================

:ResolveEnv
REM %1 = arch (32|64), %2 = explicit override (may be empty)
set "_ARCH=%~1"
set "_OVR=%~2"
if defined _OVR (
    set "RESOLVED_ENV=%_OVR%"
) else if "%_ARCH%"=="32" (
    set "RESOLVED_ENV=%DEFAULT_ENV_32%"
) else (
    set "RESOLVED_ENV=%DEFAULT_ENV_64%"
)
exit /b 0

:BuildOne
REM %1 = ARCH (32|64), %2 = conda env name
set "B_ARCH=%~1"
set "B_ENV=%~2"

echo.
echo ============================================================
echo  Building %B_ARCH%-bit target with conda env: %B_ENV%
echo ============================================================
call :LogStep "BuildOne arch=%B_ARCH% env=%B_ENV%"

REM ---- Activate the requested conda env (in this cmd session only) ----------
call :LogStep "Locating conda"
where conda >nul 2>&1
if errorlevel 1 (
    echo ERROR: Conda not found on PATH.
    echo        Open an Anaconda/Miniconda prompt or run "conda init cmd.exe".
    exit /b 1
)

REM Always (re)activate even if CONDA_DEFAULT_ENV already matches, so we are
REM sure the right interpreter is on PATH for this build pass.
call :LogStep "conda activate %B_ENV%"
call conda activate %B_ENV%
if errorlevel 1 (
    echo ERROR: Failed to activate conda environment "%B_ENV%".
    echo        Make sure it exists: conda env list
    exit /b 1
)

REM ---- Sanity-check python --------------------------------------------------
call :LogStep "Checking python in env"
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not available inside env "%B_ENV%".
    exit /b 1
)

for /f "delims=" %%a in ('python -c "import struct; print(struct.calcsize(\"P\")*8)"') do set "PY_BITS=%%a"
for /f "delims=" %%a in ('python -c "import sys; print(sys.version.split()[0])"') do set "PY_VER=%%a"
for /f "delims=" %%a in ('python -c "import sys, os; print(os.path.dirname(sys.executable))"') do set "PY_HOME=%%a"
echo [INFO] Python %PY_VER% (%PY_BITS%-bit) at %PY_HOME%

if "%B_ARCH%"=="32" if not "%PY_BITS%"=="32" (
    echo ERROR: Requested 32-bit build but env "%B_ENV%" has %PY_BITS%-bit Python.
    echo        Create or pick a 32-bit env, e.g.:
    echo            set CONDA_SUBDIR=win-32
    echo            conda create -n py3x_32bit -c conda-forge python=3.9 pip
    echo            conda activate py3x_32bit
    echo            set CONDA_SUBDIR=
    echo            pip install pygame pyinstaller numpy
    exit /b 1
)
if "%B_ARCH%"=="64" if not "%PY_BITS%"=="64" (
    echo ERROR: Requested 64-bit build but env "%B_ENV%" has %PY_BITS%-bit Python.
    exit /b 1
)

REM ---- Make sure required packages are installed ----------------------------
call :LogStep "Verifying packages: pygame, PyInstaller, numpy"
python -c "import pygame, PyInstaller, numpy" >nul 2>&1
if errorlevel 1 (
    call :LogStep "Installing requirements.txt into %B_ENV%"
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install required packages into "%B_ENV%".
        exit /b 1
    )
)

if "%VERBOSE%"=="1" (
    call :LogStep "Detailed environment info"
    where python
    python --version
    python -c "import pygame, PyInstaller, numpy, sys; print('pygame', pygame.version.ver); print('PyInstaller', PyInstaller.__version__); print('numpy', numpy.__version__); print('exec', sys.executable)"
)

REM ---- Layout paths ---------------------------------------------------------
if "%B_ARCH%"=="32" (
    set "OUTDIR=dist\win32"
    set "WORKDIR=build\win32"
) else (
    set "OUTDIR=dist\win64"
    set "WORKDIR=build\win64"
)

REM ---- Clean ----------------------------------------------------------------
if "%CLEAN%"=="1" (
    call :LogStep "Cleaning previous artifacts for %B_ARCH%-bit"
    if exist "%WORKDIR%"               rmdir /s /q "%WORKDIR%"
    if exist "%OUTDIR%\SpaceDefender"  rmdir /s /q "%OUTDIR%\SpaceDefender"
    if exist "%OUTDIR%\Space Defender-setup-%B_ARCH%.exe" del /f /q "%OUTDIR%\Space Defender-setup-%B_ARCH%.exe"
    REM Legacy folders from previous build script versions
    if exist "build\space_defender"    rmdir /s /q "build\space_defender"
    if exist "build32\space_defender"  rmdir /s /q "build32\space_defender"
)

if not exist "%OUTDIR%"  mkdir "%OUTDIR%"
if not exist "%WORKDIR%" mkdir "%WORKDIR%"

REM ---- Run PyInstaller ------------------------------------------------------
echo ------------------------------------------------------------
echo  PyInstaller: building %B_ARCH%-bit bundle
echo  Spec        : space_defender.spec
echo  Output      : %OUTDIR%\SpaceDefender
echo  Work        : %WORKDIR%
echo ------------------------------------------------------------
call :LogStep "Running PyInstaller (this may take several minutes)"

set "PYI_LOG_LEVEL=INFO"
if "%VERBOSE%"=="1" set "PYI_LOG_LEVEL=DEBUG"

echo [CMD ] pyinstaller space_defender.spec --clean --noconfirm --distpath "%OUTDIR%" --workpath "%WORKDIR%" --log-level %PYI_LOG_LEVEL%
pyinstaller space_defender.spec --clean --noconfirm --distpath "%OUTDIR%" --workpath "%WORKDIR%" --log-level %PYI_LOG_LEVEL%
if errorlevel 1 (
    echo ERROR: PyInstaller failed for %B_ARCH%-bit target.
    exit /b 1
)
call :LogStep "PyInstaller finished for %B_ARCH%-bit"

REM ---- Verify ---------------------------------------------------------------
call :VerifyBundle "%OUTDIR%" "%B_ARCH%"
if errorlevel 1 (
    echo ERROR: Post-build verification failed for %B_ARCH%-bit target.
    exit /b 1
)

REM ---- Optional NSIS setup .exe --------------------------------------------
if "%MAKE_INSTALLER%"=="1" if defined NSIS_PATH (
    call :LogStep "Generating NSIS installer for %B_ARCH%-bit"
    set "NSIS_VERBOSITY=2"
    if "%VERBOSE%"=="1" set "NSIS_VERBOSITY=4"
    echo [CMD ] "%NSIS_PATH%" /V!NSIS_VERBOSITY! /DARCH=%B_ARCH% space_defender.nsi
    "%NSIS_PATH%" /V!NSIS_VERBOSITY! /DARCH=%B_ARCH% "space_defender.nsi"
    if errorlevel 1 (
        echo ERROR: NSIS installer generation failed for %B_ARCH%-bit.
        exit /b 1
    )
    if exist "%OUTDIR%\Space Defender-setup-%B_ARCH%.exe" (
        for %%S in ("%OUTDIR%\Space Defender-setup-%B_ARCH%.exe") do set "INST_SIZE=%%~zS"
        echo [OK  ] Installer: %OUTDIR%\Space Defender-setup-%B_ARCH%.exe ^(!INST_SIZE! bytes^)
    )
) else if "%MAKE_INSTALLER%"=="1" (
    echo [WARN] NSIS not available - skipping setup .exe for %B_ARCH%-bit.
) else (
    echo [INFO] --no-installer specified - skipping setup .exe for %B_ARCH%-bit.
)

echo ------------------------------------------------------------
echo  Build complete for %B_ARCH%-bit target.
echo  Bundle  : %OUTDIR%\SpaceDefender\SpaceDefender.exe
if exist "%OUTDIR%\Space Defender-setup-%B_ARCH%.exe" echo  Setup   : %OUTDIR%\Space Defender-setup-%B_ARCH%.exe
echo ------------------------------------------------------------
exit /b 0

:LogStep
echo [STEP][%DATE% %TIME%] %~1
exit /b 0

:VerifyBundle
REM %1 = dist folder, %2 = arch (32 or 64)
set "VB_OUT=%~1"
set "VB_ARCH=%~2"
set "VB_EXE=%VB_OUT%\SpaceDefender\SpaceDefender.exe"
set "VB_PG=%VB_OUT%\SpaceDefender\_internal\pygame"
set "VB_OK=1"
set "VB_SDL_SIZE="
set "VB_MACHINE="

call :LogStep "Verifying produced bundle (%VB_ARCH%-bit)"

if not exist "%VB_EXE%" (
    echo ERROR: %VB_EXE% not found after build.
    set "VB_OK=0"
)

if not exist "%VB_PG%\SDL2.dll" (
    echo ERROR: %VB_PG%\SDL2.dll is missing.
    echo        This is the root cause of "Failed loading SDL library" at runtime.
    echo        The spec must bundle pygame's dynamic libraries into _internal\pygame.
    set "VB_OK=0"
) else (
    for %%S in ("%VB_PG%\SDL2.dll") do set "VB_SDL_SIZE=%%~zS"
    if !VB_SDL_SIZE! LSS 1000000 (
        echo ERROR: %VB_PG%\SDL2.dll is only !VB_SDL_SIZE! bytes; the full pygame SDL2 DLL is ~2.4 MB.
        echo        The bundled file looks like a PyInstaller stub, not pygame's runtime.
        set "VB_OK=0"
    )
)

if exist "%VB_EXE%" (
    for /f "usebackq delims=" %%M in (`powershell -NoProfile -Command "$b=[IO.File]::ReadAllBytes('%VB_EXE%');$o=[BitConverter]::ToInt32($b,0x3C);[BitConverter]::ToUInt16($b,$o+4)" 2^>nul`) do set "VB_MACHINE=%%M"
    if "%VB_ARCH%"=="32" if not "!VB_MACHINE!"=="332" (
        echo ERROR: Requested 32-bit build but produced SpaceDefender.exe is PE machine=!VB_MACHINE! ^(expected 332=x86^).
        echo        PyInstaller bundles the CPython interpreter of the active env; it cannot convert 64-bit to 32-bit.
        set "VB_OK=0"
    )
    if "%VB_ARCH%"=="64" if not "!VB_MACHINE!"=="34404" (
        echo ERROR: Requested 64-bit build but produced SpaceDefender.exe is PE machine=!VB_MACHINE! ^(expected 34404=x64^).
        set "VB_OK=0"
    )
)

if "%VB_OK%"=="1" (
    echo [OK  ] Post-build verification passed.
    echo        EXE        : %VB_EXE%
    echo        PE machine : !VB_MACHINE!  ^(332=x86, 34404=x64^)
    if defined VB_SDL_SIZE echo        SDL2.dll   : !VB_SDL_SIZE! bytes
) else (
    echo [ERR ] Post-build verification FAILED.
    exit /b 1
)
exit /b 0

:show_help
echo Space Defender - build.bat
echo.
echo Usage:
echo   build.bat [arch] [options]
echo.
echo Arch:
echo   32         Build 32-bit target  (default conda env: %DEFAULT_ENV_32%)
echo   64         Build 64-bit target  (default conda env: %DEFAULT_ENV_64%)
echo   all        Build both 32-bit and 64-bit
echo   auto       Auto-detect host bitness (default if omitted)
echo.
echo Options:
echo   --env NAME       Conda env to use for this build (overrides default)
echo   --env32 NAME     Conda env for the 32-bit pass (with arch=all)
echo   --env64 NAME     Conda env for the 64-bit pass (with arch=all)
echo   --clean          Wipe build/dist for this arch first  (default ON)
echo   --no-clean       Skip wiping previous build/dist
echo   --verbose, -v    Verbose tracing                      (default ON)
echo   --quiet, -q      Suppress verbose tracing
echo   --no-installer   Skip NSIS setup .exe generation
echo   --help, -h       Show this help and exit
echo.
echo Examples:
echo   build.bat 32
echo   build.bat 32 --env py3x_32bit
echo   build.bat 64 --env py311
echo   build.bat all --env32 py3x_32bit --env64 py311
echo  build.bat 32 --no-installer --quiet
popd
exit /b 0

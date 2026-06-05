# Space Defender - Windows Offline Build Instructions

## Goal
Create a self-contained Windows package so the game can run on a target PC without Python or internet access.

## What this installer does
- Bundles the Python runtime with the game code
- Includes all game assets and data files
- Produces a portable `dist\win32\SpaceDefender` or `dist\win64\SpaceDefender` folder
- Optionally generates a single NSIS installer if `makensis` is installed on the build machine

## Recommended build environment
- Windows PC with Python installed
- Python 3.8 or 3.9 recommended for broader Windows 7 compatibility
- Prefer 32-bit Python if the offline target may be Windows 7 / older hardware

## Build dependencies
The executable bundle only requires one third-party dependency at runtime:
- `pygame`

For build-time only, the installer uses:
- `pyinstaller`
- `pygame`
- optionally `makensis` if you want a `.exe` installer wrapper

## Setup before building
1. Open a Command Prompt in the `installer` directory.
2. Create and activate the build environment:
   ```bat
   conda env create -f ..\environment.yml
   conda activate py311
   ```
3. Install required packages:
   ```bat
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. If you want a one-click installer, install NSIS on the build machine:
   - https://nsis.sourceforge.io/Download

## Important: 32-bit builds really need 32-bit Python

PyInstaller's `--arch=32` flag only swaps the bootloader; the bundled CPython
interpreter is whatever the build env is. If you run `build.bat 32` while
`python` is 64-bit, PyInstaller still produces a 64-bit binary that happens to
land in `dist\win32`. That binary will not run on 32-bit Windows, and pygame
inside it will fail to load SDL ("Failed loading SDL3 / SDL2 library") on
some targets.

For a real 32-bit bundle that runs on 32-bit Windows 7/8, create a 32-bit
conda env before building:

```bat
set CONDA_SUBDIR=win-32
conda create -n py311-32 -c conda-forge python=3.11 pip
conda activate py311-32
set CONDA_SUBDIR=
pip install -r requirements.txt
```

`build.bat` checks this and refuses to write a mislabeled 32-bit folder, and
the post-build verifier re-reads the produced `SpaceDefender.exe` PE header
and aborts if the architecture does not match the requested target.

## Build command
Run (from PowerShell):
```powershell
.\build.bat all
```
- `all` → build both x64 and x86 installers
- `64` → force 64-bit build
- `32` → force 32-bit build
- no argument → auto-detects host bitness

> Note: A 32-bit build requires a 32-bit Python environment, and a 64-bit build requires a 64-bit Python environment. The build script will refuse to proceed otherwise.

## SDL runtime DLLs

`space_defender.spec` now explicitly bundles pygame's runtime DLLs
(SDL2.dll, SDL2_image.dll, SDL2_mixer.dll, SDL2_ttf.dll, portmidi.dll,
libpng16-16.dll, freetype.dll, libjpeg-9.dll, libogg-0.dll, libopus-0.dll,
zlib1.dll, …) into `dist\win*\SpaceDefender\_internal\pygame\` via
`collect_dynamic_libs('pygame')`. The matching runtime hook
(`rthook_pygame_dll.py`) calls `os.add_dll_directory` on that folder at
startup so pygame's compiled extensions can always find SDL regardless of
the launcher's working directory or PATH. The build script's
`:VerifyBundle` step also checks that `_internal\pygame\SDL2.dll` exists
and is the full pygame build (not the 292 KB PyInstaller stub) before
declaring success — this is what previously caused the "Failed loading
SDL library" runtime error on the 32-bit build.

## Output
A successful build produces:
- `installer\dist\win32\SpaceDefender\SpaceDefender.exe`
- or `installer\dist\win64\SpaceDefender\SpaceDefender.exe`

If NSIS is installed, the script also generates:
- `installer\dist\win32\Space Defender-setup-32.exe`
- or `installer\dist\win64\Space Defender-setup-64.exe`

The NSIS installer is created from the included `installer\space_defender.nsi` script.

## Offline target distribution
For a machine with no Python and no internet:
1. Copy the full folder generated under `installer\dist\win32\SpaceDefender` or `installer\dist\win64\SpaceDefender`.
2. On the target machine, run `SpaceDefender.exe` directly.

If you created the NSIS installer, you can also copy and run:
- `Space Defender-setup-32.exe`
- `Space Defender-setup-64.exe`

> The NSIS installer bundles the Python runtime, Pygame, and all required SDL libraries so a target Windows 7 machine does not need Python, Conda, or SDL installed separately.

> Note: The target machine does not need Python or Conda. Conda is only required on the build machine.

## Notes for Windows 7
- Build with Python 3.8 for best compatibility.
- Use the `32` argument if you want a 32-bit package.
- The bundled binary no longer requires Python on the target machine.

## What is included
The build now includes:
- `assets/` graphics, sounds, splash screens, backgrounds, and update assets
- `data/` configuration files such as `enemies.json`, `weapons.json`, and `profiles.json`
- Python runtime and Pygame support files (incl. SDL2 / SDL2_image / SDL2_mixer / SDL2_ttf / portmidi DLLs)

## Important
- The build machine needs internet only to install `pygame` and `pyinstaller` if not already installed.
- The target machine does not need internet or Python once the package is built.

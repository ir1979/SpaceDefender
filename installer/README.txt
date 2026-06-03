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
2. Install required packages:
   ```bat
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. If you want a one-click installer, install NSIS on the build machine:
   - https://nsis.sourceforge.io/Download

## Build command
Run:
```bat
build.bat [32|64]
```
- No argument → auto-detects host bitness
- `32` → force 32-bit build
- `64` → force 64-bit build

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

## Notes for Windows 7
- Build with Python 3.8 for best compatibility.
- Use the `32` argument if you want a 32-bit package.
- The bundled binary no longer requires Python on the target machine.

## What is included
The build now includes:
- `assets/` graphics, sounds, splash screens, backgrounds, and update assets
- `data/` configuration files such as `enemies.json`, `weapons.json`, and `profiles.json`
- Python runtime and Pygame support files

## Important
- The build machine needs internet only to install `pygame` and `pyinstaller` if not already installed.
- The target machine does not need internet or Python once the package is built.

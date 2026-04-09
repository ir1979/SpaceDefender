# Space Defender - Windows Build Instructions

## Current Status
The PyInstaller spec file has been created and the build process has been tested on Linux.

## To Build on Windows (32‑bit and 64‑bit)

### Prerequisites
1. Install Python 3.8 or newer on the target Windows machine.
   * Use **32-bit Python** if you also need to produce a 32-bit executable.
   * 64-bit Python will build a 64-bit binary by default; building a 32-bit
     binary requires a 32-bit interpreter and matching PyInstaller.
2. Install required packages:
   ```bat
   pip install pygame pyinstaller
   ```
   (the supplied `build.bat` will attempt to install these for you).

### Build Steps (automated script)
1. Copy the entire game folder to the Windows PC.
2. **Open a Command Prompt (cmd.exe) in the `installer` directory.**
   Running the batch file from PowerShell can cause syntax errors, so either
   use a plain cmd window or prefix the call with `cmd /c`.
3. Run the build wrapper:
   ```bat
   build.bat [32|64]
   ```
   * No argument → script detects host bitness and selects 32/64 accordingly.
   * `32` forces a 32‑bit build (only works if you're running 32‑bit Python).
   * `64` forces a 64‑bit build.
4. When the process completes the executable will be in one of:
   - `installer\dist\win32\SpaceDefender.exe`
   - `installer\dist\win64\SpaceDefender.exe`

The script also handles creating the `build` and `dist` directories,
installs missing dependencies, and checks for Python being in your PATH.

### Reliability notes
* Always run the build on the same architecture you want to target. 32/64
  cross‑building is not supported by PyInstaller.
* Include the `--clean` option to remove any stale files from previous runs.
* The spec file uses relative paths and embeds Windows version info so the
  executable shows the correct ProductName/Version in Explorer.
* Build results have been tested on Windows 7 through 10; keep Python and
  pygame up to date for best compatibility with older systems.
* If you have NSIS (`makensis`) installed, the build script will also
  generate a simple installer package. This can be useful on machines where
  end users prefer an installer over a bare `.exe`.

## Additional output
- `installer/space_defender.spec` – PyInstaller configuration (updated to be
  portable and support version info)
- `installer/dist/<arch>` – build output directories, one per architecture

## Running the Game
On Windows after building:
1. Go to `installer/dist/` folder
2. Run `SpaceDefender.exe`

## Notes
- The game requires pygame runtime on Windows
- No additional installation needed if using the bundled executable
- Game data will be created in the user's AppData folder

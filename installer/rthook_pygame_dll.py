"""
PyInstaller runtime hook for Space Defender.

When the bundle is launched on Windows, CPython loads pygame's compiled
extension modules (e.g. pygame\_sdl2init.cp311-win_*.pyd). Those .pyd files
load pygame's SDL runtime (SDL2.dll, SDL2_image.dll, SDL2_mixer.dll,
SDL2_ttf.dll, portmidi.dll, libpng16-16.dll, ...) via the standard Windows
DLL search order, which on Win7/8/10 looks in:

    1. The directory of the loaded .pyd
    2. The system directories
    3. The PATH directories

PyInstaller places the .pyd files under _internal\pygame\ and PyInstaller
*does* put the DLLs next to them when collect_dynamic_libs('pygame') is used
in the spec. The SDL loader however calls LoadLibraryW with the bare DLL
name in some code paths and depends on AddDllDirectory / the process DLL
search path. On older Windows targets (and when launched from a non-standard
working directory) this can still fail.

This hook runs at interpreter startup and explicitly registers the pygame
package directory with os.add_dll_directory, which makes the SDL runtime
DLLs discoverable regardless of the launcher's working directory or PATH.
It is a no-op on non-Windows and on non-frozen runs.
"""

import os
import sys


def _register_pygame_dll_dir():
    if not sys.platform.startswith("win"):
        return
    if not getattr(sys, "frozen", False):
        return

    meipass = getattr(sys, "_MEIPASS", None)
    if not meipass:
        return

    candidates = [
        os.path.join(meipass, "_internal", "pygame"),
        os.path.join(meipass, "pygame"),
    ]
    for d in candidates:
        if os.path.isdir(d):
            try:
                os.add_dll_directory(d)
            except (OSError, AttributeError):
                # add_dll_directory was added in Python 3.8 on Windows; older
                # versions fall back to the default search order, which is
                # good enough for our purposes.
                pass


_register_pygame_dll_dir()

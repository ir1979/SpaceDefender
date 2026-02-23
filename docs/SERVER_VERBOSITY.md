# Server Verbosity Control

## Overview
The Space Defender multiplayer server now supports configurable verbosity levels to control how much output is displayed during execution.

## Usage

### Command-Line Arguments

Run the server with a specific verbosity level using the `-v` or `--verbose` flag:

```bash
# Default verbosity (level 1)
python server.py 35555

# Silent mode - only critical errors
python server.py 35555 -v 0

# Low verbosity (default) - connections and key events
python server.py 35555 -v 1

# Medium verbosity - above + enemy/bullet details
python server.py 35555 -v 2

# High verbosity - all debug information
python server.py 35555 -v 3
```

Or using the long form:
```bash
python server.py 35555 --verbose 2
```

## Verbosity Levels

| Level | Name | Output |
|-------|------|--------|
| **0** | Silent | Only critical errors printed |
| **1** | Low (default) | Connection events, game start/end, player deaths, disconnects |
| **2** | Medium | Above + failed state transmissions, game loop tick counts, waiting state attempts |
| **3** | High | Above + player shooting, enemy spawning, bullet count changes |

## Output Examples

### Level 0 (Silent)
```
(no output during normal operation)
```

### Level 1 (Low - Default)
```
============================================================
  SPACE DEFENDER - MULTIPLAYER SERVER
============================================================
  Host: 127.0.0.1
  Port: 35555
  Max Players: 2
  Mode: Co-op
  Verbosity: 1 (0=silent, 1=low, 2=med, 3=high)
============================================================

[SERVER] Listening on 127.0.0.1:35555
[SERVER] Waiting for clients to connect...
[SERVER] Press Ctrl+C to stop server

[SERVER] ✓ Player 1 connected from 127.0.0.1:56789
[SERVER] 1/2 players connected
[SERVER] ✓ Player 2 connected from 127.0.0.1:56790
[SERVER] Two players ready. Starting game...
```

### Level 2 (Medium)
```
(All Level 1 output, plus:)
[SERVER] Created 2 player slots (headless mode)
[SERVER] Waiting for 2 players to connect...
[SERVER] Game loop initialized - simulation starting
[SERVER] Game loop: 600 ticks, 2/2 clients, 10 bullets, 15 enemies, L1
```

### Level 3 (High)
```
(All Level 2 output, plus:)
[SERVER] Logic thread started.
[SERVER] Player 1 fired 2 bullet(s) at (200, 350)
[SERVER] Enemy spawned: basic (Total: 5)
[SERVER] Bullets: 8 → 10
[SERVER] Bullets: 10 → 8
```

## Verbosity Configuration

The verbosity level is controlled by the global `VERBOSE_LEVEL` variable in `server.py`, which is set based on command-line arguments.

### vprint() Function

All server output uses the `vprint()` function instead of direct `print()` calls:

```python
def vprint(msg, level=1, end='\n'):
    """Print message based on configured verbosity level.
    
    Levels:
    0 - Silent (errors only)
    1 - Low (connections, key events)
    2 - Medium (above + enemy/bullet details)
    3 - High (all debug info)
    """
    if VERBOSE_LEVEL >= level:
        print(msg, end=end)
```

For example:
```python
# Always shown (if level >= 1)
vprint("[SERVER] Player connected", level=1)

# Only shown in medium+ verbosity
vprint("[SERVER] Enemy spawned", level=2)

# Only shown in high verbosity
vprint("[SERVER] Bullet count changed", level=3)

# Always shown, even in silent mode (errors only)
vprint("[CRITICAL] Server error", level=0)
```

## Benefits

- **Production**: Run with `-v 0` to suppress normal output, seeing only errors
- **Testing**: Run with `-v 2` or `-v 3` to track game logic and networking details
- **Debugging**: Use `-v 3` to monitor every significant event
- **Cleaner Logs**: Use `-v 1` for important events without noise

## Backward Compatibility

The server maintains backward compatibility:
- Legacy syntax: `python server.py 35555` works and defaults to `-v 1`
- Legacy syntax with verbosity: `python server.py 35555 -v 2` also supported

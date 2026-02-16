#!/usr/bin/env python3
"""Test server startup without network binding"""
import os
import sys

# Add project root to path (go up 3 directories from test file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up pygame for headless mode
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
pygame.init()

# Test 1: Imports
print("[TEST] Testing imports...")
try:
    from core.game import Game
    from config.settings import game_config, GameState
    from entities.player import Player
    from systems.logger import get_logger
    print("[OK] All imports successful")
except Exception as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Test 2: Logger setup
print("[TEST] Setting up logger...")
try:
    logger = get_logger('test')
    logger.info("Logger works")
    print("[OK] Logger setup successful")
except Exception as e:
    print(f"[FAIL] Logger error: {e}")
    sys.exit(1)

# Test 3: Game instance creation (server mode)
print("[TEST] Creating Game instance in server mode...")
try:
    game = Game(None, is_server=True)
    print(f"[OK] Game created: is_server={game.is_server}")
except Exception as e:
    print(f"[FAIL] Game creation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create players
print("[TEST] Creating players...")
try:
    game.players.append(Player(game_config.SCREEN_WIDTH // 3, game_config.SCREEN_HEIGHT - 100))
    game.players.append(Player(2 * game_config.SCREEN_WIDTH // 3, game_config.SCREEN_HEIGHT - 100))
    print(f"[OK] Players created: {len(game.players)} players")
except Exception as e:
    print(f"[FAIL] Player creation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Initialize game
print("[TEST] Initializing game...")
try:
    game.init_game()
    game.state = GameState.PLAYING
    print("[OK] Game initialized")
except Exception as e:
    print(f"[FAIL] Game init error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Single update iteration
print("[TEST] Running single update...")
try:
    game.update()
    print("[OK] Update successful")
except Exception as e:
    print(f"[FAIL] Update error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: get_game_state
print("[TEST] Testing get_game_state...")
try:
    from server import get_game_state

    # Add a bullet and a powerup so serialization includes them
    from entities.bullet import BulletFactory
    from entities.powerup import PowerUp

    bullet = BulletFactory.create('default', 200, 200, -10, 1, 0)
    game.bullets.add(bullet)
    game.all_sprites.add(bullet)

    powerup = PowerUp(150, 100, 'shield')
    game.powerups.add(powerup)
    game.all_sprites.add(powerup)

    state = get_game_state(game)

    assert 'bullets' in state and isinstance(state['bullets'], list)
    assert len(state['bullets']) >= 1
    assert 'weapon_type' in state['bullets'][0] or 'type' in state['bullets'][0]

    assert 'powerups' in state and isinstance(state['powerups'], list)
    assert len(state['powerups']) >= 1
    assert 'power_type' in state['powerups'][0]

    print(f"[OK] Game state: {len(state['players'])} players, {len(state['enemies'])} enemies, {len(state['bullets'])} bullets, {len(state['powerups'])} powerups")
except Exception as e:
    print(f"[FAIL] get_game_state error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[ALL TESTS PASSED]")

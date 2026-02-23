#!/usr/bin/env python
"""
Test script to simulate "PLAY ONLINE" action and capture crash details
"""
import traceback
import sys
import os

# Add project root to path (go up 3 directories from test file)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up pygame for headless mode
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
pygame.init()

import threading
import time
from server import main as server_main, shutdown_event

def test_play_online():
    print("=" * 60)
    print("TESTING PLAY ONLINE CONNECTION")
    print("=" * 60)
    
    try:
        print("\n[1] Creating game instance...")
        from core.game import Game
        game = Game(None, is_server=False)
        print(f"✓ Game created")
        print(f"  - is_network_mode: {game.is_network_mode}")
        print(f"  - is_server: {game.is_server}")
        print(f"  - Assets: {game.assets is not None}")
        
        print("\n[2] Starting test server on port 9999...")
        server_args = [sys.argv[0], '9999']
        shutdown_event.clear()
        server_thread = threading.Thread(target=server_main, args=(server_args,), daemon=True)
        server_thread.start()
        # Give server a moment to bind
        time.sleep(1)

        try:
            print("\n[3] Calling connect_to_server()...")
            result = game.connect_to_server('127.0.0.1', 9999)
            print(f"✓ connect_to_server returned: {result}")
            print(f"  - is_network_mode: {game.is_network_mode}")
            print(f"  - server_socket: {game.server_socket}")

            assert result, "Connection failed"
        finally:
            shutdown_event.set()
            server_thread.join(timeout=3)
            shutdown_event.clear()
        
        print("\n[3] Calling init_game()...")
        game.init_game()
        print(f"✓ init_game() completed")
        print(f"  - player: {game.player}")
        print(f"  - all_sprites: {len(game.all_sprites)}")
        print(f"  - current_level: {game.current_level}")
        print(f"  - level: {game.level}")
        
        print("\n[4] Checking first update with network mode...")
        game.state = 2  # GameState.PLAYING
        # Simulate a quick update
        game.handle_events()
        print(f"✓ First update completed")
        print(f"  - state: {game.state}")
        
        print("\n" + "=" * 60)
        print("✓ ALL PLAY_ONLINE TESTS PASSED")
        print("=" * 60)
        # test completed successfully
        
    except Exception as e:
        print(f"\n✗ ERROR during PLAY ONLINE: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    try:
        test_play_online()
        sys.exit(0)
    except Exception:
        sys.exit(1)

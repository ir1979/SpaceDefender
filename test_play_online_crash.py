#!/usr/bin/env python
"""
Test script to simulate "PLAY ONLINE" action and capture crash details
"""
import traceback
import sys

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
        
        print("\n[2] Calling connect_to_server()...")
        result = game.connect_to_server('127.0.0.1', 9999)
        print(f"✓ connect_to_server returned: {result}")
        print(f"  - is_network_mode: {game.is_network_mode}")
        print(f"  - server_socket: {game.server_socket}")
        
        if not result:
            print("✗ Connection failed")
            return False
        
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
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR during PLAY ONLINE: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_play_online()
    sys.exit(0 if success else 1)

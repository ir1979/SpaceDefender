"""
Test Script - Verify Player Shooting Mechanism
Tests that headless players can shoot properly
"""

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

from entities.player import Player
from config.settings import game_config

def test_player_shooting():
    """Test that headless players can shoot"""
    print("\n" + "="*60)
    print("  PLAYER SHOOTING TEST")
    print("="*60 + "\n")
    
    # Test 1: Regular player (single-player mode)
    print("Test 1: Regular Player (Single-Player Mode)")
    print("-" * 60)
    player1 = Player(100, 100, headless=False)
    print(f"✓ Created player: headless={player1.headless}, fire_cooldown={player1.fire_cooldown}")
    
    bullets = player1.shoot()
    print(f"✓ First shoot: {len(bullets)} bullets created, fire_cooldown={player1.fire_cooldown}")
    assert len(bullets) == 1, "Should create 1 bullet"
    assert player1.fire_cooldown > 0, "Should have cooldown after shooting"
    
    bullets = player1.shoot()
    print(f"✓ Second shoot (immediate): {len(bullets)} bullets, fire_cooldown={player1.fire_cooldown}")
    assert len(bullets) == 0, "Should be blocked by cooldown"
    
    # Simulate updates to decrement cooldown
    initial_cooldown = player1.fire_cooldown
    for i in range(initial_cooldown):
        player1.fire_cooldown -= 1  # Manually decrement for test
    print(f"✓ After {initial_cooldown} updates: fire_cooldown={player1.fire_cooldown}")
    
    bullets = player1.shoot()
    print(f"✓ Third shoot (after cooldown): {len(bullets)} bullets\n")
    assert len(bullets) == 1, "Should create bullet after cooldown expires"
    print("✓ Test 1 PASSED\n")
    
    # Test 2: Headless player (server mode)
    print("Test 2: Headless Player (Server Mode)")
    print("-" * 60)
    player2 = Player(200, 200, headless=True)
    print(f"✓ Created headless player: headless={player2.headless}, fire_cooldown={player2.fire_cooldown}")
    
    bullets = player2.shoot()
    print(f"✓ First shoot: {len(bullets)} bullets created, fire_cooldown={player2.fire_cooldown}")
    assert len(bullets) == 1, "Should create 1 bullet"
    assert player2.fire_cooldown > 0, "Should have cooldown after shooting"
    
    # Test that update() properly decrements cooldown in headless mode
    initial_cooldown = player2.fire_cooldown
    player2.update()  # This should decrement cooldown
    print(f"✓ After update(): fire_cooldown went from {initial_cooldown} to {player2.fire_cooldown}")
    assert player2.fire_cooldown == initial_cooldown - 1, "Update should decrement cooldown"
    
    bullets = player2.shoot()
    print(f"✓ Second shoot (immediate): {len(bullets)} bullets, fire_cooldown={player2.fire_cooldown}")
    assert len(bullets) == 0, "Should be blocked by cooldown"
    
    # Decrement cooldown to 0
    while player2.fire_cooldown > 0:
        player2.update()
    print(f"✓ After multiple updates: fire_cooldown={player2.fire_cooldown}")
    
    bullets = player2.shoot()
    print(f"✓ Third shoot (after cooldown): {len(bullets)} bullets\n")
    assert len(bullets) == 1, "Should create bullet after cooldown expires"
    print("✓ Test 2 PASSED\n")
    
    # Test 3: Network-controlled player (client in multiplayer)
    print("Test 3: Network-Controlled Player (Multiplayer Client)")
    print("-" * 60)
    player3 = Player(300, 300, network_controlled=True)
    print(f"✓ Created network player: network_controlled={player3.network_controlled}, fire_cooldown={player3.fire_cooldown}")
    
    bullets = player3.shoot()
    print(f"✓ First shoot: {len(bullets)} bullets created, fire_cooldown={player3.fire_cooldown}")
    assert len(bullets) == 1, "Should create 1 bullet"
    
    # Test that update() properly decrements cooldown in network mode
    initial_cooldown = player3.fire_cooldown
    player3.update()
    print(f"✓ After update(): fire_cooldown went from {initial_cooldown} to {player3.fire_cooldown}")
    assert player3.fire_cooldown == initial_cooldown - 1, "Update should decrement cooldown"
    print("✓ Test 3 PASSED\n")
    
    # Test 4: Rapid fire power-up
    print("Test 4: Rapid Fire Power-Up")
    print("-" * 60)
    player4 = Player(400, 400, headless=True)
    player4.activate_powerup('rapid_fire')
    print(f"✓ Activated rapid fire: rapid_fire={player4.rapid_fire}")
    
    bullets = player4.shoot()
    print(f"✓ Shoot with rapid fire: fire_cooldown={player4.fire_cooldown} (should be 5)")
    assert player4.fire_cooldown == 5, "Rapid fire should reduce cooldown to 5"
    print("✓ Test 4 PASSED\n")
    
    # Test 5: Triple shot power-up
    print("Test 5: Triple Shot Power-Up")
    print("-" * 60)
    player5 = Player(500, 500, headless=True)
    player5.activate_powerup('triple_shot')
    print(f"✓ Activated triple shot: triple_shot={player5.triple_shot}")
    
    bullets = player5.shoot()
    print(f"✓ Shoot with triple shot: {len(bullets)} bullets created")
    assert len(bullets) == 3, "Triple shot should create 3 bullets"
    print("✓ Test 5 PASSED\n")
    
    print("="*60)
    print("  ALL TESTS PASSED ✓")
    print("="*60)
    print("\nConclusion:")
    print("  • Regular players can shoot correctly")
    print("  • Headless players can shoot correctly")
    print("  • Network-controlled players can shoot correctly")
    print("  • Fire rate cooldown works properly")
    print("  • Power-ups work correctly")
    print("\nYour shooting mechanism is working!\n")
    print("If shooting still doesn't work in multiplayer:")
    print("  1. Verify server is using player_fixed_v2.py")
    print("  2. Check server creates players with headless=True")
    print("  3. Check network communication (see SHOOTING_FIX_GUIDE.txt)")
    print()

if __name__ == "__main__":
    try:
        test_player_shooting()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        print("This means the player shooting mechanism is broken.")
        print("Make sure you're using player_fixed_v2.py\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

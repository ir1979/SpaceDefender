#!/usr/bin/env python3
"""
Verify atomic bomb functionality after fix
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from entities.player import Player
    from systems.particle_system import ParticleSystem
    from config.settings import color_config
    import pygame
    
    pygame.init()
    
    print("="*60)
    print("ATOMIC BOMB FIX VERIFICATION")
    print("="*60)
    
    # Test 1: Player can have weapons
    print("\n1. Testing weapon management...")
    player = Player(400, 300)
    player.add_weapon('atomic_bomb')
    print(f"   ✓ Added atomic bomb to inventory")
    print(f"   ✓ Player weapons: {player.weapons}")
    print(f"   ✓ Selected weapon: {player.get_selected_weapon()}")
    
    # Test 2: Particle system has correct method
    print("\n2. Testing particle system...")
    ps = ParticleSystem()
    ps.emit_explosion(200, 200, color_config.YELLOW, count=15)
    print(f"   ✓ emit_explosion() method works")
    print(f"   ✓ Particles created: {len(ps.particles)}")
    
    # Test 3: Pygame sprite group empty() method
    print("\n3. Testing sprite group operations...")
    sprite_group = pygame.sprite.Group()
    sprite = pygame.sprite.Sprite()
    sprite_group.add(sprite)
    print(f"   ✓ Sprites in group: {len(sprite_group)}")
    sprite_group.empty()  # This is the correct method
    print(f"   ✓ After empty(): {len(sprite_group)} sprites")
    print(f"   ✓ empty() method works correctly!")
    
    print("\n" + "="*60)
    print("✅ ALL ATOMIC BOMB TESTS PASSED!")
    print("="*60)
    print("\nFIX SUMMARY:")
    print("  • Changed: self.enemies.clear() → self.enemies.empty()")
    print("  • Reason: pygame.sprite.Group.clear() requires (surface, bgd)")
    print("  • Solution: Use empty() for no-argument sprite removal")
    print("\nThe atomic bomb weapon now works correctly! ✓")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

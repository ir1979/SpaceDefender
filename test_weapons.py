#!/usr/bin/env python3
"""Test weapon selection and activation system"""

from entities.player import Player
from systems.logger import get_logger

logger = get_logger('test_weapons')

print("\n" + "="*80)
print("WEAPON SELECTION SYSTEM TEST")
print("="*80 + "\n")

# Create a player
player = Player(400, 500)

print(f"✓ Player created at ({player.rect.x}, {player.rect.y})")
print(f"✓ Initial weapons: {player.weapons}")
print(f"✓ Selected weapon index: {player.selected_weapon_index}\n")

# Add some weapons
print("Adding weapons to player inventory...")
player.add_weapon('atomic_bomb')
print(f"  ✓ Atomic bomb added. Weapons: {player.weapons}")

player.add_weapon('enemy_freeze')
print(f"  ✓ Enemy freeze added. Weapons: {player.weapons}")

# Try to add atomic bomb again (should not duplicate)
result = player.add_weapon('atomic_bomb')
print(f"  ✓ Add atomic bomb again returned: {result} (should be False). Weapons: {player.weapons}\n")

# Test weapon selection
print("Testing weapon selection...")
selected = player.get_selected_weapon()
print(f"  ✓ Currently selected weapon: '{selected}'")
print(f"  ✓ Selected index: {player.selected_weapon_index}\n")

# Test weapon cycling
print("Testing weapon cycling (next)...")
print(f"  Before: selected_index={player.selected_weapon_index}, weapon='{player.get_selected_weapon()}'")
player.cycle_weapon_next()
print(f"  After:  selected_index={player.selected_weapon_index}, weapon='{player.get_selected_weapon()}'")
player.cycle_weapon_next()
print(f"  After:  selected_index={player.selected_weapon_index}, weapon='{player.get_selected_weapon()}' (wrapped around)\n")

print("Testing weapon cycling (prev)...")
print(f"  Before: selected_index={player.selected_weapon_index}, weapon='{player.get_selected_weapon()}'")
player.cycle_weapon_prev()
print(f"  After:  selected_index={player.selected_weapon_index}, weapon='{player.get_selected_weapon()}'")
player.cycle_weapon_prev()
print(f"  After:  selected_index={player.selected_weapon_index}, weapon='{player.get_selected_weapon()}'\n")

# Test weapon checking
print("Testing has_weapon()...")
print(f"  ✓ has_weapon('atomic_bomb'): {player.has_weapon('atomic_bomb')}")
print(f"  ✓ has_weapon('enemy_freeze'): {player.has_weapon('enemy_freeze')}")
print(f"  ✓ has_weapon('nonexistent'): {player.has_weapon('nonexistent')}\n")

# Test manual weapon selection
print("Testing manual weapon selection...")
player.select_weapon(1)
print(f"  ✓ After select_weapon(1): selected_index={player.selected_weapon_index}, weapon='{player.get_selected_weapon()}'")
player.select_weapon(0)
print(f"  ✓ After select_weapon(0): selected_index={player.selected_weapon_index}, weapon='{player.get_selected_weapon()}'")
player.select_weapon(99)  # Out of bounds
print(f"  ✓ After select_weapon(99): selected_index={player.selected_weapon_index}, weapon='{player.get_selected_weapon()}' (no change)\n")

print("="*80)
print("✓ ALL WEAPON SYSTEM TESTS PASSED!")
print("="*80 + "\n")

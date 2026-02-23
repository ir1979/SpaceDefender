#!/usr/bin/env python3
"""Quick test to verify all 12 shop items are created correctly"""

from ui.menus import Shop
from systems.asset_manager import AssetManager
from systems.logger import get_logger

logger = get_logger('test_shop')

# Initialize assets (minimal)
class MockAssets:
    def __init__(self):
        self.fonts = {
            'large': None,
            'medium': None,
            'small': None,
        }
    
    def play_sound(self, sound_name, volume):
        pass

assets = MockAssets()
shop = Shop(assets)

print(f"✓ Shop created with {len(shop.items)} items")
print(f"✓ Max visible items: {shop.items.__len__()}")
print()

print("SHOP ITEMS:")
print("-" * 100)

for i, item in enumerate(shop.items, 1):
    effect = item['effect']
    name = item['name']
    cost = item['cost']
    desc = item['description']
    level = item['level']
    max_level = item['max_level']
    
    print(f"{i:2d}. [{effect:15s}] {name:25s} | Cost: {cost:3d} | Desc: {desc}")

print("-" * 100)
print()

# Verify all required items are present
required_items = [
    'Max Health +20',
    'Damage +10',
    'Speed +1',
    'Fire Rate +2',
    'Heal 50 HP',
    '⚡ Triple Shot',
    '🔫 Rapid Fire Upgrade',
    '🎯 Piercing Shots',
    '🛡️ Shield',
    '❤️ Extra Life',
    '💣 ATOMIC BOMB',
    '🌪️ Enemy Freeze',
]

item_names = [item['name'] for item in shop.items]

print("VERIFICATION:")
print("-" * 100)
for req_item in required_items:
    if req_item in item_names:
        print(f"✓ {req_item}")
    else:
        print(f"✗ MISSING: {req_item}")

print("-" * 100)
print()
print(f"Summary: {len(item_names)} items created")
print(f"Expected: {len(required_items)} items")
print(f"Match: {len(item_names) == len(required_items)}")

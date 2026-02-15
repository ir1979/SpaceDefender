#!/usr/bin/env python3
"""
Sprite Renamer for Space Defender
Maps extracted sprites to game asset names
"""

from pathlib import Path
import shutil

# Mapping of extracted filenames to game asset names
SPRITE_MAPPING = {
    # Player ships
    'playerShip1_blue.png': 'spaceship.png',
    'playerShip2_blue.png': 'fighter.png',
    
    # Bullets/Projectiles
    'laserBlue01.png': 'bullet_laser.png',
    'beam0.png': 'bullet_basic.png',
    'laserRed01.png': 'bullet_plasma.png',
    'laserGreen02.png': 'bullet_missile.png',
    
    # Enemies
    'enemyBlue1.png': 'enemy_basic.png',
    'enemyBlue2.png': 'enemy_fast.png',
    'enemyRed1.png': 'enemy_tank.png',
    'enemyGreen1.png': 'enemy_weaver.png',
    'ufoBlue.png': 'enemy_boss.png',
}

def rename_sprites(sprites_dir):
    """Rename extracted sprites to match game requirements"""
    sprites_dir = Path(sprites_dir)
    renamed = 0
    skipped = 0
    
    for old_name, new_name in SPRITE_MAPPING.items():
        old_path = sprites_dir / old_name
        new_path = sprites_dir / new_name
        
        if old_path.exists():
            if new_path.exists():
                print(f"  ⚠ Skip: {new_name} (already exists)")
                skipped += 1
            else:
                shutil.move(old_path, new_path)
                print(f"  ✓ {old_name} → {new_name}")
                renamed += 1
        else:
            print(f"  ✗ Not found: {old_name}")
    
    print(f"\n✓ Renamed {renamed} sprites, Skipped {skipped}")

if __name__ == '__main__':
    sprites_dir = r'c:\Users\Reza Mortazavi\Dropbox\Projects\Ali School\Kharazmi\Game\space_defender\assets\sprites'
    
    print("Sprite Renaming")
    print("=" * 50)
    print(f"Directory: {sprites_dir}")
    print("=" * 50)
    
    rename_sprites(sprites_dir)
    
    print("\n" + "=" * 50)
    print("Core game assets renamed:")
    print("  • spaceship.png (player)")
    print("  • fighter.png (player variant)")
    print("  • bullet_laser.png")
    print("  • bullet_basic.png")
    print("  • bullet_plasma.png")
    print("  • bullet_missile.png")
    print("  • enemy_basic.png")
    print("  • enemy_fast.png")
    print("  • enemy_tank.png")
    print("  • enemy_weaver.png")
    print("  • enemy_boss.png")
    print("\n✓ Additional 283 assets available for UI, effects, etc.")

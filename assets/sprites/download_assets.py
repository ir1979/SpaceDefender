#!/usr/bin/env python3
"""
Game Assets Downloader for Space Defender
Downloads free game assets from open-source resources
"""

import urllib.request
import os
from pathlib import Path

# Free game asset resources
ASSET_RESOURCES = {
    'OpenGameArt': 'https://opengameart.org',
    'Kenney.nl': 'https://kenney.nl',
    'Itch.io': 'https://itch.io/game-assets',
    'Freepik': 'https://www.freepik.com',
    'Pixabay': 'https://pixabay.com',
}

INSTRUCTIONS = """
# Game Assets Download Guide for Space Defender

## Free Asset Resources

### 1. OpenGameArt.org
- URL: https://opengameart.org
- Search: "space shooter", "spaceship", "bullet", "enemy"
- License: Various (check each asset)
- Quality: Professional

### 2. Kenney.nl
- URL: https://kenney.nl
- Search: "space", "shooter", "2D"
- License: CC0 (Free for commercial use)
- Quality: Excellent pixel art

### 3. Itch.io Game Assets
- URL: https://itch.io/game-assets
- Search: "space shooter assets", "2D sprites"
- License: Various (filter by CC0)
- Quality: Good variety

### 4. Pixabay
- URL: https://pixabay.com
- Search: "spaceship", "explosion"
- License: Free for commercial use
- Quality: Varies

### 5. Freepik
- URL: https://www.freepik.com
- Search: "space game assets"
- License: Check each (many free with attribution)
- Quality: High quality vectors and rasters

## How to Add Downloaded Assets

### Step 1: Find Assets
1. Visit one of the resources above
2. Search for: "spaceship", "bullet", "enemy", "space shooter"
3. Download PNG files with transparent background (best)

### Step 2: Organize Files
```
Downloaded files should be named:
- spaceship.png
- fighter.png
- bullet_basic.png
- bullet_laser.png
- bullet_plasma.png
- bullet_missile.png
- enemy_basic.png
- enemy_fast.png
- enemy_tank.png
- enemy_weaver.png
- enemy_boss.png
```

### Step 3: Place in Sprite Directory
1. Copy PNG files to: `assets/sprites/`
2. Restart the game
3. Assets load automatically!

## Recommended Assets

### For Spaceships
- Kenney.nl: "Space Shooter Redux" pack
- OpenGameArt: Search "spaceship"
- Free pixel art spaceships

### For Enemies
- Kenney.nl: "Space Shooter" enemy sprites
- OpenGameArt: "Space enemies"
- Various difficulty levels

### For Bullets/Effects
- Kenney.nl: "Impact effects" pack
- Itch.io: "Particle effects"
- Bullet sprite packs

### For Polish
- Explosions, particle effects
- UI elements
- Background tiles

## Batch Download Tools

### Using command line (Windows)
```powershell
# Example: Download from a direct URL
$url = "https://example.com/spaceship.png"
$output = "assets/sprites/spaceship.png"
Invoke-WebRequest -Uri $url -OutFile $output
```

### Using Python (Cross-platform)
```python
import urllib.request

url = "https://example.com/spaceship.png"
output_path = "assets/sprites/spaceship.png"
urllib.request.urlretrieve(url, output_path)
print(f"Downloaded: {output_path}")
```

## License Considerations

⚠️ **IMPORTANT**: Check licenses before using!

- **CC0** - Free, no attribution needed
- **CC-BY** - Free, must give attribution
- **CC-BY-SA** - Free, must attribute and use same license
- **Commercial** - Check terms carefully

Most resources have filters to show only free/commercial-use assets.

## Tips

1. **Transparent PNGs work best** - Easier to integrate with game
2. **Consistent style** - Mix assets carefully for cohesive look
3. **Test sizing** - Assets will be auto-scaled to 50-100px
4. **Backup originals** - Keep downloaded assets in a backup folder
5. **Check dimensions** - Square or near-square works best

## Quick Start

1. Visit https://kenney.nl
2. Download "Space Shooter Redux" pack (free CC0)
3. Extract PNG files
4. Rename to match space_defender names
5. Copy to assets/sprites/
6. Run game!

## Need Help?

If assets don't load:
- Check file names match exactly
- Verify PNG format (not JPG)
- Ensure transparent background
- Check assets/sprites/ directory
- Restart game

Game will use default shapes if sprites aren't found - no errors!
"""

def main():
    sprite_dir = Path(__file__).parent
    guide_path = sprite_dir / "DOWNLOAD_GUIDE.md"
    
    with open(guide_path, 'w') as f:
        f.write(INSTRUCTIONS)
    
    print("✓ Downloaded guide created: DOWNLOAD_GUIDE.md")
    print("\nFree Game Asset Resources:")
    for name, url in ASSET_RESOURCES.items():
        print(f"  • {name}: {url}")
    print("\nNext steps:")
    print("  1. Read: assets/sprites/DOWNLOAD_GUIDE.md")
    print("  2. Visit recommended resources above")
    print("  3. Download PNG sprites")
    print("  4. Copy to: assets/sprites/")
    print("  5. Restart the game")

if __name__ == '__main__':
    main()

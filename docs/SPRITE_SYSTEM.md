# Space Defender - Sprite System Documentation

## Overview

The Space Defender game now has a flexible **sprite loading system** that supports custom PNG/SVG/image files for game artifacts while gracefully falling back to procedurally-generated shapes if images aren't found.

## How It Works

### System Flow

1. **Game Startup** → Asset Manager initializes
2. **Sprite Loading** → Scans `assets/sprites/` directory for image files
3. **Entity Creation** → When creating entities, ShapeRenderer checks for sprites first
4. **Rendering**:
   - **If sprite exists**: Load and scale the PNG/image file
   - **If sprite missing**: Use procedurally-generated shape (from shapes.json)

### Key Features

✅ **Automatic Detection** - Scans directory for PNG, JPG, BMP, GIF files
✅ **Smart Fallback** - Uses default shapes if images aren't found
✅ **Dynamic Scaling** - Automatically scales sprites to entity size
✅ **No Overhead** - Only loads found sprites; no errors for missing ones
✅ **Easy Updates** - Simply add/remove PNG files to enable/disable sprites

## Directory Structure

```
space_defender/
├── assets/
│   └── sprites/
│       ├── README.md                    # Instructions
│       ├── generate_examples.py          # Example sprite generator
│       ├── spaceship.png                 # ✓ Loaded
│       ├── fighter.png                   # ✓ Loaded
│       ├── bullet_basic.png              # ✓ Loaded
│       ├── bullet_laser.png              # ✓ Loaded
│       ├── bullet_plasma.png             # ✓ Loaded
│       ├── bullet_missile.png            # ✓ Loaded
│       ├── enemy_basic.png               # ✓ Loaded
│       ├── enemy_fast.png                # ✓ Loaded
│       ├── enemy_tank.png                # ✓ Loaded
│       ├── enemy_weaver.png              # ✓ Loaded
│       └── enemy_boss.png                # ✓ Loaded
```

## Available Sprite Names

### Player Ships
- `spaceship` - Classic spaceship
- `fighter` - Sleek fighter jet

### Bullets
- `bullet_basic` - Standard bullet
- `bullet_laser` - Laser beam
- `bullet_plasma` - Energy orb
- `bullet_missile` - Rocket missile

### Enemies
- `enemy_basic` - Basic enemy
- `enemy_fast` - Fast enemy
- `enemy_tank` - Heavy tank
- `enemy_weaver` - Weaving enemy
- `enemy_boss` - Boss enemy

## Adding Custom Sprites

### Quick Start

1. **Create an image** (PNG recommended with transparency)
2. **Name it after a shape** (e.g., `spaceship.png`, `enemy_basic.png`)
3. **Place in** `assets/sprites/` directory
4. **Restart the game** - it will load automatically!

### Image Guidelines

- **Format**: PNG (transparency supported)
- **Size**: 50-100 pixels (will auto-scale)
- **Background**: Transparent (PNG alpha channel)
- **Quality**: Match your game's aesthetic

### Example: Adding a Custom Spaceship

```
1. Create spaceship.png (50x60 pixels)
2. Copy to: assets/sprites/spaceship.png
3. Run game - it loads automatically!
```

## Testing the System

### Run Example Generator

```bash
cd assets/sprites
python generate_examples.py
```

This creates simple example sprites for all artifact types (already done).

### Running the Game

```bash
python main.py
```

Check console output:
```
Loading sprites from .../assets/sprites/...
  ✓ Loaded sprite: spaceship.png
  ✓ Loaded sprite: enemy_basic.png
  ...
Loaded 11 sprite(s)
```

## Default Shapes (Fallback)

If sprites aren't found, the game uses procedurally-generated shapes defined in `data/shapes.json`:

- `spaceship`, `fighter` - Player ships
- `bullet_*` - Various bullet types
- `enemy_*` - Enemy types
- `hexagon`, `cross`, `crescent` - Additional shapes

## Technical Details

### Asset Manager Changes

- Added `sprites` dictionary to store loaded images
- Added `load_sprites()` method to scan and load image files
- Added `get_sprite()` and `has_sprite()` methods for checking availability
- Supports: PNG, JPG, JPEG, BMP, GIF

### ShapeRenderer Changes

- Added `asset_manager` static property
- Added `set_asset_manager()` method for initialization
- Modified `create_shape()` to check sprites first before rendering procedural shapes

### Game Initialization

```python
# In core/game.py
from entities.base_entity import ShapeRenderer
ShapeRenderer.set_asset_manager(self.assets)
```

## Benefits

✨ **No Errors** - Missing sprites don't break the game
✨ **Gradual Replacement** - Add sprites at your own pace
✨ **Performance** - Only loads found files
✨ **Flexibility** - Switch between sprites and shapes easily
✨ **Maintainability** - Clean separation of concerns

## Future Enhancements

- SVG support (vector graphics)
- Sprite animation support
- Sprite variants (damage states)
- Custom color tinting
- High-DPI sprite variants

## Troubleshooting

### Sprites not loading?

1. Check file names match exactly (case-sensitive on some systems)
2. Verify files are in `assets/sprites/` directory
3. Supported formats: PNG, JPG, JPEG, BMP, GIF
4. Check console output for loading status

### Sprite looks distorted?

- Sprites are auto-scaled; ensure image is high-quality
- Try different image resolutions
- Use PNG with transparency for best results

### Want to revert to shapes?

- Simply delete or rename sprite files in `assets/sprites/`
- Game will automatically fall back to procedural shapes

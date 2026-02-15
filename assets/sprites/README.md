# Game Sprites

Add PNG, JPG, or GIF files to this directory to replace procedural shapes with custom sprite images.

## Naming Convention

Name your sprite files after the shape types used in the game. The filename (without extension) should match the shape name.

### Available Shape Names

#### Player/Spaceship
- `spaceship` - Classic spaceship design
- `fighter` - Sleek fighter jet

#### Bullets
- `bullet_basic` - Standard bullet
- `bullet_laser` - Laser beam
- `bullet_plasma` - Energy plasma orb
- `bullet_missile` - Missile rocket

#### Enemies
- `enemy_basic` - Basic enemy
- `enemy_fast` - Fast moving enemy
- `enemy_tank` - Heavy armored tank
- `enemy_weaver` - Sinuous weaving enemy
- `enemy_boss` - Large boss enemy

#### Additional Shapes
- `hexagon` - Six-sided shape
- `cross` - Plus/cross shape
- `crescent` - Crescent moon shape
- `rectangle`, `triangle`, `circle`, `diamond`, `star` - Basic shapes

## Example

To add a custom spaceship sprite:
1. Create an image file (PNG recommended for transparency)
2. Name it `spaceship.png`
3. Place it in this directory
4. Restart the game

The sprite will automatically be loaded and scaled to the appropriate size.

## Fallback Behavior

If a sprite file is not found, the game will automatically use the procedurally-generated shape instead. This allows you to gradually add sprites without needing all of them at once.

## Image Format Recommendations

- **Format**: PNG (supports transparency)
- **Size**: Roughly 50-100 pixels (will be scaled automatically)
- **Background**: Transparent (PNG with alpha channel)
- **Style**: Match your game's aesthetic

## How It Works

1. Game starts and loads `assets/sprites/` directory
2. For each entity, it checks for a matching sprite file
3. If found, the sprite is loaded and scaled to entity size
4. If not found, the procedural shape is rendered instead

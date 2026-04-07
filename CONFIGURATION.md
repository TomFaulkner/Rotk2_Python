# ROTK2 Battle System Configuration Guide

## Overview

The battle system now supports configurable settings via environment variables and `.env` files. This allows you to customize game behavior without modifying code.

## Configuration File

Create a `.env` file in the project root directory (`/home/tom/dev/Rotk2_Python/.env`):

```bash
# Rice Depletion Mode
# Options: force_retreat (original game) | desertion (alternative)
RICE_DEPLETION_MODE=force_retreat

# Rice consumption rate (troops per rice unit)
RICE_CONSUMPTION_RATE=250

# Desertion percentage when rice runs out (only for desertion mode)
DESERTION_PERCENTAGE=0.15

# Maximum battle duration
MAX_BATTLE_DAYS=30

# Maximum units on battlefield per side
MAX_UNITS_ON_MAP=10

# Debug mode
DEBUG_MODE=false

# Enable battle event logging
LOG_BATTLE_EVENTS=true
```

## Rice Depletion Modes

### `force_retreat` (Default) - Original Game Behavior
When a side runs out of rice:
- **All units are immediately removed from the battlefield**
- The side is considered defeated/retreated
- Battle ends with victory for the opposing side

This matches the original ROTK2 SNES/DOS behavior.

### `desertion` - Alternative Mode
When a side runs out of rice:
- **15% of troops desert each day** (configurable via `DESERTION_PERCENTAGE`)
- Desertion is applied proportionally to all units
- Units with 0 soldiers are marked as defeated
- Battle continues until all units desert or victory conditions are met

This creates a more gradual pressure to end battles.

## Usage Examples

### Using Environment Variables

```bash
# Run with force retreat mode (default)
python3 battle_test.py

# Run with desertion mode
RICE_DEPLETION_MODE=desertion python3 battle_test.py

# Run with custom desertion percentage
RICE_DEPLETION_MODE=desertion DESERTION_PERCENTAGE=0.25 python3 battle_test.py
```

### Using .env File

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your preferred settings

3. Run the game normally:
   ```bash
   python3 battle_test.py
   ```

## Available Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `RICE_DEPLETION_MODE` | `force_retreat` | Behavior when rice runs out: `force_retreat` or `desertion` |
| `RICE_CONSUMPTION_RATE` | `250` | Troops per rice unit (250 troops = 1 rice/day) |
| `DESERTION_PERCENTAGE` | `0.15` | Fraction of troops that desert daily when out of rice (0.15 = 15%) |
| `MAX_BATTLE_DAYS` | `30` | Maximum days a battle can last |
| `MAX_UNITS_ON_MAP` | `10` | Maximum units per side on battlefield |
| `DEBUG_MODE` | `false` | Enable debug logging |
| `LOG_BATTLE_EVENTS` | `true` | Log battle events to console |

## Programmatic Access

Access settings in Python code:

```python
from config import get_settings, RiceDepletionMode

settings = get_settings()

# Check current mode
if settings.rice_depletion_mode == RiceDepletionMode.FORCE_RETREAT:
    print("Using original game behavior")
else:
    print(f"Using desertion mode: {settings.desertion_percentage * 100}% daily")

# Access other settings
print(f"Rice consumption: 1 rice per {settings.rice_consumption_rate} troops")
```

## Reloading Settings

If you modify the `.env` file during runtime:

```python
from config import reload_settings

# Reload settings from .env
new_settings = reload_settings()
```

## Default Behavior

If no `.env` file exists and no environment variables are set:
- **Rice depletion mode**: `force_retreat` (matches original ROTK2)
- **Rice consumption**: 250 troops per rice unit
- **All other settings**: Use documented defaults

The system is designed to work out-of-the-box with original game behavior.
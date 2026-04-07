# ROTK2 Python Remake - Project Plan

## Project Overview

A Python/Pygame remake of Romance of the Three Kingdoms II (三國誌II / Sangokushi II), originally a 1989 DOS game by Koei. This project aims to create a playable, cross-platform version with modern graphics and LLM-based AI.

**Current State:** ~40% Complete  
**Target:** Playable game with full battle system and LLM AI  
**Estimated Timeline:** 12 weeks

---

## Current Status

### What's Complete ✅

- Python/Pygame framework (7,197 lines of code)
- Data loading from original game files
- 13 of 20 commands implemented:
  - Command 1: 迁移 (Move officers/provinces)
  - Command 2: 输送 (Send supplies)
  - Command 4: 征兵 (Recruit/train soldiers)
  - Command 5: 人事 (Hire/Find/Assign/Fire officers)
  - Command 8: 侦查 (Intelligence)
  - Commands 9/10/12: Information displays
  - Command 11: 指令 (Orders)
  - Command 13: 外交 (Diplomacy)
  - Command 14: 委托 (Delegate)
  - Command 15: 市场 (Market)
  - Command 16: 领地 (Territory)
  - Command 18: 地图 (Map view)
  - Command 19: 结束 (End turn)
- Text rendering with Chinese character support
- Save/load game system (S0-S6 files)
- CGA graphics rendering engine
- Province/Officer/Ruler data structures

### What's Missing ❌

- **Battle System (Command 3)**: UI only, no actual gameplay
- **AI System**: Not started
- **Commands 6, 7, 17**: 会议 (Council), 评定 (Strategy), 登录 (Register/Save)
- **English Localization**: Currently Chinese only
- **EGA Graphics**: Not implemented (not needed - using modern graphics)

---

## Architecture

```
Rotk2_Python/
├── Src/
│   ├── Main.py                    # Entry point
│   ├── Battle/                    # Battle system module (NEW)
│   │   ├── __init__.py
│   │   ├── BattleEngine.py        # Core battle logic
│   │   ├── HexGrid.py             # 12x13 grid management
│   │   ├── Unit.py                # Officer units in battle
│   │   ├── Movement.py            # Movement cost calculations
│   │   ├── Combat.py              # Attack/damage resolution
│   │   ├── Tactics.py             # Spells/tactics system
│   │   ├── TurnManager.py         # Turn phases
│   │   ├── LLMAI.py               # LLM-based AI interface
│   │   └── Victory.py             # Win/lose conditions
│   ├── Graphics/                  # Modern graphics (NEW)
│   │   ├── __init__.py
│   │   ├── Portraits.py           # Portrait loading/management
│   │   ├── BattleRenderer.py      # Battle screen rendering
│   │   └── MapRenderer.py         # Map improvements
│   └── [existing command files...]
├── data/                          # Extracted game data (NEW)
│   ├── officers.json              # All 255 officers
│   ├── provinces.json             # All 41 provinces
│   ├── rulers.json                # All 16 rulers
│   ├── text_en.json               # English translations
│   └── terrain_data.json          # Hex terrain per province
├── Resources/
│   ├── portraits/                 # Officer portraits (NEW)
│   ├── hex_tiles/                 # Hex terrain images (NEW)
│   └── [original data files...]
└── Config/
    └── settings.json              # Game settings
```

---

## Battle System Specifications

### Unit Limits

| Side | Own Officers | Allied Officers | Total Max |
|------|--------------|-----------------|-----------|
| **Attacker** | 5 | Up to 5 (Joint attack) | **10** |
| **Defender** | 10 | Up to 5 (Reinforcements) | **15** |

**Joint Attack Mechanics:**
- Diplomacy command (Command 13) initiates alliance
- Allied ruler can send up to 5 officers
- Both sides can receive allied support

### Grid System

- **Size:** 12 rows × 13 columns (156 hexes)
- **Data location:** `Hexdata.dat` - 15,108 bytes
- **Map offset formula:** `0x33b9 + 156 × (province_no - 1) + 0x38`
- **Hex size:** 32×32 pixels (staggered row layout)

### Movement Costs

| Terrain | Cost | Passable | Notes |
|---------|------|----------|-------|
| Plains/Land | 1 | ✅ Yes | Standard movement |
| Forest | 2-3 | ✅ Yes | Slower than plains |
| Water | 5 | ✅ Yes | Requires ships |
| Mountains | Impassable | ❌ No | Cannot move through |
| Fortress/Base | Unknown | ✅ Yes | To be determined |

**Critical Rule:** Moving adjacent to an enemy **immediately ends the unit's turn**

### Tactics Available

1. **Fire Attack (火计)** - Wind-dependent, destroys troops
2. **Ambush (埋伏)** - Forest-only, surprise attack
3. **Duel (单挑)** - Officer vs officer combat
4. **Rally (鼓舞)** - Morale boost
5. **Defend (坚守)** - Fortify position
6. **Retreat (撤退)** - Escape battle

### Weather Effects

- **Rain:** Disables fire tactics
- **Wind:** Affects fire spread direction
- **Clear:** Standard conditions

### Combat Mechanics

**Combat Formula (Approximate):**
```
attack_power = (officer.war * unit.soldiers) / 100
defense = terrain_bonus + formation_bonus
damage = (attack_power - defense) * random(0.8, 1.2)
```

**Officer Stats Affecting Combat:**
- **War (战力):** Attack power, duel strength
- **Intelligence (智力):** Tactic success rate, spell effectiveness
- **Charisma (号召):** Troop morale, rally effectiveness
- **Soldiers:** Unit size (HP equivalent)
- **Training:** Combat effectiveness, formation bonuses

**Victory Conditions:**
- Destroy all enemy units
- Defeat enemy commander
- Capture enemy castle/fortress
- Force enemy retreat

---

## Data Files Structure

### Officer Data

**Source:** Kaodata.dat + Game Buffer (Data.BUF)

```
Each officer: 43 bytes (0x2B)
Total: 255 officers
Portrait data: 210,240 bytes in Kaodata.dat (~438 portraits)

Key offsets:
- 0x04: Intelligence (智力)
- 0x05: War/Combat (战力)
- 0x06: Charisma (号召)
- 0x0A: Ruler number
- 0x0B: Loyalty
- 0x12-0x13: Soldiers (word)
- 0x14-0x15: Weapons (word)
- 0x16: Training level
- 0x19: Birth year
- 0x1A-0x1B: Portrait ID
- 0x1C+: Name data
```

### Province Data

**Source:** Data.BUF

```
Total: 41 provinces
Each province: 35 bytes (0x23)
Start: 0x2D8C + DATA_OFFSET

Key offsets:
- 0x00-0x01: Next province offset
- 0x02-0x03: Governor offset
- 0x08-0x09: Gold
- 0x0A-0x0D: Food
- 0x0E-0x0F: Population
- 0x10: Ruler number (0xFF = empty)
- 0x11: War ruler number (0xFF = no war)
- 0x14: War province number
- 0x16: Land value
- 0x17: Popularity
- 0x18: Flood control
```

### Text Data

**Source:** DSBUF.DAT (65,535 bytes)

```
Chinese text stored as: $index$ format
ASCII text: Direct characters
Game strings accessed by offset (e.g., 0x609d = command names)
```

---

## LLM-Based AI Architecture

### System Design

```python
class LLMBattleAI:
    def get_decision(game_state):
        # Convert game state to text description
        prompt = self.create_prompt(game_state)
        
        # Call LLM API (OpenAI)
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or gpt-3.5-turbo
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse response to game action
        action = self.parse_response(response.choices[0].message.content)
        return action
```

### Prompt Template

```markdown
You are [RULER_NAME], a warlord in ancient China.

BATTLE SITUATION:
- Your forces: [X] officers, [Y] total soldiers
- Enemy forces: [A] officers, [B] total soldiers
- Weather: [WEATHER], Wind: [DIRECTION]
- Terrain: [DESCRIPTION]

YOUR UNITS:
1. [GENERAL_NAME] - [SOLDIERS] soldiers at position ([X],[Y])
   Stats: War [WAR], Int [INT], Chm [CHM]
   Can move [N] hexes, adjacent to enemy: [YES/NO]

ENEMY UNITS:
[Similar description]

VALID ACTIONS:
- Move [UNIT_ID] to ([X],[Y])
- Attack with [UNIT_ID] targeting [ENEMY_ID]
- Use tactic [TACTIC_NAME] with [UNIT_ID] at ([X],[Y])
- Duel [UNIT_ID] vs [ENEMY_GENERAL]
- Rally with [UNIT_ID]
- Defend with [UNIT_ID]
- Retreat [UNIT_ID]

What is your command?
```

### API Strategy

- **Provider:** OpenAI (GPT-4/GPT-3.5)
- **Flexibility:** Can switch LLMs per ruler or per battle
- **Fallback:** Implement simple heuristic AI for offline/testing
- **Optimization:** Cache similar game states to reduce API calls

---

## Development Phases

### Phase 1: Foundation (Week 1-2)

- [ ] Create data extraction scripts
- [ ] Export officer data to JSON
- [ ] Export province data to JSON
- [ ] Create English text system
- [ ] Verify original graphics can be loaded
- [ ] Set up project structure

**Deliverable:** Clean data files and English text rendering

### Phase 2: Battle Core (Week 3-5)

- [ ] Implement HexGrid class (12×13)
- [ ] Create Unit class for battle officers
- [ ] Implement movement system with terrain costs
- [ ] Add adjacency combat rule
- [ ] Unit placement system (10 vs 15 max)
- [ ] Turn management (player/AI phases)

**Deliverable:** Units can move on grid with proper rules

### Phase 3: Combat (Week 6-7)

- [ ] Implement attack mechanics
- [ ] Create damage calculation formulas
- [ ] Add morale system
- [ ] Implement victory conditions
- [ ] Basic battle UI

**Deliverable:** Functional combat with win/lose states

### Phase 4: Tactics (Week 8-9)

- [ ] Fire Attack tactic (weather dependent)
- [ ] Ambush tactic (forest only)
- [ ] Duel system
- [ ] Rally tactic
- [ ] Defend tactic
- [ ] Retreat option
- [ ] Weather/wind effects

**Deliverable:** All 6 tactics working

### Phase 5: LLM AI (Week 10-11)

- [ ] OpenAI API integration
- [ ] Prompt engineering
- [ ] Response parsing
- [ ] State caching
- [ ] Fallback simple AI
- [ ] Testing different LLM models

**Deliverable:** AI opponents using LLM decision-making

### Phase 6: Polish (Week 12)

- [ ] Game balance adjustments
- [ ] Bug fixes
- [ ] Graphics improvements (if time)
- [ ] Sound effects (optional)
- [ ] Final testing

**Deliverable:** Playable, balanced game

---

## Graphics Strategy

### Phase 1: Original Graphics
- Use original graphics from `kaodata.dat`
- Test with original CGA/hex tiles
- Focus on gameplay functionality

### Phase 2: Modern Upgrade (Post-Playable)
- Generate AI portraits for all 255 officers
- Create better hex terrain tiles
- Improve UI styling
- Add animations

---

## Key Implementation Details

### Hex Grid Coordinate System

- Origin at top-left (0,0)
- Rows: 0-11, Columns: 0-12
- Staggered layout: Even columns normal, odd columns offset by 16px
- Rendering: `y_offset = (col % 2) * 16`

### Movement Validation

```python
def can_move_to(unit, target_hex):
    cost = terrain_cost[target_hex.terrain]
    if unit.movement_points < cost:
        return False
    if will_be_adjacent_to_enemy(target_hex):
        unit.end_turn_after_move = True
    return True
```

### Portrait Loading

- Portrait ID from officer data: `(buffer[0x1B] << 8) + buffer[0x1A] - 1`
- Kaodata.dat contains ~438 portraits
- Each portrait in CGA format (~480 bytes)
- Can be loaded via existing DrawCGA class

---

## Open Questions

- [ ] Exact forest movement cost (2 or 3?)
- [ ] Fortress/base movement cost
- [ ] Specific combat damage formulas (can approximate)
- [ ] Portrait extraction details from kaodata.dat

---

## Notes

- **CGA/EGA emulation:** Not required - using modern graphics
- **Chinese text:** Being replaced with English
- **SNES assets:** Optional - can use original graphics first
- **AI:** LLM-based via OpenAI API, with fallback simple AI
- **Target:** Playable game in 12 weeks, polish afterward

---

## File Locations

- Original data: `/home/tom/dev/Rotk2_Python/Resources/`
- Source code: `/home/tom/dev/Rotk2_Python/Src/`
- Extracted data: `/home/tom/dev/Rotk2_Python/data/` (to be created)
- Documentation: `/home/tom/dev/Rotk2_Python/PLANS.md`

---

## Completion Log

### April 1, 2026 - Phase 0 Complete ✅

**Completed Tasks:**
1. ✅ Created comprehensive project documentation (PLANS.md)
2. ✅ Analyzed current codebase state
3. ✅ Documented battle system specifications with corrections
4. ✅ Designed LLM-based AI architecture
5. ✅ Created data extraction script
6. ✅ Extracted all game data to JSON:
   - 255 officers (213KB)
   - 41 provinces (37KB)
   - 16 rulers (8.5KB)
   - Terrain data for all provinces (449KB)
   - English text template
7. ✅ Created symlinks for case-sensitive file access
8. ✅ Verified data extraction works

**Files Created:**
- `/PLANS.md` - Complete project documentation
- `/scripts/extract_game_data.py` - Data extraction script
- `/data/officers.json` - All officer data
- `/data/provinces.json` - All province data
- `/data/rulers.json` - All ruler data
- `/data/terrain_data.json` - Hex terrain maps
- `/data/text_en.json` - English text template
- `/data/extraction_summary.json` - Extraction metadata

**Next:** Phase 1 - Battle System Implementation

### April 1, 2026 - Portrait System Complete ✅

**Completed Tasks:**
1. ✅ Organized 387 SNES portraits into `/Resources/portraits/`
   - 208 unique officer portraits
   - 144 generic portraits (fallback)
   - Daughters and custom character portraits
2. ✅ Created `PortraitLoader` class with:
   - CSV mapping loader (officer ID → portrait ID)
   - Portrait caching system
   - Generic portrait fallback
   - Preloading support
   - JSON mapping export
3. ✅ Tested portrait loading - all major officers load correctly
4. ✅ Generated `portrait_mapping.json` for reference

**Files Created:**
- `/Src/PortraitLoader.py` - Portrait management class
- `/Resources/portraits/unique/` - 208 unique portraits
- `/Resources/portraits/generic/` - 144 generic portraits
- `/Resources/portraits/daughters/` - Special character portraits
- `/Resources/portraits/custom/` - Custom ruler portraits
- `/Resources/portraits/portrait_mapping.json` - ID mapping

**Portrait Usage:**
```python
from PortraitLoader import PortraitLoader

loader = PortraitLoader()
portrait = loader.get_portrait(officer_id=0)  # Cao Cao
name = loader.get_officer_name(0)  # "Cao Cao"
```

**Next:** Phase 1 - Battle System Implementation

---

*Last Updated: April 2026*

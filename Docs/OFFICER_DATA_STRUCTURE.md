# ROTK2 Officer Data Structure Documentation

## Overview
Each officer in ROTK2 is stored in a 43-byte (0x2B) record in the game data.

## Memory Layout (43 bytes per officer)

### Offsets 0x00-0x01: Next Officer Pointer
- **Description:** Linked list pointer to next officer in same city
- **Calculation:** `value - 0x38` = offset of next officer
- **Usage:** Used for iterating officers within a province

### Offset 0x02: Status Flags (High/Low Nibble)
- **High 4 bits:** Death status
  - Bit 7: Dead flag
- **Low 4 bits:** Movement status  
  - Bit 0: Can move this turn
- **Usage:** Track officer availability for commands

### Offset 0x03: Spy/Sickness Flags
- **High 4 bits:** Spy status
  - Value > 0: Officer is a spy (value = enemy ruler number)
- **Low 4 bits:** Sickness status
  - Bit 0: Is sick
- **Usage:** Spy infiltration and disease mechanics

### Offset 0x04: Intelligence (Int)
- **Range:** 0-100
- **Usage:** 
  - Fire attack success rate
  - Strategic advice quality
  - Diplomatic negotiation success

### Offset 0x05: War Ability (War)
- **Range:** 0-100
- **Usage:**
  - Personal combat damage
  - Battle unit attack power
  - Training effectiveness

### Offset 0x06: Charisma (Chm)
- **Range:** 0-100
- **Usage:**
  - Recruitment success
  - Officer loyalty maintenance
  - Population growth (if governor)

### Offset 0x07: Honor (yili - 義理)
- **Range:** 0-100
- **Usage:**
  - Bribe resistance (higher = harder to bribe)
  - Loyalty stability
  - Personal combat honor

### Offset 0x08: Benevolence (rende - 仁德)
- **Range:** 0-100
- **Usage:**
  - Officer satisfaction
  - Province stability
  - Post-bribe loyalty calculation

### Offset 0x09: Ambition (yewang - 野望) ⭐ KEY STAT
- **Range:** 0-100
- **Usage:**
  - **High (85+):** Auto-accepts personal combat challenges
  - **Bribe susceptibility:** Higher ambition = easier to turn
  - **Tiger-Wolf susceptibility:** Higher = more likely to rebel when tricked
  - Governor rebellion likelihood
- **Implementation Note:** Used in our battle system for auto-duel acceptance

### Offset 0x0A: Ruler Number
- **Description:** Index of ruler this officer serves
- **Calculation:** `0x20 + ruler_no * 0x2B` = ruler's data address
- **Special Value:** 0xFF = Unemployed/free officer

### Offset 0x0B: Loyalty
- **Range:** 0-100
- **Usage:**
  - **90-100:** Very unlikely to betray
  - **80-89:** Possible but rare betrayal
  - **<80:** Increasing risk of defection
  - **<80:** Easy recruitment target
  - Post-bribe loyalty calculation

### Offset 0x0C: Bodyguards (shiwei - 侍衛)
- **Range:** 0-?
- **Usage:** Elite troops assigned to officer

### Offset 0x0D: Spy Assignment (Ambush Faction)
- **Description:** Enemy ruler number officer is spying on
- **Usage:** Spy operations and infiltration

### Offset 0x0E: Spy Location (Ambush City)
- **Description:** City where spy is planted
- **Usage:** Spy network tracking

### Offset 0x0F: Compatibility ⭐ KEY STAT
- **Range:** 0-15 (represents faction alignment)
- **Groups:**
  - 0-4: Shu (Liu Bei) faction tendency
  - 5-9: Wu (Sun Jian) faction tendency  
  - 10-14: Wei (Cao Cao) faction tendency
  - 15: Other
- **Usage:**
  - Bribe success calculation
  - Post-bribe loyalty
  - Starting loyalty when hired
  - Example: Diao Chan changed from 0x0F to 0x08 after event
- **Formula:** `diff = abs(officer1.Compatibility - officer2.Compatibility)`

### Offsets 0x10-0x11: Bloodline
- **Description:** Family relationships
- **Usage:**
  - Blood ties override loyalty mechanics
  - Family members won't betray each other
  - Example: Cao Ang extremely loyal to Cao Cao

### Offsets 0x12-0x13: Soldiers
- **Description:** Number of soldiers under command
- **Range:** 0-30000

### Offsets 0x14-0x15: Weapons
- **Description:** Equipment level
- **Range:** 0-10000 (represents equipment quality)

### Offset 0x16: Training Level
- **Range:** 0-100
- **Usage:** Battle mobility and effectiveness

### Offsets 0x17-0x18: Equipment/Item Flags
- **Description:** Special items equipped
- **Notes:** Changes when items given:
  - Green Dragon Blade: 0x17 changes from 0 to 6
  - Red Hare Horse: 0x18 changes from 0xFF to 0
  - Books: Complex changes to both bytes

### Offset 0x19: Birth Year
- **Description:** Year officer was born
- **Usage:** Age calculation

### Offsets 0x1A-0x1B: Portrait ID
- **Description:** Index into portrait graphics
- **Calculation:** `(value - 1)` = portrait offset
- **Special:** Values >= 219 = composite/custom portraits

### Offsets 0x1C-0x29: Name Data
- **7 pairs of bytes:** Character indices for officer name
- **Encoding:** Chinese character codes or ASCII for English
- **Format:** Each pair represents one character

### Offset 0x2A: Unknown
- **Description:** Unknown usage

---

## Special Officers

### Lu Bu & Wei Yan - Special Cases
- **Status:** "Rebellious by nature"
- **Can be bribed at ANY loyalty level** (including 100)
- Much higher betrayal chance than normal officers
- Still worth monitoring even with 90+ loyalty

### Family Ties
- Bloodline data overrides loyalty mechanics
- Family members extremely unlikely to betray each other
- Example: Cao Ang → Cao Cao (extremely loyal)

---

## Unknown/Uncovered Data

### Tiger-Wolf (虎狼之計) Susceptibility
- **Status:** ❌ NOT FOUND in officer data structure
- **Likely Implementation:** Derived from existing stats:
  - High Ambition (yewang) + Low Honor (yili) = High susceptibility
  - Governor status + Low Loyalty = Rebellion risk
  - No explicit "Tiger-Wolf chance" byte found

### Explicit Personality Types
- **Status:** ❌ NOT FOUND (Tiger/Wolf/Ox/etc.)
- **Note:** ROTK3+ has explicit personality types
- **ROTK2:** Personality derived from stat combinations

### Rebellion/Defection Base Chance
- **Status:** ❌ NOT FOUND as explicit value
- **Likely Derived From:**
  - Ambition level
  - Loyalty level
  - Honor level
  - Compatibility with ruler

---

## Derived Statistics (Not Stored, Calculated)

### Personal Combat Ambition Check
```python
# Auto-accept duel if ambition >= 85
if officer.ambition >= 85:
    auto_accept_challenge = True
```

### Bribe Success Calculation
```python
base_success = 2 * (100 - officer.yili) - officer.Chm + officer.yewang
compatibility_factor = abs(officer.Compatibility - bribing_ruler.Compatibility)
loyalty_factor = 100 - officer.Loyalty
```

### Post-Bribe Loyalty
```python
new_loyalty = abs(100 - sqrt((officer.Loyalty / 2) * compatibility_diff)) - random(0-5)
```

### Tiger-Wolf (虎狼之計) Susceptibility ⭐ KEY DERIVED STAT
**Formula:** `tiger_wolf_susceptibility = ambition - honor`

**Range:** Roughly -100 to +100
- **High positive (>30):** Very susceptible to rebellion trick (e.g., Li Jue)
- **Negative:** Honor-bound, unlikely to betray
- **Examples:**
  - Ambition 80, Honor 20 = Susceptibility 60 (very easy to flip)
  - Ambition 30, Honor 90 = Susceptibility -60 (very loyal)

**Can Be Tiger-Wolfed Calculation:**
```python
def can_be_tiger_wolfed(officer, current_loyalty, bribe_amount):
    susceptibility = officer.ambition - officer.honor  # yewang - yili
    base_chance = (100 - current_loyalty) + (susceptibility * 1.5) + (bribe_amount // 800)
    return random.random() < (base_chance / 100.0)
```

**Factors:**
- Low loyalty = easier to turn
- High ambition + Low honor = very susceptible
- Bribe amount increases success chance
- Officers like Li Jue have high ambition, low honor = easy targets

### Governor Rebellion Risk
```python
# High risk factors:
- Is Governor: True
- Tiger-Wolf Susceptibility > 30: High risk
- Loyalty < 80: High
- Compatibility diff with ruler > 5: High

# Formula estimate:
rebellion_risk = (tiger_wolf_susceptibility * 0.5) + ((100 - loyalty) * 0.3) + (compatibility_diff * 2)
```

---

## Implementation Notes for Remake

### What We Have ✅
- All stat offsets documented
- Ambition (yewang) implemented for auto-duel
- Compatibility system for bribes
- Loyalty mechanics
- Bloodline/family system

### What We DON'T Have ❌
- Explicit Tiger-Wolf susceptibility stat
- Explicit rebellion probability stat
- Personality type classification (Tiger/Wolf/Ox)
- Pre-calculated defection chances

### Recommendation
Derive Tiger-Wolf susceptibility from:
1. **Ambition (40% weight)** - Higher = more likely to seek power
2. **Loyalty (30% weight)** - Lower = easier to turn
3. **Honor (20% weight)** - Lower = less principled
4. **Compatibility (10% weight)** - Lower = unhappy with ruler

This matches ROTK2's emergent gameplay where officer behavior stems from interacting stats rather than explicit personality types.

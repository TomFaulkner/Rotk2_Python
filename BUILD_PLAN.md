# Battle System Build Plan

## Overview
Implementation of ROTK2 battle system based on Amiga manual and admtanaka's GameFAQs guide.

**Status:** Ready to implement  
**Estimated Time:** 3-4 weeks  
**Priority:** High

---

## Phase 1: Foundation (Week 1)

### Day 1-2: Project Structure
Create Src/Battle/ directory with:
- HexGrid.py - 12x13 hex grid management
- BattleUnit.py - Unit class (officer + soldiers)
- Terrain.py - Terrain types and costs
- BattleEngine.py - Core battle logic
- TurnManager.py - Turn phases and flow
- BattleRenderer.py - Render battle screen

### Day 3-4: HexGrid Implementation
- Create 12x13 grid data structure
- Load terrain from terrain_data.json
- Hex coordinate system (staggered rows)
- Adjacency detection (6 directions)
- Render hex grid with terrain

**Grid Details:**
- 12 rows x 13 columns = 156 hexes
- Terrain: Plains(2), Forest(3), Hills(3), Castle(3), Water(5)
- Coordinate: (row, col) with offset for odd columns

### Day 5-7: BattleUnit Class
- Unit composition (officer + soldiers)
- Unit stats: mobility, position, training, arms, loyalty
- Unit placement on grid
- Reserve system for excess units
- Portrait display

---

## Phase 2: Movement System (Week 1-2)

### Day 8-9: Mobility System
- Calculate base mobility from training (max 6 at 100 training)
- Terrain cost application
- Movement range calculation
- Formula: distance = mobility // terrain_cost

### Day 10-11: Movement Rules
- Move unit to adjacent hex
- CRITICAL RULE: Moving adjacent to enemy ends turn
- Flag unit as "engaged"
- Terrain passability check
- Prevent unit stacking

### Day 12-14: Battle Setup
- Use existing Command3.py pre-battle screen
- Select attacking generals (max 10)
- Select defending generals (max 10)
- Appoint commander-in-chief
- Allocate supplies (gold, rice)
- Place units on battlefield
- Reserve system for excess units

---

## Phase 3: Combat System (Week 2-3)

### Day 15-17: Attack Types

**Simultaneous Attack (Primary):**
- Check adjacent friendly units
- Combined attack power
- Low casualties for attackers
- Best attack type

**Normal Attack:**
- Single unit vs single unit
- Moderate casualties both sides
- Use when no allies adjacent

**Charge Attack:**
- Heavy casualties both sides
- Fight until one unit destroyed
- Risk: Leader may die
- Good for capturing weak units

**Fire Attack:**
- Set hex on fire (not unit)
- Check intelligence for success
- Fire spreads to adjacent hexes
- Leader dies if less than 1 soldier and trapped

### Day 18-19: Personal Combat (Duel)
- Day 1 challenge system
- Accept/Refuse mechanics
- Refuse penalty: ~8% desertion
- Duel resolution
- Capture/kill loser
- War ability gain if lower defeats higher

### Day 20-21: Victory Conditions
- Check for commander capture or death
- Check for castle occupation
- Check for supply depletion
- Battle end resolution
- Post-battle options: recruit, release, behead

---

## Phase 4: Tactics and Systems (Week 3)

### Day 22-23: Bribe System
- Select target enemy unit
- Offer gold (0-99)
- Success factors:
  * Target loyalty
  * Compatibility with both rulers
  * Lu Bu and Wei Yan: always bribable
  * Familial relationships reduce chance
- Switch sides if successful

### Day 24-25: Fire Mechanics
- Fire spreads each turn
- Wind direction affects spread
- Damage to units in fire
- Cannot enter burning hexes
- Fire extinguishes over time

### Day 26-27: Reserve and Reinforcements
- Track reserve units
- Call reinforcements when active units less than 10
- Deploy reserve to battlefield
- Replace lost units

### Day 28: View System
- Show enemy unit info (costs 10 gold)
- Display loyalty, skill, arms, war, intel
- Cheap and useful

---

## Phase 5: AI Integration (Week 4)

### Day 29-30: LLM AI Setup
- OpenAI API integration
- Prompt template for battle decisions
- Convert game state to text
- Parse LLM response to actions
- Cache responses

### Day 31-32: Simple Fallback AI
- Heuristic-based AI for offline play
- Basic decision making
- Priority: Survive, then attack
- Use when API unavailable

### Day 33-34: Battle Integration
- Connect to main game loop
- Trigger battle from Command3.py
- Return battle results
- Update province ownership

### Day 35: Testing and Polish
- Test all attack types
- Balance damage formulas
- Fix bugs
- Optimize performance

---

## Key Implementation Details

### Mobility Formula
Base mobility = 6 if training >= 100, else training / 16.67
Movement range = mobility // terrain_cost

### Combat Damage (Approximate)
Base attack = (war * soldiers) / 100
Simultaneous: defender takes 1.2x, attacker takes 0.3x
Normal: defender takes 1.0x, attacker takes 0.6x
Charge: defender takes 1.5x, attacker takes 1.2x

### Bribe Success Factors
Base chance: 5%
Loyalty >90: 1% (very hard)
Loyalty <50: 30% (easier)
Lu Bu/Wei Yan: +20%
High compatibility with you: +15%
Low compatibility with enemy: +10%
Family relationship: 90% reduction
Gold: up to +49.5% (at 99 gold)

### Duel War Gain
If lower war defeats higher war:
New war = (winner.war + loser.war) // 2

---

## Files to Create/Modify

### New Files in Src/Battle/:
- __init__.py
- HexGrid.py
- BattleUnit.py
- Terrain.py
- BattleEngine.py
- TurnManager.py
- BattleRenderer.py
- Combat.py (damage calculations)
- Tactics.py (fire, bribe, etc.)
- LLMAI.py
- SimpleAI.py

### Files to Modify:
- Src/Command3.py - Connect to battle system
- Src/Main.py - Battle trigger integration

---

## Success Criteria

- [ ] Units can move on hex grid
- [ ] Movement ends when adjacent to enemy
- [ ] All 4 attack types work
- [ ] Fire spreads correctly
- [ ] Bribery works with loyalty/compatibility
- [ ] Duels resolve correctly
- [ ] Victory conditions detected
- [ ] LLM AI makes decisions
- [ ] Simple AI works offline
- [ ] Battles resolve and update game state

---

## Notes

- Focus on SNES/PC terrain types (simpler than Amiga)
- Lu Bu and Wei Yan: high betrayal risk, not guaranteed
- Family relationships matter
- Compatibility (Shu/Wei/Wu) affects bribery
- Keep it playable first, polish later

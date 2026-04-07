# ROTK2 Battle System - Complete Mechanics Guide

**Source:** GameFAQs Strategy Guide v1.22 (2006) by admtanaka / Greg Hartman  
**Extracted:** April 2026

---

## Table of Contents

1. [Battle Overview](#battle-overview)
2. [Victory Conditions](#victory-conditions)
3. [Battle Commands](#battle-commands)
4. [Movement System](#movement-system)
5. [Terrain Costs](#terrain-costs)
6. [Attack Types](#attack-types)
7. [Fire Mechanics](#fire-mechanics)
8. [Personal Combat (Duel)](#personal-combat-duel)
9. [Unit Stats in Battle](#unit-stats-in-battle)
10. [Bribing Enemy Units](#bribing-enemy-units)
11. [Capturing Officers](#capturing-officers)
12. [Battle Progression](#battle-progression)
13. [Key Formulas](#key-formulas)

---

## Battle Overview

### When Battles Occur
- You attack another state
- You are attacked by another state  
- As a wanderer, attempt to establish yourself in an owned state

### Initial Setup
1. Select generals to fight
2. Appoint commander-in-chief
3. Allocate money and rice supplies
4. Place units on battlefield (max 10 on map, rest in reserve)
5. Attacker places supply units

**Note:** A general + his troops = one unit

### Battle Duration
- Battles last **30 days** (one month)
- Either side can send reinforcements after 30 days
- War continues month-to-month until resolved

---

## Victory Conditions

### Attacker Wins:
1. Eliminate enemy commander
2. Move a unit onto the defending castle
3. Defenders run out of rice

### Defender Wins:
1. Attackers run out of rice
2. Capture/eliminate enemy commander

### Post-Battle Options
- **Recruit** captured officers (they join your army)
- **Release** captured officers (they become free generals)
- **Behead** captured officers (permanently kill them)

**Note:** You can NEVER recruit an enemy ruler - only behead or release.

---

## Battle Commands

### 1. MOVE

**1a. Normal Move**
- Move unit in desired direction
- **CRITICAL:** You stop moving if you move adjacent to an enemy unit
- Mobility remaining is lost when adjacent to enemy
- Max mobility: 6 (at 100 training/skill)

**1b. Move Enemy**
- Attempt to move an enemy to the square you vacate
- Enemy must be adjacent
- Most useful if your square is on fire
- Higher intel = better success
- Works best against low-intel enemies

### 2. ATTACK

**2a. Simultaneous Attack (Simult.)**
- Every unit adjacent to target joins the attack
- Casualties generally **very low** on attacking side
- Most efficient way to eliminate strong opponents
- Best attack type overall

**2b. Normal Attack**
- Engage enemy with your unit only
- One normal attack > single attack from simult.
- Attacker casualties noticeably higher
- Use when no allies are nearby

**2c. Fire Attack**
- Attempt to set ground or adjacent unit on fire
- Units trapped in fire take heavy random casualties
- Unit with ~20 soldiers will usually retreat
- Unit with <1 soldier that cannot escape = **leader dies in flames**
- Castle is very hard to set on fire
- Higher leader intel = better success chance
- War ability may also play a role

**2d. Charge**
- Both units take **heavy casualties**
- If overpowering, definitely worth it
- Usually breaks through to other side of enemy
- If you don't break through, expect heavy losses
- Good for eliminating weak units and capturing leaders
- Sometimes leader dies when unit eliminated by charge

### 3. FLEE (Retreat)
- Withdraw unit from battlefield
- If commanding unit flees, entire army must withdraw
- Cannot change commander mid-battle
- Exception: Ruler arrives as reinforcement after 1+ months = becomes new commander
- Useful for extending conflict against powerful provinces
- Units fleeing have chance of being captured (higher if near many enemies)

### 4. VIEW
- Costs **10 gold**
- Shows enemy unit info: loyalty, skill, arms level, war ability, intel
- Always bring money to battle for this

### 5. TACTICS

**5a. Bribe**
- Attempt to bribe enemy unit to join you
- Max 99 gold per attempt (use max - success rate still low)
- Officer keeps money if you fail
- Best targets: Low loyalty or naturally disloyal officers
- **0 gold bribe works** if you have a pact with them
- Compatibility affects success and post-bribe loyalty
- Attempting to bribe loyalty >90 almost always wastes time
- **Lu Bu and Wei Yan can be bribed even at loyalty 100**

**5b. Reinforce**
- Only available when defending
- Bring out units left inside castle
- Generally don't need to leave units inside unless you have 10+ to deploy

---

## Movement System

### Base Mobility
- Most units start with ~6 mobility points
- **Maximum mobility: 6** (requires 100 training/skill)
- Mobility depends on training level of troops

### Mobility Modifiers
- **Standby (rest turn):** +1 mobility next turn
- Not using any command = resting

### Movement Stops When:
- You move **adjacent to an enemy unit**
- You get ambushed
- Remaining mobility is lost

**Strategic Note:** This adjacency rule is critical! Positioning to block enemy movement is a key tactic.

---

## Terrain Costs

### SNES/PC Version (from admtanaka guide)
| Terrain | Mobility Cost |
|---------|---------------|
| **Fields (Plains)** | 2 |
| **Forests** | 3 |
| **Hills** | 3 |
| **Castle** | 3 |
| **Water** | 5 |

### Amiga Version (from manual)
| Terrain | Mobility Cost |
|---------|---------------|
| **Plains** | 2 |
| **Mountains** | 4 |
| **Swamp** | 5 |
| **Water (Naval)** | 6 |
| **Water (Non-Naval)** | 10 |
| **Castle** | 3 |
| **Highly Mountainous** | Impassable |

**Note:** The Amiga version had more terrain types. SNES/PC versions simplified to fewer terrain types.

### Movement Calculation Example
- 6 mobility in plains (cost 2) = 3 hexes
- 6 mobility in forest (cost 3) = 2 hexes

---

## Attack Types Comparison

| Attack Type | Casualties (You) | Casualties (Enemy) | Best Use |
|-------------|------------------|-------------------|----------|
| **Simultaneous** | Very Low | Moderate-High | Primary attack method |
| **Normal** | Moderate | Moderate | When alone |
| **Charge** | High | Very High | Overpowering weak units |
| **Fire** | None | Heavy (random) | Trap enemies, burn castles |

### Simultaneous Attack Details
- Most efficient attack type
- Casualties very low on attacking side UNLESS target is especially powerful
- Requires multiple units adjacent to target
- Always use when possible

### Normal Attack Details
- Single unit vs single unit
- Higher casualties than simult. for attacker
- More damage per attack than simult. individual attacks
- Use only when no allies adjacent

### Charge Details
- Heavy casualties on BOTH sides
- Usually breaks through enemy unit
- If you don't break through = big trouble
- Good for: Capturing weak unit leaders
- Risk: Leader may die when unit eliminated

### Fire Attack Details
- Sets hex on fire (not unit directly)
- Spreads to adjacent hexes
- Trapped units take heavy random casualties
- Units with ~20 soldiers usually retreat automatically
- **Leader dies if:** <1 soldier AND cannot escape
- Castle very resistant to fire
- Success based on leader intel
- Cannot enter burning hex

---

## Fire Mechanics

### How Fire Works
1. Select Fire attack on adjacent hex
2. If successful, hex catches fire
3. Fire spreads to adjacent hexes over time
4. Units in/on adjacent burning hexes take damage

### Fire Damage
- Heavy random casualties
- Affects both sides (friend and foe)
- Can completely destroy enemy generals

### Strategic Use
- Force enemy to move from advantageous position
- Trap units with no escape route
- Destroy enemy supplies
- Deny terrain to enemy

### Wind Effects
- Fire spreads downwind
- Check wind direction before using
- Can backfire if wind blows toward your units

---

## Personal Combat (Duel)

### When It Happens
- **Day 1 of battle:** Both sides can propose personal combat
- Sometimes powerful officers volunteer automatically
- Enemy can accept or refuse challenge

### Consequences of Refusing
- **~8%** of soldiers desert (small morale penalty)
- Applies to both sides

### Duel Outcome
- Fight until one falls or draw
- **Loser (and his entire unit) = captured and removed from battle**

### War Ability Gain
- If lower war defeats higher war:
- Winner's war ability raises to **average of both numbers (rounded down)**
- Risky but can raise general's ability

**Example:** Jin Xuan (war 43) defeats Yang Huai (war 77)  
Jin Xuan's new war = (43+77)/2 = 60

---

## Unit Stats in Battle

### Important Stats

**War Ability (Power)**
- Affects combat effectiveness
- Determines training efficiency
- Used in personal combat

**Intelligence**
- Fire attack success
- Move Enemy success
- Spy tactics success
- Advisor quality

**Training/Skill**
- Max 100
- Determines mobility (max 6 at 100)
- Higher = more movement
- Never attack without 100 skill

**Arms Level**
- Percentage of soldiers with weapons
- Affects combat effectiveness
- Keep at 100%
- Computer slow to buy arms - exploit this!

**Loyalty**
- High loyalty (>90) = unlikely to be bribed
- Low loyalty (<80) = easy recruitment target
- Lu Bu and Wei Yan = always bribable even at 100

**Soldiers**
- Max 100 (displayed as 10,000 actual)
- Higher = stronger unit
- Assign to highest war ability officers

### Unit Composition
- 1 General + Assigned Soldiers = 1 Unit
- Max 10 units on battlefield per side
- Excess in reserve

---

## Bribing Enemy Units

### Mechanics
- Cost: Up to 99 gold per attempt
- Success rate: Low even at max gold
- Failed bribe: Officer keeps the money

### Best Targets
1. **Low loyalty officers** (<80 ideal)
2. **Lu Bu** - Bribable at ANY loyalty
3. **Wei Yan** - Bribable at ANY loyalty
4. **Poor compatibility** with their ruler
5. **High compatibility** with you

### Special Cases
- **Pact units:** Can bribe with 0 gold (they switch automatically)
- **Loyalty >90:** Almost always waste of time (except Lu Bu/Wei Yan)
- **Post-bribe loyalty:** Based on compatibility

### Preparation
- Bring several thousand gold if planning multiple bribes
- Use max 99 gold per attempt
- Focus on high-value targets

---

## Capturing Officers

### When Captured
- Unit eliminated in battle
- General captured in personal combat
- Fleeing unit caught by enemy

### Capture Options

**Recruit**
- Officer joins your army
- Post-capture loyalty based on compatibility
- Captured on offense = usable in current war
- Captured on defense = cannot use in reserve

**Release**
- Officer becomes free general
- No benefit to you
- Computer may recruit them later

**Behead**
- Permanently kill officer
- Removes from game entirely

### Ruler Capture Special Rules
- Can NEVER recruit a ruler
- Options: Release (if they have somewhere to flee) or Behead
- If no province to flee to = must behead

---

## Battle Progression

### Turn Structure
1. **Day 1:** Optional personal combat challenge
2. **Days 1-30:** Tactical movement and combat
3. **Day 30:** Battle ends or continues with reinforcements

### Reinforcements
- Available after 30 days
- Both sides can bring fresh units
- Can change strategy mid-battle
- Attacker can send ruler as reinforcement (becomes commander)

### Winning the Battle
Attacker wins if:
- Enemy commander captured/killed
- Unit enters enemy castle
- Defenders run out of rice

Defender wins if:
- Attackers run out of rice
- Attacker commander captured/killed

### Post-Battle
- Distribute war spoils (if attacking)
- Decide fate of captured officers
- Province 10 always gives war spoil item
- Items raise officer abilities and max loyalty

---

## Key Formulas

### Mobility
```
Base Mobility = 6 (with 100 training)
Actual Mobility = Base - Terrain Cost penalties
Movement Range = Mobility / Terrain Cost
```

Example:
- 6 mobility, plains (2) = 3 hexes
- 6 mobility, forest (3) = 2 hexes

### Training Required for Max Mobility
```
Max Mobility (6) requires 100 training/skill
Training increases through Train command
Higher war ability = faster training
```

### Personal Combat War Gain
```
If Winner.War < Loser.War:
    New.War = (Winner.War + Loser.War) / 2 [rounded down]
```

Example: 43 vs 77 → New war = 60

### Fire Damage
```
Random heavy damage (no exact formula given)
Unit with ~20 soldiers usually retreats
Unit with <1 soldier + no escape = leader dies
```

### Desertion from Refusing Duel
```
~8% of soldiers desert (+/- 1%)
```

---

## Strategic Tips from Guide

### Before Battle
1. Always have 100 training before attacking
2. Keep arms at 100%
3. Ensure loyalty >90 for all attacking officers
4. Never use Lu Bu or Wei Yan to command (they'll desert)
5. Bring plenty of gold (10 gold per view, up to 99 per bribe)

### During Battle
1. **Always use Simultaneous Attack** when possible
2. Surround enemies before attacking
3. Use fire to trap enemies or deny terrain
4. Bribe high-value low-loyalty targets
5. Check enemy stats with View (costs 10 gold)

### Unit Composition
1. Assign most soldiers to highest war ability officers
2. Keep one high-intel unit for fire attacks
3. Governor/defending commander should have decent war ability
4. Don't attack with officers whose loyalty <90

### Difficulty Effects
- **Level 1:** Player troops have advantage
- **Level 2:** Fair battle
- **Level 3:** Computer troops have advantage
- Higher difficulty = harder to win battles
- Computer trains troops faster on higher difficulties

---

## Key Differences from Amiga Manual

### Unit Limits
- **Amiga Manual:** Max 10 generals on battlefield at once
- **Your Correction:** 10 attacker + 5 ally vs 10 defender + 5 ally
- **Note:** PC/SNES version may differ from Amiga

### Terrain Costs
- **Amiga:** Plains 2, Mountains 4, Water 6/10, Castle 3
- **This Guide:** Fields 2, Forest 3, Hills 3, Water 5, Castle 3
- **Note:** Possible version differences or terminology differences

### Command Names
- Amiga and PC versions use different command numbering
- Core mechanics are similar across versions

---

## Important Game Mechanics

### Compatibility System
- Every general leans toward Shu, Wu, or Wei
- Compatibility affects:
  - Starting loyalty when recruited
  - How quickly loyalty decreases
  - Bribe success rate
  - Post-bribe loyalty

### Officers With High Betrayal Risk

**Lu Bu and Wei Yan**
- **Potentially** able to betray at ANY loyalty level (including 100)
- Much higher betrayal chance than other officers
- Can be bribed even at high loyalty
- NOT guaranteed - may take multiple attempts
- Still worth monitoring even with 90+ loyalty

**Normal Officers**
- At 90+ loyalty: Very unlikely to betray
- At 80-89 loyalty: Possible but rare
- Below 80 loyalty: Increasing risk

### Factors Affecting Betrayal/Bribery

**1. Compatibility (Shu/Wei/Wu Alignment)**
- Every officer leans toward Shu, Wei, or Wu
- High compatibility with bribing ruler = easier to bribe
- Low compatibility with current ruler = easier to bribe
- Compatibility affects post-bribe loyalty

**2. Familial Relationships**
- Family members very unlikely to betray each other
- Example: Cao Ang extremely unlikely to betray Cao Cao
- Blood ties override loyalty numbers

**3. Loyalty Number**
- Primary factor for normal officers
- Lu Bu/Wei Yan ignore this rule

**4. Multiple Attempts**
- May need several attempts to successfully bribe
- Success not guaranteed on first try
- Persistence matters for high-value targets

### Computer AI Behavior
- Won't attack provinces with >500 troops (as attacker limited to 5 units)
- Slow to buy arms early game
- Gets bonuses based on ruler (Cao Cao gets largest)
- Poor at training troops on lower difficulties

---

## Battle Tactics Summary

### Attacking Castles
- Move unit onto castle = instant victory
- Castle is hard to set on fire
- Defender can reinforce from castle reserves

### Defending Castles
- Keep governor with decent war ability
- Leave units in castle as reserves
- Use reinforce command to bring them out
- Castle terrain cost: 3

### Using Fire
- Check wind direction first
- Fire spreads downwind
- Can kill enemy generals if trapped
- Can backfire on your own units

### Capturing Generals
- Simultaneous attack = best for minimizing casualties
- Charge = best for capturing (but high risk)
- Fire = best for killing without combat
- Low loyalty = easy to bribe

---

*Guide compiled from GameFAQs Strategy Guide v1.22 by admtanaka (Greg Hartman)*  
*Original guide dated 4/23/2006*

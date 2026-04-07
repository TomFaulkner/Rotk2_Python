# ROTK2 Battle System - From Amiga Manual

## Overview
Battles use a hexagonal map of the contested state. Each general + troops = one unit.

## Initial Setup
1. Select generals to fight
2. Appoint commander-in-chief
3. Allocate money and rice supplies
4. Place units on battlefield (max 10 on map, rest in reserve)
5. Attacker places supply units

## Victory Conditions

Attacker wins:
- Enemy runs out of supplies
- Takes all castles
- No enemy generals left
- Kills enemy master
- Captures and releases enemy master

Defender wins:
- Steals enemy supplies
- Enemy supplies run out
- Kills enemy commander-in-chief

## Terrain System (6 Types)

| Terrain | Mobility Cost |
|---------|---------------|
| Plains | 2 |
| Mountains | 4 |
| Swamp | 5 |
| River/Water (naval) | 6 |
| River/Water (non-naval) | 10 |
| Castle | 3 |
| Highly Mountainous | Impassable |

## Mobility System

Base: ~6 mobility points

Factors affecting mobility:
- Power of general (+)
- Training level (+)
- Heavy weapons (-)
- Winter season (-2)
- Standby previous turn (+1 next turn)

Movement = Mobility / Terrain Cost
Example: 10 mobility in plains (2) = 5 hexes

## Battle Commands

1. MOVE - Move units
2. ATTACK - Attack enemy
3. RETREAT - Escape battlefield
4. SURRENDER - General surrenders
5. STANDBY - Do nothing, +1 mobility next turn
6. VIEW - View battle reports

## Attack Types

A. REGULAR ATTACK
- Standard combat
- Casualties on both sides
- General captured if soldiers reach zero

B. SIMULTANEOUS ATTACK
- Entire unit charges
- High casualties both sides
- Better when surrounding enemy

C. CHARGE
- Very high casualties
- Fight until one side destroyed
- Low chance of capturing generals

D. TRICK
- Trap enemy
- Success depends on intelligence
- Sets enemy mobility to 0
- Hard to capture generals

E. INCENDIARY ATTACK (Fire)
- Set neighboring hex on fire
- Fire spreads downwind
- Burns friend or foe
- Check wind direction first
- Cannot enter burning hex

## Capturing Generals

Options when capturing:
A. BEHEAD - Kill permanently
B. FREE - Release them
C. RECRUIT - Make subordinate (low loyalty)

Note: Captured on offense = can use in current war
Captured on defense = cannot use in reserve

## Key Stats in Battle

- Power (War) - Affects combat effectiveness
- Intelligence - Affects trick success
- Soldiers - Unit strength
- Training - Affects mobility
- Weapons - Heavy weapons reduce mobility
- Naval ability - Can cross water easier

## Fire and Wind

Fire attack spreads in wind direction.
Wind direction is shown on battle screen.
Fire burns everything - use carefully!

## Reserve System

- Max 10 generals on map
- Excess go to reserve
- Can call reinforcements if active units drop below 10

## Placement Rules

- Place only on oval marks
- Units cannot stack
- Supplies can share hex with friendly unit
- Press 0 to confirm placement

## Unit Limits

From manual: Max 10 generals on battlefield at once.
This differs from your correction (10 attacker + 5 ally vs 10 defender + 5 ally).
The manual describes the Amiga version which may differ from PC/SNES.

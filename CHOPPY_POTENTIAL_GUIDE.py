#!/usr/bin/env python3
"""
CHOPPY WATER POTENTIAL FORMULA - Complete Documentation

This system uses a three-condition formula to identify periods of elevated
danger due to wind-tide opposition combined with significant tidal range.
"""

print("=" * 70)
print("CHOPPY WATER POTENTIAL FORMULA - DOCUMENTED")
print("=" * 70)

formula = """
CONDITION 1: Tide Range
  ├─ Measured from NIWA tidal forecast data
  ├─ Compares high tide vs low tide height difference
  ├─ Threshold: > 0.5m (50cm differential)
  └─ When exceeded: More energetic tidal flows

CONDITION 2: Wind Speed
  ├─ From MetOcean forecast
  ├─ Measured in knots at 10m elevation
  ├─ Threshold: > 7 knots
  └─ When exceeded: Sufficient energy to oppose tidal currents

CONDITION 3: Wind vs Tide Opposition
  ├─ Wind direction within 45° of opposite tide flow
  ├─ Flood tide: Primary direction ~45° (NE), opposite = 225° (SW)
  ├─ Ebb tide: Primary direction ~225° (SW), opposite = 45° (NE)
  └─ When triggered: Waves and currents work against each other

COMBINED FORMULA:
  IF (Tide Range > 0.5m) AND (Wind > 7kt) AND (Opposition < 45°angle)
  THEN: Flag as 🚨 CHOPPY WATER POTENTIAL
"""

print(formula)

print("\n" + "=" * 70)
print("PHYSICAL EXPLANATION")
print("=" * 70)

explanation = """
When a large tide runs (> 50cm range):
  • Creates strong current flow in one direction
  • Increases water surface energy and momentum
  • Amplifies any opposing conditions

With sufficient wind (> 7 knots):
  • Waves begin to build and travel
  • Wind stress on surface is significant
  • Can counteract tidal currents

When wind opposes tide direction:
  • Waves travel against current direction
  • Current actively resists wave propagation
  • Results in: Shorter, steeper wave faces (not longer waves)
  • Water appears more unstable and chaotic
  • Vessel experiences increased vertical motion
  • Pitching and yawing become more pronounced

RESULT: Dangerous sea state despite moderate wave heights
  Example: 1.2m waves in opposition can feel like 1.7m waves
"""

print(explanation)

print("\n" + "=" * 70)
print("SAFETY ASSESSMENT IMPACT")
print("=" * 70)

impact = """
BEFORE this formula (old logic):
  • Opposition applied 1.4x multiplier to effective wave
  • Only reported opposition from first forecast period
  • No differentiation between minor and severe opposition
  
AFTER this formula (NEW):
  • Periods with choppy potential are clearly identified
  • Listed FIRST in opposition analysis with 🚨 WARNING
  • Complete details: tide range, wind, wave, angle
  • Separated from "standard opposition" events
  • Crew can tactically avoid those specific time windows
  • Decision-making is data-driven with clear thresholds

EXAMPLE DECISION LOGIC:

Scenario 1: Opposition with large tide + strong wind
  Tide: 1.2m range ✓
  Wind: 12kt ✓
  Opposition: Yes ✓
  → FLAG: 🚨 CHOPPY WATER POTENTIAL - AVOID

Scenario 2: Opposition with small tide + strong wind
  Tide: 0.4m range ✗
  Wind: 12kt ✓
  Opposition: Yes ✓
  → FLAG: ⚠️ Standard opposition - POSSIBLE

Scenario 3: Opposition with large tide + light wind
  Tide: 1.2m range ✓
  Wind: 5kt ✗
  Opposition: Yes ✓
  → FLAG: ⚠️ Standard opposition - MINOR CONCERN

Scenario 4: Opposition with large tide + strong wind + little angle
  Tide: 1.5m range ✓
  Wind: 16kt ✓
  Opposition: 2° angle ✓
  Wave: 1.3m (raw)
  → FLAG: 🚨 CRITICAL CHOPPY WATER - DO NOT GO
"""

print(impact)

print("\n" + "=" * 70)
print("FORECAST OUTPUT EXAMPLE")
print("=" * 70)

example = """
When a weekend forecast is checked (Fri-Sun) at Mana Marina:

🌊 **WIND/TIDE OPPOSITION ANALYSIS:**

🚨 **CHOPPY WATER POTENTIAL** (Tide > 50cm + Wind > 7kt + Opposition):

• [Fri 20 11:00] ⚠️ CRITICAL CONDITIONS
   Wind: 220° (SW) opposes Flood (NE)
   Tide range: 1.35m | Wind: 14kt | Wave: 1.2m
   Angle diff: 4° | Effect: Steep, choppy seas (40% chop increase)

• [Fri 20 14:00] ⚠️ CRITICAL CONDITIONS
   Wind: 225° (SW) opposes Flood (NE)
   Tide range: 1.40m | Wind: 16kt | Wave: 1.4m
   Angle diff: 0° | Effect: Steep, choppy seas (40% chop increase)

Standard opposition (tide ≤ 50cm or wind ≤ 7kt):

• [Fri 20 08:00] Wind 215° (SW) opposes Flood (NE)
   Tide: 0.4m | Wind: 6kt | Wave: 0.6m
   Angle: 30° | Effect: Increased chop (40% multiplier)

Summary: Wind against tide increases effective wave height by ~40%
⚠️ **2 period(s) with CHOPPY WATER POTENTIAL** - Conditions to avoid

USER INTERPRETATION:
  ✅ Friday 8am: Safe (tide too small)
  ⚠️ Friday 11am-3pm: AVOID (choppy water potential)
  ✅ Friday 5pm+: Check further forecast (opposition ends)
"""

print(example)

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

summary = """
✅ FORMULA IMPLEMENTED:
   Tide Differential > 50cm AND Wind > 7kt AND Opposition < 45° angle
   
✅ RESULTS IN:
   🚨 Flagged as CHOPPY WATER POTENTIAL
   ⚠️ Listed separately in opposition analysis
   📊 Shows tide range, wind speed, angle difference
   🎯 Enables tactical decision-making

✅ SAFETY IMPACT:
   • Crew knows exact times to avoid crossing
   • Can plan with alternative time windows
   • Understands physical cause (tidal + wind opposition)
   • Makes informed risk assessment
"""

print(summary)

print("=" * 70)

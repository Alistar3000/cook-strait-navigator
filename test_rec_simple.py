#!/usr/bin/env python3
"""Direct test of recommendation functions without full navigator import."""

import os
import sys

# Mock the get_secret function
def get_secret(key_name):
    return os.getenv(key_name, None)

# Define the location characteristics
LOCATION_CHARACTERISTICS = {
    # North Island - Wellington
    "mana marina": {"difficulty": 1, "shelter": "High", "type": "Marina", "protected": True, "best_wind": 15, "best_wave": 0.8},
    "mana": {"difficulty": 1, "shelter": "High", "type": "Beach/Estuary", "protected": True, "best_wind": 15, "best_wave": 0.8},
    "plimmerton": {"difficulty": 2, "shelter": "Medium", "type": "Beach", "protected": True, "best_wind": 18, "best_wave": 1.2},
    "pukerua bay": {"difficulty": 2, "shelter": "Medium", "type": "Beach", "protected": False, "best_wind": 20, "best_wave": 1.5},
    "titahi bay": {"difficulty": 1, "shelter": "High", "type": "Bay", "protected": True, "best_wind": 15, "best_wave": 0.9},
    "makara": {"difficulty": 3, "shelter": "Low", "type": "Exposed Beach", "protected": False, "best_wind": 12, "best_wave": 1.0},
    "terawhiti": {"difficulty": 4, "shelter": "Very Low", "type": "Exposed", "protected": False, "best_wind": 8, "best_wave": 0.5},
    "ship cove": {"difficulty": 2, "shelter": "Medium", "type": "Cove", "protected": True, "best_wind": 16, "best_wave": 1.0},
}

def get_location_recommendation_score(location_name, wind_kt, wave_m, boat_class, tide_state=None):
    """Score a location based on current/forecast weather conditions."""
    if location_name not in LOCATION_CHARACTERISTICS:
        return {"score": 50, "reason": "Unknown location"}
    
    loc = LOCATION_CHARACTERISTICS[location_name]
    score = 100
    issues = []
    positives = []
    
    # Set thresholds based on boat class and location difficulty
    if boat_class == "SMALL":
        if loc["difficulty"] >= 3:
            score -= 20
            issues.append(f"Location too exposed for small boat")
    elif boat_class == "MEDIUM":
        if loc["difficulty"] >= 4:
            score -= 15
            issues.append("Location exposed for medium boat")
    
    # Wind scoring
    best_wind = loc["best_wind"]
    if wind_kt <= best_wind - 5:
        positives.append("Light winds - ideal conditions")
        score += 10
    elif wind_kt <= best_wind:
        positives.append("Good wind conditions")
        score += 5
    elif wind_kt <= best_wind + 5:
        score -= 5
        issues.append(f"Wind slightly above ideal ({wind_kt:.0f}kt vs {best_wind}kt)")
    elif wind_kt <= best_wind + 10:
        score -= 15
        issues.append(f"Wind moderately above ideal")
    else:
        score -= 30
        issues.append(f"Wind too strong for safe fishing")
    
    # Wave scoring
    best_wave = loc["best_wave"]
    if wave_m <= best_wave - 0.3:
        positives.append("Calm seas")
        score += 10
    elif wave_m <= best_wave:
        positives.append("Wave height good")
        score += 5
    elif wave_m <= best_wave + 0.3:
        score -= 5
        issues.append(f"Waves slightly choppy")
    elif wave_m <= best_wave + 0.6:
        score -= 15
        issues.append("Waves moderately choppy")
    else:
        score -= 25
        issues.append("Seas too rough for safe fishing")
    
    # Shelter bonus
    if loc["protected"] and wind_kt > 18:
        positives.append(f"Protected location helps in moderate wind")
        score += 8
    
    # Tide condition bonus
    if tide_state in ["rising", "flood"]:
        positives.append("Rising tide - good for fishing")
        score += 5
    elif tide_state in ["falling", "ebb"]:
        issues.append("Falling tide may reduce activity")
        score -= 3
    
    score = max(0, min(100, score))
    
    reason = ""
    if positives:
        reason = ", ".join(positives)
    if issues:
        reason += (" | " if reason else "") + " ⚠️ ".join(issues)
    if not reason:
        reason = "Average conditions"
    
    return {
        "score": score,
        "location": location_name,
        "conditions": f"{wind_kt:.0f}kt wind, {wave_m:.1f}m waves",
        "reason": reason,
        "type": loc["type"],
        "shelter": loc["shelter"]
    }

def recommend_fishing_locations(wind_data, wave_data, boat_class, boat_size, tide_state=None, num_recommendations=3):
    """Recommend best fishing locations based on weather forecast."""
    if not wind_data or not wave_data:
        return ""
    
    # Use average conditions from forecast
    avg_wind = sum(wind_data[:3]) / len(wind_data[:3]) if wind_data else 0
    avg_wave = sum(wave_data[:3]) / len(wave_data[:3]) if wave_data else 0
    
    # Score all locations
    scores = []
    for location_name in LOCATION_CHARACTERISTICS.keys():
        result = get_location_recommendation_score(
            location_name, avg_wind, avg_wave, boat_class, tide_state
        )
        scores.append(result)
    
    # Sort by score
    scores.sort(key=lambda x: x["score"], reverse=True)
    
    # Filter good locations
    good_locations = [s for s in scores if s["score"] > 40]
    
    if not good_locations:
        return "\n🎣 **Location Status:** Current conditions challenging for fishing\n"
    
    # Format recommendations
    recommendation_text = "\n🎣 **Recommended Fishing Locations:**\n"
    
    for i, loc in enumerate(good_locations[:num_recommendations], 1):
        score_emoji = "🟢" if loc["score"] > 75 else "🟡" if loc["score"] > 55 else "🟠"
        recommendation_text += f"{i}. {score_emoji} **{loc['location'].title()}** ({loc['shelter']} shelter, {loc['type']})\n"
        recommendation_text += f"   Score: {loc['score']:.0f}/100 | {loc['conditions']}\n"
        recommendation_text += f"   {loc['reason']}\n"
    
    return recommendation_text


# Run tests
print("="*60)
print("Test Case 1: Good conditions (calm day)")
print("="*60)

wind_gust = [10, 12, 11, 10, 13, 12]
wave_height = [0.6, 0.7, 0.7, 0.6, 0.8, 0.7]
boat_class = "SMALL"
boat_size = 5.0

result = recommend_fishing_locations(wind_gust, wave_height, boat_class, boat_size, tide_state="rising")
print(result)

# Test case 2: Moderate conditions
print("\n" + "="*60)
print("Test Case 2: Moderate wind/waves")
print("="*60)

wind_gust = [18, 20, 19, 21, 22, 20]
wave_height = [1.2, 1.4, 1.3, 1.5, 1.6, 1.4]
boat_class = "MEDIUM"
boat_size = 8.0

result = recommend_fishing_locations(wind_gust, wave_height, boat_class, boat_size, tide_state="falling")
print(result)

# Test case 3: Rough conditions
print("\n" + "="*60)
print("Test Case 3: Rough conditions")
print("="*60)

wind_gust = [28, 30, 32, 31, 29, 30]
wave_height = [2.2, 2.4, 2.6, 2.5, 2.3, 2.4]
boat_class = "LARGE"
boat_size = 10.0

result = recommend_fishing_locations(wind_gust, wave_height, boat_class, boat_size)
print(result)

# Test individual location scores
print("\n" + "="*60)
print("Test Case 4: Detailed location scoring")
print("="*60)

test_locations = ["mana", "titahi bay", "ship cove", "terawhiti"]
wind = 15  # knots
wave = 1.0  # meters
boat_class = "MEDIUM"

for loc in test_locations:
    score = get_location_recommendation_score(loc, wind, wave, boat_class, "rising")
    print(f"\n{loc.title()}:")
    print(f"  Score: {score['score']:.0f}/100")
    print(f"  Type: {score['type']}, Shelter: {score['shelter']}")
    print(f"  Reason: {score['reason']}")

print("\n✅ All recommendation tests completed!")

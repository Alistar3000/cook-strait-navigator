# Mooring & Anchorage Locations

This folder contains information about anchorages, moorings, and bays in the Marlborough Sounds and surrounding areas.

## Purpose

The system uses this data to recommend safe overnight stops and shelter locations based on current and forecast weather conditions. When users ask "Where should I anchor tonight?" or "Best bay for northerly winds?", the AI searches this knowledge base.

## What to Include

Your documents should contain information about:

### Essential Information
- **Bay/Location Name**: Clear identification
- **Geographic Location**: Which sound, channel, or area
- **Shelter Direction**: Protection from which wind directions (N, NE, E, SE, S, SW, W, NW)
- **Holding Ground**: Mud, sand, rock, shell - and quality (good/poor)
- **Depth**: Typical anchoring depths
- **Swing Room**: Space available for anchoring

### Additional Useful Information
- **Approach Notes**: Hazards, channels, leading marks
- **Facilities**: Moorings, marina, supplies, water
- **Hazards**: Rocks, reefs, cables, traffic
- **Tidal Considerations**: Current strength, tidal range effects
- **Weather Notes**: Known wind funneling, katabatic effects
- **Alternative Anchorages**: Nearby options if this one is unsuitable

## File Format

The system accepts:
- **Plain text (.txt)** - Recommended for easy editing
- **Markdown (.md)** - Good for organized notes
- **PDF (.pdf)** - For scanned cruising guides or charts

## Example Entry Format

```
Bay Name: Ship Cove, Queen Charlotte Sound

Location: Northwest corner of Queen Charlotte Sound, 5nm from Tory Channel entrance

Shelter: Excellent protection from N, NE, E, SE, S. Open to W and NW but these are rare. Best all-weather anchorage in outer QCS.

Holding: Good holding in mud, 8-12m depths. 

Approach: Clear entrance, keep to center of bay. Watch for shallow patch (2m) off western point marked by kelp.

Facilities: DOC mooring buoys (limited), water ashore at Captain Cook memorial.

Notes: Popular anchorage, can be crowded in summer. Excellent for northerly storms.
```

## After Adding Files

Once you've added your mooring location documents to this folder, run:

```bash
python ingest_knowledge.py
```

This will process the documents and make them available for the AI to search when providing mooring recommendations.

## Tips

- Include date-based notes if conditions change seasonally
- Mention if the bay is better suited for certain boat sizes
- Note if facilities or conditions have changed over time
- Personal experience notes are valuable (e.g., "best holding in the SE corner")

# Tournament Director .tdt Parser

A Python parser for extracting tournament data from Tournament Director .tdt save files.

## Overview

This parser reads Tournament Director save files (.tdt format) and extracts comprehensive tournament information including player data, buy-ins, rebuys, add-ons, final rankings, and prize distributions.

## Features

- **Tournament Information**: Extracts basic tournament details (league, description, buy-in fee)
- **Player Data**: Comprehensive player statistics including buy-ins, rebuys, add-ons, and total investment
- **Final Rankings**: Calculates player finishing positions based on elimination order and prize winners
- **Prize Structure**: Extracts prize percentages and actual prize money awarded
- **JSON Output**: Generates structured JSON output for further analysis

## Usage

### Basic Usage

```bash
python src/tournament_parser.py "path/to/your/tournament.tdt"
```

### Output

The parser provides:

1. **Console Output**: Formatted tournament summary with player rankings
2. **JSON File**: Complete structured data saved as `<filename>.tournament_results.json`

### Example Output

```
================================================================================
TOURNAMENT SUMMARY: Weekly Game 2025
League: Paul's Poker League
Buy-in: $25
================================================================================

Total Players: 12
Total Prize Pool: $550
Total Prizes Awarded: $550
Buy-ins: 12, Rebuys: 2, Add-ons: 8

================================================================================
PRIZE STRUCTURE
================================================================================
1st Place: $253 (46%) - Player A
2nd Place: $149 (27%) - Player B  
3rd Place: $94 (17%) - Player C
4th Place: $55 (10%) - Player D

================================================================================
FINAL RESULTS
================================================================================

Pos   Player Name               Buy-ins  Rebuys  Add-ons  Total $  Elim Rd  Prize Won
------------------------------------------------------------------------------------------------------------------------
#1    Player A                  1        0       1        $50      Active   $253     
#2    Player B                  1        1       1        $75      Active   $149      
#3    Player C                  1        0       1        $50      Active   $94      
#4    Player D                  1        0       1        $50      Active   $55      
#5    Player E                  1        0       0        $25      Active   -        
...
```

## File Structure

```
├── README.md                    # This file
├── src/
│   └── tournament_parser.py     # Main parser script
└── your_tournament_files/       # Place your .tdt files here
    └── *.tdt                    # Tournament Director save files
```

## Requirements

- Python 3.6+
- No external dependencies required (uses only standard library)

## How It Works

The parser analyzes Tournament Director .tdt files which contain JavaScript-like object definitions for tournament data:

1. **Tournament Extraction**: Parses version, description, league info, and buy-in structure
2. **Player Processing**: Extracts player details, buy-ins, rebuys, add-ons from `GamePlayer` objects
3. **Prize Parsing**: Identifies prize structure from `GamePrize` objects
4. **Ranking Calculation**: Determines final positions based on:
   - Prize winners (explicit positions)
   - Elimination order for remaining players
   - Active players ranked by participation

## Data Structure

The parser outputs JSON with the following structure:

```json
{
  "tournament": {
    "version": "3.7.2",
    "description": "Weekly Game 2025",
    "league": "Paul's Poker League",
    "buyin_fee": 25
  },
  "players": [
    {
      "uuid": "player-uuid",
      "name": "Player A",
      "buyins": 1,
      "rebuys": 0,
      "addons": 1,
      "total_invested": 50,
      "final_position": 1,
      "prize_won": 253,
      "elimination_round": null
    }
  ],
  "prizes": [
    {
      "description": "1st Place",
      "position": 1,
      "percentage": 46,
      "prize_money": 253,
      "winner_uuids": ["player-uuid"]
    }
  ],
  "summary": {
    "total_players": 12,
    "total_prize_pool": 550,
    "total_prizes_awarded": 550,
    "total_buyins": 12,
    "total_rebuys": 2,
    "total_addons": 8
  }
}
```

## About Tournament Director

Tournament Director is poker tournament management software available at [https://thetournamentdirector.net](https://thetournamentdirector.net). This parser works with .tdt save files from version 3.7.2+.

## License

This project is open source and available under the MIT License.
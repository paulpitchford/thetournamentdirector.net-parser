#!/usr/bin/env python3
"""
Tournament Director .tdt Parser
Extracts tournament info, player data, rankings, and prize information from .tdt save files
"""

import re
import json
import sys
from pathlib import Path

def parse_tournament_file(filepath):
    """Parse a Tournament Director .tdt file completely"""
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    data = {
        'tournament': {},
        'players': [],
        'prizes': [],
        'summary': {}
    }
    
    # Extract tournament information
    version_match = re.search(r'V:\s*"([^"]+)"', content)
    if version_match:
        data['tournament']['version'] = version_match.group(1)
    
    desc_match = re.search(r'Description:\s*"([^"]+)"', content)
    if desc_match:
        data['tournament']['description'] = desc_match.group(1)
    
    league_match = re.search(r'LeagueName:\s*"([^"]+)"', content)
    if league_match:
        data['tournament']['league'] = league_match.group(1)
    
    # Extract buy-in fee
    fee_match = re.search(r'Buyins:.*?Fee:\s*(\d+)', content, re.DOTALL)
    if fee_match:
        data['tournament']['buyin_fee'] = int(fee_match.group(1))
    
    # Extract prize information - look for the Prizes section in single line format
    # First find if there are any GamePrize entries in the file
    game_prizes = re.findall(r'new GamePrize\(\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\)', content)
    
    if game_prizes:
        # Process each prize entry
        for prize_data in game_prizes:
            
            prize = {}
            
            # Extract description (1st Place, 2nd Place, etc.)
            desc = re.search(r'Description:\s*"([^"]+)"', prize_data)
            if desc:
                prize['description'] = desc.group(1)
            
            # Extract recipient (position number)
            recipient = re.search(r'Recipient:\s*(\d+)', prize_data)
            if recipient:
                prize['position'] = int(recipient.group(1))
            
            # Extract percentage amount
            amount = re.search(r'Amount:\s*(\d+)', prize_data)
            if amount:
                prize['percentage'] = int(amount.group(1))
            
            # Extract calculated amount (actual prize money)
            calc_amount = re.search(r'CalculatedAmount:\s*(\d+)', prize_data)
            if calc_amount:
                prize['prize_money'] = int(calc_amount.group(1))
            
            # Extract awarded players (winners)
            awarded = re.search(r'AwardedToPlayers:\s*\[([^\]]*)\]', prize_data)
            if awarded:
                awarded_content = awarded.group(1)
                uuids = re.findall(r'"([^"]+)"', awarded_content)
                prize['winner_uuids'] = uuids
            else:
                prize['winner_uuids'] = []
            
            data['prizes'].append(prize)
    
    # Extract player data
    player_blocks = re.split(r'new GamePlayer\(\{', content)[1:]
    
    for block in player_blocks:
        # Extract UUID
        uuid_match = re.search(r'UUID:\s*"([^"]+)"', block)
        if not uuid_match:
            continue
        
        player_uuid = uuid_match.group(1)
        
        # Extract name
        nickname = re.search(r'Nickname:\s*"([^"]*)"', block)
        firstname = re.search(r'Firstname:\s*"([^"]*)"', block)
        lastname = re.search(r'Lastname:\s*"([^"]*)"', block)
        
        name = ""
        if nickname and nickname.group(1).strip():
            name = nickname.group(1).strip()
        else:
            parts = []
            if firstname and firstname.group(1).strip():
                parts.append(firstname.group(1).strip())
            if lastname and lastname.group(1).strip():
                parts.append(lastname.group(1).strip())
            name = " ".join(parts)
        
        if not name:
            continue  # Skip unnamed players
        
        # Check if player participated
        buyins_match = re.search(r'Buyins:\s*\[([^\]]*)\]', block)
        paid_match = re.search(r'PaidInFull:\s*(true|false)', block)
        paid = paid_match and paid_match.group(1) == 'true'
        
        # Skip players who didn't participate
        if not buyins_match or not buyins_match.group(1).strip():
            if not paid:
                continue
        
        player = {
            'uuid': player_uuid,
            'name': name,
            'buyins': 0,
            'rebuys': 0,
            'addons': 0,
            'total_invested': 0,
            'final_position': None,
            'prize_won': 0,
            'elimination_round': None
        }
        
        # Count buy-ins and rebuys
        buyin_blocks = re.findall(r'new GameBuyin\(\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\)', block)
        for i, buyin_match in enumerate(buyin_blocks):
            amount_match = re.search(r'Amount:\s*(\d+)', buyin_match)
            if amount_match:
                amount = int(amount_match.group(1))
                if i == 0:
                    player['buyins'] = 1
                else:
                    player['rebuys'] += 1
                player['total_invested'] += amount
            
            # Check for elimination
            bustout_match = re.search(r'BustOut:\s*new GameBustOut\(\{([^}]+)\}\)', buyin_match)
            if bustout_match:
                bust_data = bustout_match.group(1)
                round_match = re.search(r'Round:\s*(\d+)', bust_data)
                if round_match:
                    player['elimination_round'] = int(round_match.group(1))
        
        # Count add-ons
        addon_blocks = re.findall(r'new GameAddOn\(\{([^}]+)\}\)', block)
        for addon_match in addon_blocks:
            amount_match = re.search(r'Amount:\s*(\d+)', addon_match)
            if amount_match:
                player['addons'] += 1
                player['total_invested'] += int(amount_match.group(1))
        
        data['players'].append(player)
    
    # Match players to prizes
    for prize in data['prizes']:
        for winner_uuid in prize['winner_uuids']:
            for player in data['players']:
                if player['uuid'] == winner_uuid:
                    player['final_position'] = prize['position']
                    player['prize_won'] = prize['prize_money']
                    break
    
    # Calculate remaining positions based on elimination order
    unranked_players = [p for p in data['players'] if p['final_position'] is None]
    
    # Sort by elimination round (later elimination = better position)
    eliminated_players = [p for p in unranked_players if p['elimination_round'] is not None]
    eliminated_players.sort(key=lambda x: x['elimination_round'], reverse=True)
    
    # Active players (no elimination)
    active_players = [p for p in unranked_players if p['elimination_round'] is None]
    
    # Assign positions starting after the highest prize position
    max_prize_position = max([p['position'] for p in data['prizes']], default=0)
    position = max_prize_position + 1
    
    # Active players first
    for player in active_players:
        player['final_position'] = position
        position += 1
    
    # Then eliminated players
    for player in eliminated_players:
        player['final_position'] = position
        position += 1
    
    # Calculate summary
    data['summary'] = {
        'total_players': len(data['players']),
        'total_prize_pool': sum(p['total_invested'] for p in data['players']),
        'total_prizes_awarded': sum(p['prize_money'] for p in data['prizes']),
        'total_buyins': sum(p['buyins'] for p in data['players']),
        'total_rebuys': sum(p['rebuys'] for p in data['players']),
        'total_addons': sum(p['addons'] for p in data['players'])
    }
    
    return data

def display_tournament_results(data):
    """Display comprehensive tournament results"""
    
    print(f"\n{'='*120}")
    print(f"TOURNAMENT SUMMARY: {data['tournament'].get('description', 'Unknown')}")
    print(f"League: {data['tournament'].get('league', 'Unknown')}")
    print(f"Buy-in: ${data['tournament'].get('buyin_fee', 0)}")
    print(f"{'='*120}")
    
    # Tournament summary
    summary = data['summary']
    print(f"\nTotal Players: {summary['total_players']}")
    print(f"Total Prize Pool: ${summary['total_prize_pool']}")
    print(f"Total Prizes Awarded: ${summary['total_prizes_awarded']}")
    print(f"Buy-ins: {summary['total_buyins']}, Rebuys: {summary['total_rebuys']}, Add-ons: {summary['total_addons']}")
    
    # Prize structure
    if data['prizes']:
        print(f"\n{'='*120}")
        print("PRIZE STRUCTURE")
        print(f"{'='*120}")
        
        for prize in sorted(data['prizes'], key=lambda x: x['position']):
            winner_names = []
            for uuid in prize['winner_uuids']:
                for player in data['players']:
                    if player['uuid'] == uuid:
                        winner_names.append(player['name'])
                        break
            
            winner_str = ", ".join(winner_names) if winner_names else "Not awarded"
            print(f"{prize['description']}: ${prize['prize_money']} ({prize['percentage']}%) - {winner_str}")
    
    # Player results
    print(f"\n{'='*120}")
    print("FINAL RESULTS")
    print(f"{'='*120}")
    
    # Sort players by final position
    players_sorted = sorted(data['players'], key=lambda x: (
        x['final_position'] if x['final_position'] is not None else 999
    ))
    
    print(f"\n{'Pos':<5} {'Player Name':<25} {'Buy-ins':<8} {'Rebuys':<7} {'Add-ons':<8} {'Total $':<8} {'Elim Rd':<8} {'Prize Won':<10}")
    print("-" * 120)
    
    for player in players_sorted:
        pos = f"#{player['final_position']}" if player['final_position'] is not None else "-"
        name = player['name'][:24]
        buyins = player['buyins']
        rebuys = player['rebuys']
        addons = player['addons']
        total = player['total_invested']
        elim_rd = f"R{player['elimination_round']}" if player['elimination_round'] else "Active"
        prize = f"${player['prize_won']}" if player['prize_won'] > 0 else "-"
        
        print(f"{pos:<5} {name:<25} {buyins:<8} {rebuys:<7} {addons:<8} ${total:<7} {elim_rd:<8} {prize:<10}")

def main():
    if len(sys.argv) < 2:
        print("\nUsage: python tournament_parser.py <tdt_file>")
        print("\nExample:")
        print('  python tournament_parser.py "game 3 25.tdt"')
        return
    
    filepath = Path(sys.argv[1])
    
    if not filepath.exists():
        print(f"Error: File not found - {filepath}")
        return
    
    print(f"Parsing tournament file: {filepath.name}")
    
    try:
        data = parse_tournament_file(filepath)
        display_tournament_results(data)
        
        # Save complete data as JSON
        json_output = filepath.with_suffix('.tournament_results.json')
        with open(json_output, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"\nComplete data saved to: {json_output.name}")
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
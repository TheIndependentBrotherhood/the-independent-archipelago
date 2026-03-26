import json

# Load existing games
with open('../data/games.json', 'r', encoding='utf-8') as f:
    games_data = json.load(f)

# Add missing inProgress attribute
missing_count = 0
for game in games_data['games']:
    if 'inProgress' not in game:
        game['inProgress'] = []
        missing_count += 1

# Save updated games
with open('../data/games.json', 'w', encoding='utf-8') as f:
    json.dump(games_data, f, indent=2, ensure_ascii=False)

print(f"Added missing inProgress attribute to {missing_count} games")
print(f"Total games: {len(games_data['games'])}")

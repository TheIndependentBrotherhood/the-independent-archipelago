import json

# Load games and add inProgress field if missing
with open('../data/games.json', 'r', encoding='utf-8') as f:
    games_data = json.load(f)

for game in games_data['games']:
    if 'inProgress' not in game:
        game['inProgress'] = []

with open('../data/games.json', 'w', encoding='utf-8') as f:
    json.dump(games_data, f, indent=2, ensure_ascii=False)

print(f"✅ Added inProgress field to all {len(games_data['games'])} games")

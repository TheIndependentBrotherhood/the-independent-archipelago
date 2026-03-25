import json

# Sort games.json
with open('data/games.json', 'r', encoding='utf-8') as f:
    games_data = json.load(f)

games_data['games'] = sorted(games_data['games'], key=lambda g: g['name'].lower())

with open('data/games.json', 'w', encoding='utf-8') as f:
    json.dump(games_data, f, indent=2, ensure_ascii=False)

# Sort users.json
with open('data/users.json', 'r', encoding='utf-8') as f:
    users_data = json.load(f)

users_data['users'] = sorted(users_data['users'], key=lambda u: u['pseudo'].lower())

with open('data/users.json', 'w', encoding='utf-8') as f:
    json.dump(users_data, f, indent=2, ensure_ascii=False)

print("✅ Fichiers triés avec succès!")
print(f"  - {len(games_data['games'])} jeux triés par nom")
print(f"  - {len(users_data['users'])} utilisateurs triés par pseudo")

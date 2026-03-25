import json
from collections import defaultdict
from difflib import SequenceMatcher

# Load games.json
with open('data/games.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

games = data['games']

# Check for duplicates by name
name_dict = defaultdict(list)
for game in games:
    name_dict[game['name'].lower()].append(game)

# Find potential duplicates
print('=== DOUBLONS POTENTIELS PAR NOM IDENTIQUE ===\n')
duplicates_found = False
for name, game_list in sorted(name_dict.items()):
    if len(game_list) > 1:
        duplicates_found = True
        print(f'{name} ({len(game_list)} entrées):')
        for game in game_list:
            url_short = game['url'][:60] if game['url'] else 'N/A'
            print(
                f'  - {game["id"]} | Platform: {game["platform"]} | {url_short}...')
        print()

if not duplicates_found:
    print('Aucun doublon par nom exact trouvé.\n')

# Check for similar names
print('=== JEUX AVEC NOMS TRÈS SIMILAIRES (70%-99%) ===\n')


def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


similar_games = []
for i, game1 in enumerate(games):
    for game2 in games[i+1:]:
        ratio = similarity(game1['name'], game2['name'])
        if 0.7 < ratio < 1.0:  # Similar but not identical
            similar_games.append((ratio, game1, game2))

similar_games.sort(reverse=True)
if similar_games:
    for ratio, g1, g2 in similar_games[:25]:  # Show top 25
        print(f'Similarité: {ratio:.1%}')
        print(f'  1. {g1["id"]} | {g1["name"]} ({g1["platform"]})')
        print(f'  2. {g2["id"]} | {g2["name"]} ({g2["platform"]})')
        print()
else:
    print('Aucun jeu avec nom similaire trouvé.\n')

print(f'\nTotal: {len(games)} jeux')

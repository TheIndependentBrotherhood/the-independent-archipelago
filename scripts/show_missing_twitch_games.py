#!/usr/bin/env python3
"""
Affiche les jeux qui n'ont pas d'ID Twitch associé
"""

import json
import os


def main():
    games_file = "data/games.json"
    mapping_file = "data/twitch_games_mapping.json"

    # Charger les fichiers
    with open(games_file, 'r', encoding='utf-8') as f:
        games_data = json.load(f)

    with open(mapping_file, 'r', encoding='utf-8') as f:
        twitch_mapping = json.load(f)

    # Trouver les jeux manquants
    games = games_data.get('games', [])
    missing_games = []
    found_games = []

    for game in games:
        game_name = game.get('name')
        if game_name in twitch_mapping:
            found_games.append(game_name)
        else:
            missing_games.append(game_name)

    # Afficher les résultats
    print("=" * 70)
    print(f"RÉSUMÉ: {len(found_games)}/{len(games)} jeux trouvés sur Twitch")
    print("=" * 70)
    print()

    if missing_games:
        print(f"❌ {len(missing_games)} jeux NON TROUVÉS sur Twitch:\n")
        for idx, game_name in enumerate(sorted(missing_games), 1):
            print(f"  {idx:3d}. {game_name}")

        print()
        print("=" * 70)
    else:
        print("✓ Tous les jeux ont une image Twitch!")


if __name__ == "__main__":
    main()

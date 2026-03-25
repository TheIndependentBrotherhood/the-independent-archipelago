#!/usr/bin/env python3
"""
Merge Twitch game IDs from twitch_games_mapping.json into games.json
"""

import json
import sys

try:
    # Load twitch mapping
    with open("data/twitch_games_mapping.json", "r") as f:
        twitch_mapping = json.load(f)

    # Load games
    with open("data/games.json", "r") as f:
        games_data = json.load(f)

    # Merge: add twitchId to each game
    merged_count = 0
    for game in games_data["games"]:
        game_name = game["name"]
        if game_name in twitch_mapping:
            game["twitchId"] = twitch_mapping[game_name]
            merged_count += 1
        else:
            game["twitchId"] = None

    # Save updated games.json
    with open("data/games.json", "w") as f:
        json.dump(games_data, f, indent=2, ensure_ascii=False)

    print(
        f"✅ Succès! {merged_count}/{len(games_data['games'])} jeux ont un Twitch ID")
    print(f"Fichier sauvegardé: data/games.json")

except Exception as e:
    print(f"❌ Erreur: {e}", file=sys.stderr)
    sys.exit(1)

#!/usr/bin/env python3
"""
Récupère tous les jeux disponibles sur Twitch via l'API Helix
et génère un mapping nom_jeu -> id_twitch pour les images boxart
"""

import requests
import json
import re
from typing import Dict, List, Optional

# Credentials Twitch
CLIENT_ID = "tmouo7p8oqhx6e6qa10m1wd0mhhcm3"
CLIENT_SECRET = "sc5a9y8ncq64ihe2he5uwn8mw3e307"
REFRESH_TOKEN = "9zh5zst9a9pon8uijo247tkwhbmrk4h2aof95ygh4roypfg5io"


class TwitchAPI:
    def __init__(self):
        self.access_token = None
        self.base_url = "https://api.twitch.tv/helix"
        self.authenticate()

    def authenticate(self) -> bool:
        """Récupère un access token via le refresh token"""
        url = "https://id.twitch.tv/oauth2/token"
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN
        }

        try:
            response = requests.post(url, data=data)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get('access_token')

            if self.access_token:
                print(f"✓ Authentication réussi")
                return True
            else:
                print("✗ Impossible de récupérer le token")
                return False

        except requests.exceptions.RequestException as e:
            print(f"✗ Erreur d'authentification: {e}")
            return False

    def get_game_id_by_name(self, game_name: str) -> Optional[str]:
        """Récupère l'ID Twitch d'un jeu par son nom"""
        if not self.access_token:
            return None

        headers = {
            "Client-ID": CLIENT_ID,
            "Authorization": f"Bearer {self.access_token}"
        }

        url = f"{self.base_url}/games"
        params = {"name": game_name}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get('data') and len(data.get('data')) > 0:
                return data['data'][0]['id']
            return None

        except requests.exceptions.RequestException as e:
            print(f"✗ Erreur lors de la récupération de {game_name}: {e}")
            return None

    def get_all_games_from_file(self, games_file: str) -> Dict[str, str]:
        """
        Lit le fichier games.json et retourne un mapping
        game_name -> twitch_id
        """
        mapping = {}

        try:
            with open(games_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            games = data.get('games', [])
            total = len(games)

            print(f"\nTraitement de {total} jeux...")

            for idx, game in enumerate(games, 1):
                game_name = game.get('name')
                if game_name:
                    # Chercher l'ID Twitch
                    twitch_id = self.get_game_id_by_name(game_name)

                    if twitch_id:
                        mapping[game_name] = twitch_id
                        print(f"[{idx}/{total}] ✓ {game_name} -> {twitch_id}")
                    else:
                        print(f"[{idx}/{total}] - {game_name} (non trouvé)")

            return mapping

        except Exception as e:
            print(f"✗ Erreur lors de la lecture du fichier: {e}")
            return {}


def main():
    print("=" * 60)
    print("Récupération des IDs Twitch pour les jeux Archipelago")
    print("=" * 60)

    api = TwitchAPI()

    if not api.access_token:
        print("\n✗ Impossible de se connecter à l'API Twitch")
        return

    games_file = "data/games.json"
    mapping = api.get_all_games_from_file(games_file)

    if mapping:
        output_file = "data/twitch_games_mapping.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Mapping sauvegardé dans {output_file}")
        print(f"✓ {len(mapping)} jeux trouvés sur Twitch")
    else:
        print("\n✗ Aucun jeu trouvé")


if __name__ == "__main__":
    main()

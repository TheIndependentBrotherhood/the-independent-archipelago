import json
from html.parser import HTMLParser
import re

# Parse HTML to extract games


class GameParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.games = []
        self.in_link = False
        self.current_game = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_dict = dict(attrs)
            if 'href' in attrs_dict and 'title' in attrs_dict:
                self.current_game = {
                    'name': attrs_dict['title'],
                    'href': attrs_dict['href']
                }
                self.in_link = True

    def handle_endtag(self, tag):
        if tag == 'a' and self.current_game:
            self.games.append(self.current_game)
            self.current_game = None
            self.in_link = False


# Read HTML file
with open('../data/origin/archipelago_wiki_first_page.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Parse games from HTML
parser = GameParser()
parser.feed(html_content)
wiki_games = parser.games

print(f"Extracted {len(wiki_games)} games from wiki HTML")

# Load existing games
with open('../data/games.json', 'r', encoding='utf-8') as f:
    games_data = json.load(f)

games_by_id = {game['id']: game for game in games_data['games']}

# Update/add games from wiki
updated_count = 0
added_count = 0

for wiki_game in wiki_games:
    name = wiki_game['name'].strip()
    href = wiki_game['href'].strip()
    wiki_url = f"https://archipelago.miraheze.org{href}"

    # Create game ID
    game_id = name.lower().replace(' ', '-').replace(':', '').replace("'", '').replace('!',
                                                                                       '').replace('&', 'and').replace('/', '-').replace('.', '').replace(',', '')
    # Clean up multiple dashes
    game_id = re.sub(r'-+', '-', game_id).strip('-')

    if game_id in games_by_id:
        # Update existing game
        games_by_id[game_id]['url'] = wiki_url
        updated_count += 1
    else:
        # Add new game
        game = {
            "id": game_id,
            "name": name,
            "platform": "Unknown",
            "url": wiki_url,
            "description": f"Archipelago randomizer for {name}",
            "githubUrl": None,
            "discordUrl": None,
            "completed": [],
            "todo": []
        }
        games_by_id[game_id] = game
        added_count += 1

# Convert back to list, sort by name
updated_games = sorted(games_by_id.values(), key=lambda g: g['name'].lower())
result = {"games": updated_games}

with open('../data/games.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Updated {updated_count} games with wiki URLs")
print(f"Added {added_count} new games")
print(f"Total games: {len(updated_games)}")

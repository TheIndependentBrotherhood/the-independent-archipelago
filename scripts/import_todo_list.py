import json
import sys
import os


def normalize_user_id(pseudo):
    """
    Create a normalized user ID from pseudo.
    Example: "John Doe" -> "johndoe"
    """
    return pseudo.strip().lower().replace(' ', '').replace("'", '')


def add_user_if_not_exists(pseudo):
    """
    Add a new user to users.json if it doesn't exist.
    Uses wolf emoji (🐺) by default and maintains alphabetical order.
    """
    try:
        # Load existing users
        with open('../data/users.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)

        user_id = normalize_user_id(pseudo)

        # Check if user already exists
        for user in users_data['users']:
            if user['id'] == user_id or user['pseudo'] == pseudo:
                return user_id  # User already exists

        # Create new user with wolf emoji
        new_user = {
            "id": user_id,
            "pseudo": pseudo,
            "emoji": "🐺"
        }

        # Add user and maintain alphabetical order by pseudo
        users_data['users'].append(new_user)
        users_data['users'].sort(key=lambda u: u['pseudo'].lower())

        # Save updated users
        with open('../data/users.json', 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Created new user: {pseudo} (emoji: 🐺)")
        return user_id

    except Exception as e:
        print(f"Error managing users: {e}")
        return None


def import_todo_list(json_file_path):
    """
    Import a todo list JSON file and add the pseudo to the games.

    JSON file format:
    {
      "pseudo": "PlayerName",
      "gameIds": ["game-id-1", "game-id-2", ...]
    }
    """

    # Check if file exists
    if not os.path.exists(json_file_path):
        print(f"Error: File not found: {json_file_path}")
        return False

    try:
        # Read the todo list JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            todo_data = json.load(f)

        # Validate the structure
        if 'pseudo' not in todo_data or 'gameIds' not in todo_data:
            print("Error: Invalid JSON format. Expected 'pseudo' and 'gameIds' fields.")
            return False

        pseudo = todo_data['pseudo'].strip()
        game_ids = todo_data['gameIds']

        if not pseudo:
            print("Error: Pseudo cannot be empty")
            return False

        if not isinstance(game_ids, list):
            print("Error: gameIds must be an array")
            return False

        print(f"Importing todo list for pseudo: {pseudo}")
        print(f"Games to add: {len(game_ids)}")

        # Add user if doesn't exist
        user_id = add_user_if_not_exists(pseudo)
        if not user_id:
            print("Error: Could not create or retrieve user")
            return False

        # Load existing games
        with open('../data/games.json', 'r', encoding='utf-8') as f:
            games_data = json.load(f)

        # Create a map of game IDs for quick lookup
        games_by_id = {game['id']: game for game in games_data['games']}

        # Add the user ID to each game's todo list
        added_count = 0
        not_found = []

        for game_id in game_ids:
            if game_id in games_by_id:
                game = games_by_id[game_id]
                # Check if user ID is already in the todo list
                if user_id not in game['todo']:
                    game['todo'].append(user_id)
                    added_count += 1
            else:
                not_found.append(game_id)

        # Save updated games
        with open('../data/games.json', 'w', encoding='utf-8') as f:
            json.dump(games_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Added {pseudo} to {added_count} games' todo list")

        if not_found:
            print(f"⚠ Warning: {len(not_found)} game IDs not found:")
            for gid in not_found[:5]:  # Show first 5
                print(f"  - {gid}")
            if len(not_found) > 5:
                print(f"  ... and {len(not_found) - 5} more")

        return True

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python import_todo_list.py <path_to_json_file>")
        print("Example: python import_todo_list.py john_doe_todo_list.json")
        sys.exit(1)

    json_file = sys.argv[1]
    success = import_todo_list(json_file)
    sys.exit(0 if success else 1)

import json
import sys
import os


def import_todo_list(json_file_path):
    """
    Import a todo list JSON file and add the games to a user.

    JSON file format:
    {
      "id": "user-id-or-uuid",  // Existing user ID or UUID v4 for new users
      "gameIds": ["game-id-1", "game-id-2", ...]
    }

    For new users (UUID ID), the pseudo is extracted from the filename:
    "JeanDupont_todo_list.json" -> pseudo = "JeanDupont"
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
        if 'id' not in todo_data or 'gameIds' not in todo_data:
            print("Error: Invalid JSON format. Expected 'id' and 'gameIds' fields.")
            return False

        user_id = todo_data['id'].strip()
        game_ids = todo_data['gameIds']

        if not user_id:
            print("Error: User ID cannot be empty")
            return False

        if not isinstance(game_ids, list):
            print("Error: gameIds must be an array")
            return False

        # Extract pseudo from filename for logging (e.g., "JeanDupont_todo_list.json" -> "JeanDupont")
        filename = os.path.basename(json_file_path)
        pseudo_from_filename = filename.replace(
            '_todo_list.json', '').replace('.json', '')

        print(f"Importing todo list for ID: {user_id}")
        print(f"Games to add: {len(game_ids)}")

        # Load existing users to check if user exists
        with open('../data/users.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)

        # Check if user already exists
        existing_user = None
        for user in users_data['users']:
            if user['id'] == user_id:
                existing_user = user
                break

        if existing_user:
            print(f"✓ User '{existing_user['pseudo']}' found")
        else:
            # New user - create it with pseudo from filename and provided UUID
            print(f"✓ Creating new user with ID: {user_id}")
            new_user = {
                "id": user_id,
                "pseudo": pseudo_from_filename,
                "emoji": "🐺"
            }
            users_data['users'].append(new_user)
            users_data['users'].sort(key=lambda u: u['pseudo'].lower())

            with open('../data/users.json', 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=2, ensure_ascii=False)

            print(
                f"✓ Created new user: {pseudo_from_filename} (ID: {user_id}, emoji: 🐺)")

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

        print(
            f"✓ Added {pseudo_from_filename} to {added_count} games' todo list")

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

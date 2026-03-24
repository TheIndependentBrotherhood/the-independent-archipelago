# The Independent Archipelago

Your complete, centralized guide to **Archipelago games**. One site to rule them all! 🌴

## What is this?

This is a simple, static website that aggregates information about all Archipelago games in one place. No more jumping between different sites!

## Features

- 🔍 **Search** - Find games quickly by name, genre, or description
- 📱 **Responsive** - Works on desktop, tablet, and mobile
- ⚡ **Fast** - Pure HTML, CSS, and JavaScript (no build tools needed)
- 📝 **Easy to update** - Just edit `data/games.json` to add or modify games

## Project Structure

```
.
├── index.html           # Main page
├── data/
│   └── games.json      # Game database
├── css/
│   └── style.css       # Styling
├── js/
│   └── app.js          # Game loading and search logic
└── README.md           # This file
```

## How to Add Games

Edit `data/games.json` and add a new game object:

```json
{
  "id": "game-id",
  "name": "Game Name",
  "url": "https://archipelago.gg/games/...",
  "description": "Game description",
  "difficulty": "Easy/Medium/Hard/Very Hard",
  "players": "1/Multiplayer",
  "genre": "Action RPG/Adventure/etc",
  "status": "Active"
}
```

## Deployment

This site is hosted on **GitHub Pages**. Every push to `main` automatically deploys the site.

### Setup (one time):

1. Go to repository Settings → Pages
2. Set source to "Deploy from a branch"
3. Select `main` branch and `/ (root)` folder
4. Your site will be live at `https://theindependentbrotherhood.github.io/the-independent-archipelago/`

## Development

No build process needed! Just edit files and push to `main`.

To test locally, you can use Python's simple HTTP server:

```bash
python -m http.server 8000
```

Then visit http://localhost:8000

## Contributing

Want to add a game? Edit `data/games.json` and submit a pull request!

## License

Open source and free to use.

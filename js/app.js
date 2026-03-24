// Load games data and render
async function loadGames() {
  try {
    const response = await fetch('data/games.json');
    const data = await response.json();
    renderGames(data.games);
    updateLastUpdated();
  } catch (error) {
    console.error('Error loading games:', error);
    document.getElementById('gamesContainer').innerHTML = 
      '<div class="no-results">Error loading games. Please try again later.</div>';
  }
}

// Render games to the DOM
function renderGames(games) {
  const container = document.getElementById('gamesContainer');
  
  if (games.length === 0) {
    container.innerHTML = '<div class="no-results">No games found.</div>';
    return;
  }

  container.innerHTML = games.map(game => createGameCard(game)).join('');
}

// Create a game card HTML
function createGameCard(game) {
  const difficultyClass = `difficulty-${game.difficulty.toLowerCase().replace(/\s+/g, '-')}`;
  
  return `
    <div class="game-card">
      <h3>${game.name}</h3>
      <p>${game.description}</p>
      <div class="game-meta">
        <span class="tag ${difficultyClass}">${game.difficulty}</span>
        <span class="tag">${game.genre}</span>
        <span class="tag">${game.players}</span>
      </div>
      <a href="${game.url}" target="_blank" class="game-link">View Details</a>
    </div>
  `;
}

// Search functionality
document.getElementById('searchInput').addEventListener('input', async (e) => {
  const query = e.target.value.toLowerCase();
  
  const response = await fetch('data/games.json');
  const data = await response.json();
  
  const filtered = data.games.filter(game => 
    game.name.toLowerCase().includes(query) ||
    game.description.toLowerCase().includes(query) ||
    game.genre.toLowerCase().includes(query)
  );
  
  renderGames(filtered);
});

// Update last updated timestamp
function updateLastUpdated() {
  const now = new Date();
  const formatted = now.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
  document.getElementById('lastUpdated').textContent = formatted;
}

// Load games when page loads
document.addEventListener('DOMContentLoaded', loadGames);

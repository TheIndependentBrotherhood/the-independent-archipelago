// Load games data and render
let usersMap = {};

async function loadGames() {
  try {
    // Load users first
    const usersResponse = await fetch('data/users.json');
    const usersData = await usersResponse.json();
    usersMap = {};
    usersData.users.forEach(user => {
      usersMap[user.id] = user;
    });

    // Load games
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
  const allCompleted = game.completed.slice(0, 3);
  const allTodo = game.todo.slice(0, 3);
  const completedExtra = Math.max(0, game.completed.length - 3);
  const todoExtra = Math.max(0, game.todo.length - 3);

  const completedBadges = allCompleted.map(userId => {
    const user = usersMap[userId];
    return `<span class="user-emoji" title="${user?.pseudo || userId}">${user?.emoji || '👤'}</span>`;
  }).join('');

  const todoBadges = allTodo.map(userId => {
    const user = usersMap[userId];
    return `<span class="user-emoji" title="${user?.pseudo || userId}">${user?.emoji || '👤'}</span>`;
  }).join('');

  return `
    <div class="game-card">
      <h3>${game.name}</h3>
      <p>${game.description}</p>
      <div class="game-meta">
        <div class="status-line">
          ${game.todo.length > 0 ? `<div class="user-bubble todo-bubble" onclick="showUsers('todo-${game.id}')">
            <i class="fas fa-list-check"></i>
            <div class="avatars-inline">${todoBadges}${todoExtra > 0 ? `<span class="extra-count">+${todoExtra}</span>` : ''}</div>
          </div>` : ''}
          
          ${game.completed.length > 0 ? `<div class="user-bubble completed-bubble" onclick="showUsers('completed-${game.id}')">
            <i class="fas fa-check-circle"></i>
            <div class="avatars-inline">${completedBadges}${completedExtra > 0 ? `<span class="extra-count">+${completedExtra}</span>` : ''}</div>
          </div>` : ''}
        </div>
      </div>
      <a href="${game.url}" target="_blank" class="game-link">View Details</a>
      
      ${game.todo.length > 0 ? `<div id="todo-${game.id}" class="modal hidden">
        <div class="modal-content">
          <h4><i class="fas fa-list-check"></i> To Do</h4>
          <div class="users-list">
            ${game.todo.map(userId => {
              const user = usersMap[userId];
              return `<div class="user-item">${user?.emoji || '👤'} ${user?.pseudo || userId}</div>`;
            }).join('')}
          </div>
        </div>
      </div>` : ''}
      
      ${game.completed.length > 0 ? `<div id="completed-${game.id}" class="modal hidden">
        <div class="modal-content">
          <h4><i class="fas fa-check-circle"></i> Completed</h4>
          <div class="users-list">
            ${game.completed.map(userId => {
              const user = usersMap[userId];
              return `<div class="user-item">${user?.emoji || '👤'} ${user?.pseudo || userId}</div>`;
            }).join('')}
          </div>
        </div>
      </div>` : ''}
    </div>
  `;
}

// Show users modal
function showUsers(modalId) {
  const modal = document.getElementById(modalId);
  if (modal.classList.contains('hidden')) {
    modal.classList.remove('hidden');
  } else {
    modal.classList.add('hidden');
  }
}

// Search functionality
document.getElementById('searchInput').addEventListener('input', async (e) => {
  const query = e.target.value.toLowerCase();
  
  const response = await fetch('data/games.json');
  const data = await response.json();
  
  const filtered = data.games.filter(game => 
    game.name.toLowerCase().includes(query) ||
    game.description.toLowerCase().includes(query)
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

// Close modals when clicking outside
document.addEventListener('click', (e) => {
  if (!e.target.closest('.user-group') && !e.target.closest('.modal')) {
    document.querySelectorAll('.modal').forEach(modal => {
      modal.classList.add('hidden');
    });
  }
});

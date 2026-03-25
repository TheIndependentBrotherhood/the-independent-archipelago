// Load games data and render
let usersMap = {};
let allGames = [];
let selectedTodoFilter = null;
let selectedInProgressFilter = null;
let selectedCompletedFilter = null;

async function loadGames() {
  try {
    // Load users first
    const usersResponse = await fetch("data/users.json");
    const usersData = await usersResponse.json();
    usersMap = {};
    usersData.users.forEach((user) => {
      usersMap[user.id] = user;
    });

    // Load games
    const response = await fetch("data/games.json");
    const data = await response.json();
    allGames = data.games;

    // Initialize filters
    initializeFilters(data.games);

    renderGames(data.games);
    updateLastUpdated();
  } catch (error) {
    console.error("Error loading games:", error);
    document.getElementById("gamesContainer").innerHTML =
      '<div class="no-results">Error loading games. Please try again later.</div>';
  }
}

function initializeFilters(games) {
  // Get all unique users in todo, inProgress and completed
  const todoUsers = new Set();
  const inProgressUsers = new Set();
  const completedUsers = new Set();

  games.forEach((game) => {
    game.todo.forEach((userId) => todoUsers.add(userId));
    game.inProgress.forEach((userId) => inProgressUsers.add(userId));
    game.completed.forEach((userId) => completedUsers.add(userId));
  });

  // Create filter buttons for todo
  const todoFilterContainer = document.getElementById("todoUserFilter");
  todoFilterContainer.innerHTML = "";
  todoUsers.forEach((userId) => {
    const user = usersMap[userId];
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = `${user.emoji} ${user.pseudo}`;
    btn.addEventListener("click", () => toggleTodoFilter(userId, btn));
    todoFilterContainer.appendChild(btn);
  });

  // Create filter buttons for inProgress
  const inProgressFilterContainer = document.getElementById(
    "inProgressUserFilter",
  );
  inProgressFilterContainer.innerHTML = "";
  inProgressUsers.forEach((userId) => {
    const user = usersMap[userId];
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = `${user.emoji} ${user.pseudo}`;
    btn.addEventListener("click", () => toggleInProgressFilter(userId, btn));
    inProgressFilterContainer.appendChild(btn);
  });

  // Create filter buttons for completed
  const completedFilterContainer = document.getElementById(
    "completedUserFilter",
  );
  completedFilterContainer.innerHTML = "";
  completedUsers.forEach((userId) => {
    const user = usersMap[userId];
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = `${user.emoji} ${user.pseudo}`;
    btn.addEventListener("click", () => toggleCompletedFilter(userId, btn));
    completedFilterContainer.appendChild(btn);
  });
}

function toggleTodoFilter(userId, btn) {
  if (selectedTodoFilter === userId) {
    selectedTodoFilter = null;
    btn.classList.remove("active");
  } else {
    document
      .querySelectorAll("#todoUserFilter .filter-btn.active")
      .forEach((b) => b.classList.remove("active"));
    selectedTodoFilter = userId;
    btn.classList.add("active");
  }
  applyFilters();
}

function toggleInProgressFilter(userId, btn) {
  if (selectedInProgressFilter === userId) {
    selectedInProgressFilter = null;
    btn.classList.remove("active");
  } else {
    document
      .querySelectorAll("#inProgressUserFilter .filter-btn.active")
      .forEach((b) => b.classList.remove("active"));
    selectedInProgressFilter = userId;
    btn.classList.add("active");
  }
  applyFilters();
}

function toggleCompletedFilter(userId, btn) {
  if (selectedCompletedFilter === userId) {
    selectedCompletedFilter = null;
    btn.classList.remove("active");
  } else {
    document
      .querySelectorAll("#completedUserFilter .filter-btn.active")
      .forEach((b) => b.classList.remove("active"));
    selectedCompletedFilter = userId;
    btn.classList.add("active");
  }
  applyFilters();
}

function applyFilters() {
  let filtered = allGames;

  if (selectedTodoFilter) {
    filtered = filtered.filter((game) =>
      game.todo.includes(selectedTodoFilter),
    );
  }

  if (selectedInProgressFilter) {
    filtered = filtered.filter((game) =>
      game.inProgress.includes(selectedInProgressFilter),
    );
  }

  if (selectedCompletedFilter) {
    filtered = filtered.filter((game) =>
      game.completed.includes(selectedCompletedFilter),
    );
  }

  renderGames(filtered);
}

// Render games to the DOM
function renderGames(games) {
  const container = document.getElementById("gamesContainer");

  if (games.length === 0) {
    container.innerHTML = '<div class="no-results">No games found.</div>';
    return;
  }

  container.innerHTML = games.map((game) => createGameCard(game)).join("");
}

// Create a game card HTML
function createGameCard(game) {
  const allCompleted = game.completed.slice(0, 3);
  const allInProgress = game.inProgress.slice(0, 3);
  const allTodo = game.todo.slice(0, 3);
  const completedExtra = Math.max(0, game.completed.length - 3);
  const inProgressExtra = Math.max(0, game.inProgress.length - 3);
  const todoExtra = Math.max(0, game.todo.length - 3);

  const completedBadges = allCompleted
    .map((userId) => {
      const user = usersMap[userId];
      return `<span class="user-emoji" title="${user?.pseudo || userId}">${user?.emoji || "👤"}</span>`;
    })
    .join("");

  const inProgressBadges = allInProgress
    .map((userId) => {
      const user = usersMap[userId];
      return `<span class="user-emoji" title="${user?.pseudo || userId}">${user?.emoji || "👤"}</span>`;
    })
    .join("");

  const todoBadges = allTodo
    .map((userId) => {
      const user = usersMap[userId];
      return `<span class="user-emoji" title="${user?.pseudo || userId}">${user?.emoji || "👤"}</span>`;
    })
    .join("");

  return `
    <div class="game-card">
      <h3>${game.name}</h3>
      <p>${game.description}</p>
      <div class="game-meta">
        <div class="status-line">
          <div class="user-group-todo status-left">
            <div class="user-bubble todo-bubble ${game.todo.length === 0 ? "empty" : ""}" ${game.todo.length > 0 ? `onclick="showUsers('todo-${game.id}')"` : ""}>
              <i class="fas fa-list-check"></i>
              ${game.todo.length > 0 ? `<div class="avatars-inline">${todoBadges}${todoExtra > 0 ? `<span class="extra-count">+${todoExtra}</span>` : ""}</div>` : ""}
            </div>
          </div>
          
          <div class="user-group-inprogress status-center">
            <div class="user-bubble inprogress-bubble ${game.inProgress.length === 0 ? "empty" : ""}" ${game.inProgress.length > 0 ? `onclick="showUsers('inProgress-${game.id}')"` : ""}>
              <i class="fas fa-play-circle"></i>
              ${game.inProgress.length > 0 ? `<div class="avatars-inline">${inProgressBadges}${inProgressExtra > 0 ? `<span class="extra-count">+${inProgressExtra}</span>` : ""}</div>` : ""}
            </div>
          </div>
          
          <div class="user-group-completed status-right">
            <div class="user-bubble completed-bubble ${game.completed.length === 0 ? "empty" : ""}" ${game.completed.length > 0 ? `onclick="showUsers('completed-${game.id}')"` : ""}>
              <i class="fas fa-check-circle"></i>
              ${game.completed.length > 0 ? `<div class="avatars-inline">${completedBadges}${completedExtra > 0 ? `<span class="extra-count">+${completedExtra}</span>` : ""}</div>` : ""}
            </div>
          </div>
        </div>
      </div>
      <div class="action-buttons">
        ${
          game.url
            ? `<a href="${game.url}" target="_blank" class="btn-icon" title="View on Archipelago.gg">
          <i class="fas fa-globe"></i>
        </a>`
            : ""
        }
        ${
          game.discordUrl
            ? `<a href="${game.discordUrl}" target="_blank" class="btn-icon" title="Go to Discord channel">
          <i class="fab fa-discord"></i>
        </a>`
            : ""
        }
        ${
          game.githubUrl
            ? `<a href="${game.githubUrl}" target="_blank" class="btn-icon" title="View on GitHub">
          <i class="fab fa-github"></i>
        </a>`
            : ""
        }
      </div>
      
      ${
        game.todo.length > 0
          ? `<div id="todo-${game.id}" class="modal hidden">
        <div class="modal-content">
          <h4><i class="fas fa-list-check"></i> To Do</h4>
          <div class="users-list">
            ${game.todo
              .map((userId) => {
                const user = usersMap[userId];
                return `<div class="user-item">${user?.emoji || "👤"} ${user?.pseudo || userId}</div>`;
              })
              .join("")}
          </div>
        </div>
      </div>`
          : ""
      }
      
      ${
        game.inProgress.length > 0
          ? `<div id="inProgress-${game.id}" class="modal hidden">
        <div class="modal-content">
          <h4><i class="fas fa-play-circle"></i> In Progress</h4>
          <div class="users-list">
            ${game.inProgress
              .map((userId) => {
                const user = usersMap[userId];
                return `<div class="user-item">${user?.emoji || "👤"} ${user?.pseudo || userId}</div>`;
              })
              .join("")}
          </div>
        </div>
      </div>`
          : ""
      }
      
      ${
        game.completed.length > 0
          ? `<div id="completed-${game.id}" class="modal hidden">
        <div class="modal-content">
          <h4><i class="fas fa-check-circle"></i> Completed</h4>
          <div class="users-list">
            ${game.completed
              .map((userId) => {
                const user = usersMap[userId];
                return `<div class="user-item">${user?.emoji || "👤"} ${user?.pseudo || userId}</div>`;
              })
              .join("")}
          </div>
        </div>
      </div>`
          : ""
      }
    </div>
  `;
}

// Show users modal
function showUsers(modalId) {
  const modal = document.getElementById(modalId);
  if (modal.classList.contains("hidden")) {
    modal.classList.remove("hidden");
  } else {
    modal.classList.add("hidden");
  }
}

// Search functionality
document.getElementById("searchInput").addEventListener("input", async (e) => {
  const query = e.target.value.toLowerCase();

  let filtered = allGames;

  if (query) {
    filtered = filtered.filter(
      (game) =>
        game.name.toLowerCase().includes(query) ||
        game.description.toLowerCase().includes(query),
    );
  }

  if (selectedTodoFilter) {
    filtered = filtered.filter((game) =>
      game.todo.includes(selectedTodoFilter),
    );
  }

  if (selectedInProgressFilter) {
    filtered = filtered.filter((game) =>
      game.inProgress.includes(selectedInProgressFilter),
    );
  }

  if (selectedCompletedFilter) {
    filtered = filtered.filter((game) =>
      game.completed.includes(selectedCompletedFilter),
    );
  }

  renderGames(filtered);
});

// Update last updated timestamp
function updateLastUpdated() {
  const now = new Date();
  const formatted = now.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  document.getElementById("lastUpdated").textContent = formatted;
}

// Load games when page loads
document.addEventListener("DOMContentLoaded", loadGames);

// Close modals when clicking outside
document.addEventListener("click", (e) => {
  if (!e.target.closest(".user-group") && !e.target.closest(".modal")) {
    document.querySelectorAll(".modal").forEach((modal) => {
      modal.classList.add("hidden");
    });
  }
});

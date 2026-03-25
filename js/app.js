// Load games data and render
let usersMap = {};
let allGames = [];
let selectedTodoFilters = new Set();
let selectedInProgressFilters = new Set();
let selectedCompletedFilters = new Set();

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
  createFilterGroup(
    "Todo",
    "todoUserFilter",
    todoUsers,
    toggleTodoFilter,
    clearTodoFilters,
  );

  // Create filter buttons for inProgress
  createFilterGroup(
    "In Progress",
    "inProgressUserFilter",
    inProgressUsers,
    toggleInProgressFilter,
    clearInProgressFilters,
  );

  // Create filter buttons for completed
  createFilterGroup(
    "Completed",
    "completedUserFilter",
    completedUsers,
    toggleCompletedFilter,
    clearCompletedFilters,
  );
}

function createFilterGroup(
  title,
  containerId,
  users,
  toggleFunction,
  clearFunction,
) {
  const filterGroup = document.querySelector(`#${containerId}`).parentElement;

  // Update title with clear button
  const titleElement = filterGroup.querySelector("h3");
  titleElement.innerHTML = `${title} <button class="clear-filter-btn" title="Clear filter"><i class="fas fa-times"></i></button>`;
  titleElement
    .querySelector(".clear-filter-btn")
    .addEventListener("click", clearFunction);

  // Create filter buttons
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  users.forEach((userId) => {
    const user = usersMap[userId];
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = `${user.emoji} ${user.pseudo}`;
    btn.addEventListener("click", () => toggleFunction(userId, btn));
    container.appendChild(btn);
  });
}

function toggleTodoFilter(userId, btn) {
  if (selectedTodoFilters.has(userId)) {
    selectedTodoFilters.delete(userId);
    btn.classList.remove("active");
  } else {
    selectedTodoFilters.add(userId);
    btn.classList.add("active");
  }
  applyFilters();
}

function clearTodoFilters() {
  selectedTodoFilters.clear();
  document
    .querySelectorAll("#todoUserFilter .filter-btn.active")
    .forEach((b) => b.classList.remove("active"));
  applyFilters();
}

function toggleInProgressFilter(userId, btn) {
  if (selectedInProgressFilters.has(userId)) {
    selectedInProgressFilters.delete(userId);
    btn.classList.remove("active");
  } else {
    selectedInProgressFilters.add(userId);
    btn.classList.add("active");
  }
  applyFilters();
}

function clearInProgressFilters() {
  selectedInProgressFilters.clear();
  document
    .querySelectorAll("#inProgressUserFilter .filter-btn.active")
    .forEach((b) => b.classList.remove("active"));
  applyFilters();
}

function toggleCompletedFilter(userId, btn) {
  if (selectedCompletedFilters.has(userId)) {
    selectedCompletedFilters.delete(userId);
    btn.classList.remove("active");
  } else {
    selectedCompletedFilters.add(userId);
    btn.classList.add("active");
  }
  applyFilters();
}

function clearCompletedFilters() {
  selectedCompletedFilters.clear();
  document
    .querySelectorAll("#completedUserFilter .filter-btn.active")
    .forEach((b) => b.classList.remove("active"));
  applyFilters();
}

function applyFilters() {
  let filtered = allGames;

  // Apply status filters with OR logic between categories
  if (
    selectedTodoFilters.size > 0 ||
    selectedInProgressFilters.size > 0 ||
    selectedCompletedFilters.size > 0
  ) {
    filtered = filtered.filter((game) => {
      const matchesTodo =
        selectedTodoFilters.size === 0 ||
        game.todo.some((userId) => selectedTodoFilters.has(userId));
      const matchesInProgress =
        selectedInProgressFilters.size === 0 ||
        game.inProgress.some((userId) => selectedInProgressFilters.has(userId));
      const matchesCompleted =
        selectedCompletedFilters.size === 0 ||
        game.completed.some((userId) => selectedCompletedFilters.has(userId));
      return matchesTodo || matchesInProgress || matchesCompleted;
    });
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

  // Apply status filters with OR logic between categories
  if (
    selectedTodoFilter ||
    selectedInProgressFilter ||
    selectedCompletedFilter
  ) {
    filtered = filtered.filter((game) => {
      const matchesTodo =
        !selectedTodoFilter || game.todo.includes(selectedTodoFilter);
      const matchesInProgress =
        !selectedInProgressFilter ||
        game.inProgress.includes(selectedInProgressFilter);
      const matchesCompleted =
        !selectedCompletedFilter ||
        game.completed.includes(selectedCompletedFilter);
      return matchesTodo || matchesInProgress || matchesCompleted;
    });
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

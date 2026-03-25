// Load games data and render
let usersMap = {};
let allGames = [];
let selectedTodoFilters = new Set();
let selectedInProgressFilters = new Set();
let selectedCompletedFilters = new Set();
let selectedPlatformFilters = new Set();

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

    // Initialize alphabet navigation
    initializeAlphabetNav(data.games);

    renderGames(data.games);
    updateLastUpdated();
  } catch (error) {
    console.error("Error loading games:", error);
    document.getElementById("gamesContainer").innerHTML =
      '<div class="no-results">Error loading games. Please try again later.</div>';
  }
}

function initializeFilters(games) {
  // Get all unique platforms
  const platforms = new Set();
  games.forEach((game) => {
    if (game.platform) platforms.add(game.platform);
  });

  // Create filter buttons for platforms
  createPlatformFilterGroup(
    "Platform",
    "platformFilter",
    Array.from(platforms).sort(),
    togglePlatformFilter,
    clearPlatformFilters,
  );

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

function createPlatformFilterGroup(
  title,
  containerId,
  platforms,
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

  platforms.forEach((platform) => {
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = platform;
    btn.addEventListener("click", () => toggleFunction(platform, btn));
    container.appendChild(btn);
  });
}

function togglePlatformFilter(platform, btn) {
  if (selectedPlatformFilters.has(platform)) {
    selectedPlatformFilters.delete(platform);
    btn.classList.remove("active");
  } else {
    selectedPlatformFilters.add(platform);
    btn.classList.add("active");
  }
  applyFilters();
}

function clearPlatformFilters() {
  selectedPlatformFilters.clear();
  document
    .querySelectorAll("#platformFilter .filter-btn.active")
    .forEach((b) => b.classList.remove("active"));
  applyFilters();
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

  // Apply platform filter
  if (selectedPlatformFilters.size > 0) {
    filtered = filtered.filter((game) =>
      selectedPlatformFilters.has(game.platform),
    );
  }

  // Apply status filters with OR logic between categories
  if (
    selectedTodoFilters.size > 0 ||
    selectedInProgressFilters.size > 0 ||
    selectedCompletedFilters.size > 0
  ) {
    filtered = filtered.filter((game) => {
      let hasMatch = false;

      // Check each category that has filters selected
      if (selectedTodoFilters.size > 0) {
        hasMatch =
          hasMatch ||
          game.todo.some((userId) => selectedTodoFilters.has(userId));
      }

      if (selectedInProgressFilters.size > 0) {
        hasMatch =
          hasMatch ||
          game.inProgress.some((userId) =>
            selectedInProgressFilters.has(userId),
          );
      }

      if (selectedCompletedFilters.size > 0) {
        hasMatch =
          hasMatch ||
          game.completed.some((userId) => selectedCompletedFilters.has(userId));
      }

      return hasMatch;
    });
  }

  renderGames(filtered);
}

// Render games to the DOM
function renderGames(games) {
  const container = document.getElementById("gamesContainer");
  const resultsCount = document.getElementById("resultsCount");

  // Update results count
  if (games.length === 0) {
    resultsCount.textContent = "No games found";
    container.innerHTML = '<div class="no-results">No games found.</div>';
    return;
  }

  resultsCount.textContent = `${games.length} game${games.length !== 1 ? "s" : ""} found`;
  container.innerHTML = games.map((game) => createGameCard(game)).join("");

  // Validate Twitch images after rendering
  validateTwitchImages();
}

// Initialize alphabet navigation
function initializeAlphabetNav(games) {
  const alphabetContainer = document.getElementById("alphabetLetters");
  alphabetContainer.innerHTML = "";

  // Create buttons for each letter
  const letters = [
    "#",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
  ];

  letters.forEach((letter) => {
    const btn = document.createElement("button");
    btn.className = "alphabet-btn";
    btn.textContent = letter;
    btn.addEventListener("click", () => scrollToLetter(letter, games));
    alphabetContainer.appendChild(btn);
  });
}

// Scroll to first game starting with letter
function scrollToLetter(letter, games) {
  // Get all visible game cards in the DOM
  const visibleCards = Array.from(document.querySelectorAll(".game-card"));

  if (visibleCards.length === 0) {
    return; // No cards visible
  }

  let targetCard;

  if (letter === "#") {
    // Find first card starting with a number
    targetCard = visibleCards.find((card) => {
      const title = card.querySelector("h3")?.textContent;
      return title && /^\d/.test(title);
    });
  } else {
    // Find first card starting with the letter
    targetCard = visibleCards.find((card) => {
      const title = card.querySelector("h3")?.textContent;
      return title && title.toUpperCase().startsWith(letter);
    });
  }

  if (targetCard) {
    targetCard.scrollIntoView({ behavior: "smooth", block: "start" });
  }
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

  const twitchId = game.twitchId;
  const backgroundStyle = twitchId
    ? `style="background-image: url('https://static-cdn.jtvnw.net/ttv-boxart/${twitchId}-144x192.jpg');"`
    : "";
  const twitchClass = twitchId ? "has-twitch-image" : "";

  // Generate unique ID for this card to handle image loading
  const cardId = `card-${game.id}`;

  return `
    <div class="game-card ${twitchClass}" id="${cardId}" ${backgroundStyle}>
      <h3>${game.name}</h3>
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

// Validate Twitch images and fallback if they fail to load
function validateTwitchImages() {
  document.querySelectorAll(".game-card.has-twitch-image").forEach((card) => {
    const twitchId = card.style.backgroundImage.match(/\/(\d+)/)?.[1];
    if (twitchId) {
      // Try without _IGDB first
      const urlWithoutIGDB = `https://static-cdn.jtvnw.net/ttv-boxart/${twitchId}-144x192.jpg`;
      const urlWithIGDB = `https://static-cdn.jtvnw.net/ttv-boxart/${twitchId}_IGDB-144x192.jpg`;

      tryLoadImage(card, urlWithoutIGDB, urlWithIGDB, twitchId);
    }
  });
}

// Try to load image with fallback chain
async function tryLoadImage(card, urlWithoutIGDB, urlWithIGDB, twitchId) {
  // Check first URL
  if (await isValidImageUrl(urlWithoutIGDB)) {
    card.style.backgroundImage = `url('${urlWithoutIGDB}')`;
    return;
  }

  // Check second URL with _IGDB
  if (await isValidImageUrl(urlWithIGDB)) {
    card.style.backgroundImage = `url('${urlWithIGDB}')`;
    return;
  }

  // Both failed, show fallback (remove class to show Archipelago logo)
  const gameName = card.querySelector("h3")?.textContent || "Unknown";
  console.warn(
    `Failed to load Twitch image for "${gameName}" (Twitch ID: ${twitchId}). Both URLs failed: ${urlWithoutIGDB} and ${urlWithIGDB}`,
  );
  card.classList.remove("has-twitch-image");
  card.style.backgroundImage = "none";
}

// Check if an image URL is valid (no 302 redirect to 404)
async function isValidImageUrl(url) {
  try {
    const response = await fetch(url, { method: "HEAD" });
    // Check if it's a valid response and not redirected to 404
    if (response.ok && !response.url.includes("404_boxart")) {
      return true;
    }
    return false;
  } catch (error) {
    return false;
  }
}

// Search functionality
document.getElementById("searchInput").addEventListener("input", (e) => {
  const query = e.target.value.toLowerCase();

  let filtered = allGames;

  // Apply search filter first
  if (query) {
    filtered = filtered.filter(
      (game) =>
        game.name.toLowerCase().includes(query) ||
        game.description.toLowerCase().includes(query),
    );
  }

  // Apply platform filter
  if (selectedPlatformFilters.size > 0) {
    filtered = filtered.filter((game) =>
      selectedPlatformFilters.has(game.platform),
    );
  }

  // Apply status filters with OR logic between categories
  if (
    selectedTodoFilters.size > 0 ||
    selectedInProgressFilters.size > 0 ||
    selectedCompletedFilters.size > 0
  ) {
    filtered = filtered.filter((game) => {
      let hasMatch = false;

      // Check each category that has filters selected
      if (selectedTodoFilters.size > 0) {
        hasMatch =
          hasMatch ||
          game.todo.some((userId) => selectedTodoFilters.has(userId));
      }

      if (selectedInProgressFilters.size > 0) {
        hasMatch =
          hasMatch ||
          game.inProgress.some((userId) =>
            selectedInProgressFilters.has(userId),
          );
      }

      if (selectedCompletedFilters.size > 0) {
        hasMatch =
          hasMatch ||
          game.completed.some((userId) => selectedCompletedFilters.has(userId));
      }

      return hasMatch;
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

// Scroll to top button
const scrollTopBtn = document.getElementById("scrollTopBtn");
if (scrollTopBtn) {
  scrollTopBtn.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
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

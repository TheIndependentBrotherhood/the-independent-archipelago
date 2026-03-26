// Dark mode management
function initDarkMode() {
  // Check if user has a stored preference
  const storedTheme = localStorage.getItem("theme");
  const prefersDark = globalThis.matchMedia(
    "(prefers-color-scheme: dark)",
  ).matches;

  // Set theme based on stored preference or system preference
  if (storedTheme === "dark" || (!storedTheme && prefersDark)) {
    document.documentElement.classList.add("dark-mode");
    updateDarkModeIcon();
  }

  // Listen for system theme changes
  globalThis
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", (e) => {
      if (!localStorage.getItem("theme")) {
        if (e.matches) {
          document.documentElement.classList.add("dark-mode");
        } else {
          document.documentElement.classList.remove("dark-mode");
        }
        updateDarkModeIcon();
      }
    });
}

function toggleDarkMode() {
  document.documentElement.classList.toggle("dark-mode");
  const isDarkMode = document.documentElement.classList.contains("dark-mode");
  localStorage.setItem("theme", isDarkMode ? "dark" : "light");
  updateDarkModeIcon();
}

function updateDarkModeIcon() {
  const button = document.getElementById("darkModeToggle");
  const isDarkMode = document.documentElement.classList.contains("dark-mode");
  if (button) {
    const icon = button.querySelector("i");
    if (isDarkMode) {
      icon.classList.remove("fa-moon");
      icon.classList.add("fa-sun");
      button.title = "Switch to light mode";
    } else {
      icon.classList.remove("fa-sun");
      icon.classList.add("fa-moon");
      button.title = "Switch to dark mode";
    }
  }
}

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
  createTodoFilterGroup(
    "To Do List",
    "todoUserFilter",
    todoUsers,
    toggleTodoFilter,
    clearTodoFilters,
    allGames,
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

function createTodoFilterGroup(
  title,
  containerId,
  users,
  toggleFunction,
  clearFunction,
  games,
) {
  const filterGroup = document.querySelector(`#${containerId}`).parentElement;

  // Update title with clear button and spin button
  const titleElement = filterGroup.querySelector("h3");
  titleElement.textContent = title;

  const buttonsContainer = document.createElement("div");
  buttonsContainer.className = "title-buttons-container";

  const spinBtn = document.createElement("button");
  spinBtn.className = "spin-btn-title";
  spinBtn.title = "Spin the wheel";
  spinBtn.innerHTML = '<i class="fas fa-dharmachakra"></i> Spin';
  spinBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    openWheelSelector(Array.from(users), games);
  });

  const clearBtn = document.createElement("button");
  clearBtn.className = "clear-filter-btn";
  clearBtn.title = "Clear filter";
  clearBtn.innerHTML = '<i class="fas fa-times"></i>';
  clearBtn.addEventListener("click", clearFunction);

  buttonsContainer.appendChild(spinBtn);
  buttonsContainer.appendChild(clearBtn);
  titleElement.appendChild(buttonsContainer);

  // Create filter buttons without spin button
  const container = document.getElementById(containerId);
  container.innerHTML = "";

  // Add filter buttons
  const filtersContainer = document.createElement("div");
  filtersContainer.className = "todo-filters-container";

  users.forEach((userId) => {
    const user = usersMap[userId];
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = `${user.emoji} ${user.pseudo}`;
    btn.addEventListener("click", () => toggleFunction(userId, btn));
    filtersContainer.appendChild(btn);
  });

  container.appendChild(filtersContainer);
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
  validateTwitchImages(".game-card.has-twitch-image");
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

// Open wheel selector to choose user
function openWheelSelector(userIds, games) {
  const selector = document.createElement("div");
  selector.id = "wheel-selector";
  selector.className = "wheel-selector";
  selector.innerHTML = `
    <div class="wheel-selector-content">
      <button class="wheel-close-btn">
        <i class="fas fa-times"></i>
      </button>
      <h3>Choose a Player</h3>
      <div class="selector-buttons">
        ${userIds
          .map((userId) => {
            const user = usersMap[userId];
            const userGames = games.filter((g) => g.todo.includes(userId));
            const canSpin = userGames.length > 1;
            return `
              <button class="selector-btn ${!canSpin ? "disabled" : ""}" data-user-id="${userId}" ${!canSpin ? "disabled" : ""}>
                <span class="selector-emoji">${user.emoji}</span>
                <span class="selector-name">${user.pseudo}</span>
                <span class="selector-count">${userGames.length} game${userGames.length !== 1 ? "s" : ""}</span>
              </button>
            `;
          })
          .join("")}
      </div>
    </div>
  `;

  document.body.appendChild(selector);

  // Close button
  selector.querySelector(".wheel-close-btn").addEventListener("click", () => {
    selector.remove();
  });

  // Selector buttons
  selector.querySelectorAll(".selector-btn:not(.disabled)").forEach((btn) => {
    btn.addEventListener("click", () => {
      const userId = btn.getAttribute("data-user-id");
      selector.remove();
      spinWheelForUser(userId, games);
    });
  });

  // Close when clicking outside
  selector.addEventListener("click", (e) => {
    if (e.target === selector) {
      selector.remove();
    }
  });
}

// Spin the wheel for a user's todo list
function spinWheelForUser(userId, games) {
  // Get all games for this user's todo list
  const userTodoGames = games.filter((game) => game.todo.includes(userId));

  if (userTodoGames.length === 0) {
    alert("No games in todo list for this user!");
    return;
  }

  const user = usersMap[userId];

  // Close existing wheel popup if any
  const existingPopup = document.getElementById("wheel-popup");
  if (existingPopup) {
    existingPopup.remove();
  }

  // Create wheel popup
  const wheelPopup = document.createElement("div");
  wheelPopup.id = "wheel-popup";
  wheelPopup.className = "wheel-popup";
  wheelPopup.innerHTML = `
    <div class="wheel-popup-content">
      <button class="wheel-close-btn">
        <i class="fas fa-times"></i>
      </button>
      <h3>${user.emoji} ${user.pseudo}'s Wheel of Fortune</h3>
      <div class="wheel-spinner-container">
        <canvas id="wheelCanvas" class="wheel-canvas"></canvas>
        <div class="wheel-pointer">▼</div>
        <button class="spin-btn-icon" id="spinBtnLarge" title="Spin the wheel">
          <i class="fas fa-dharmachakra"></i>
        </button>
      </div>
      <div id="wheelResult" class="wheel-result hidden">
      </div>
    </div>
  `;

  document.body.appendChild(wheelPopup);

  // Draw wheel
  const canvas = document.getElementById("wheelCanvas");
  const ctx = canvas.getContext("2d");
  canvas.width = 450;
  canvas.height = 450;

  let currentRotation = 0;

  function drawWheel(rotation = 0) {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = canvas.width / 2 - 10;
    const segmentCount = userTodoGames.length;
    const segmentAngle = (Math.PI * 2) / segmentCount;

    const isDarkMode = document.documentElement.classList.contains("dark-mode");

    // Colors for segments - using badge colors (adjusted for dark mode)
    const colors = isDarkMode
      ? [
          "#3a3a1a", // todo-bg dark
          "#1a2a3a", // inprogress-bg dark
          "#1a3a1a", // completed-bg dark
          "#3a1a1a", // error-like
          "#2a1a3a", // purple-like
          "#1a3a3a", // teal-like
          "#3a2a1a", // orange-like
          "#3a3a1a", // yellow-like
          "#2a2a3a", // blue-like
          "#3a2a2a", // brown-like
          "#2a3a2a", // green-like
          "#3a3a2a", // gold-like
        ]
      : [
          "#fff3cd", // Yellow
          "#cfe2ff", // Blue
          "#d4edda", // Green
          "#f8d7da", // Red/Pink
          "#e7d4f5", // Violet
          "#d1ecf1", // Cyan
          "#ffe4c4", // Bisque/Orange
          "#f0e68c", // Khaki
          "#ffcccc", // Light Pink
          "#ccf0ff", // Light Blue
          "#e0ffe0", // Light Green
          "#fffacd", // Light Yellow
        ];

    const borderColor = isDarkMode ? "#666" : "#333";

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw segments
    userTodoGames.forEach((game, index) => {
      const startAngle = index * segmentAngle + rotation;
      const endAngle = (index + 1) * segmentAngle + rotation;

      // Draw segment
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, startAngle, endAngle);
      ctx.lineTo(centerX, centerY);
      ctx.fillStyle = colors[index % colors.length];
      ctx.fill();

      // Draw border
      ctx.strokeStyle = borderColor;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw game name
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(startAngle + segmentAngle / 2);

      // Create clipping region for text (stays within segment)
      ctx.beginPath();
      ctx.arc(0, 0, radius, -segmentAngle / 2, segmentAngle / 2);
      ctx.lineTo(0, 0);
      ctx.clip();

      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = "bold 14px sans-serif";

      const textRadius = radius * 0.65;
      const gameName = game.name.substring(0, 30);

      // Draw text with outline for better visibility
      ctx.strokeStyle = "rgba(255, 255, 255, 0.9)";
      ctx.lineWidth = 4;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.strokeText(gameName, textRadius, 0);

      // Draw text
      ctx.fillStyle = "#1a1a1a";
      ctx.fillText(gameName, textRadius, 0);

      ctx.restore();
    });

    // Draw center circle
    ctx.beginPath();
    ctx.arc(centerX, centerY, 25, 0, Math.PI * 2);
    ctx.fillStyle = "#1a472a";
    ctx.fill();
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw center icon
    ctx.fillStyle = "#fff";
    ctx.font = "bold 18px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("🎡", centerX, centerY);
  }

  // Initial draw
  drawWheel();

  // Add event listeners
  wheelPopup
    .querySelector(".wheel-close-btn")
    .addEventListener("click", closeWheelPopup);
  wheelPopup.querySelector("#spinBtnLarge").addEventListener("click", () => {
    spinAnimation(userId, userTodoGames, canvas, drawWheel, userTodoGames);
  });

  // Close popup when clicking outside
  wheelPopup.addEventListener("click", (e) => {
    if (e.target === wheelPopup) {
      closeWheelPopup();
    }
  });
}

function spinAnimation(userId, userTodoGames, canvas, drawWheel, games) {
  const result = document.getElementById("wheelResult");
  const spinBtn = document.getElementById("spinBtnLarge");

  // Hide result and disable button
  result.classList.add("hidden");
  spinBtn.disabled = true;
  spinBtn.style.opacity = "0.5";

  // Animation variables
  const animationDuration = 3000;
  const rotationsCount = 8; // Full rotations

  // Pre-select a random game to ensure consistency
  const selectedIndex = Math.floor(Math.random() * games.length);
  const selectedGame = games[selectedIndex];
  const segmentCount = games.length;
  const segmentAngle = (Math.PI * 2) / segmentCount;

  // Calculate the final rotation so the selected game lands at the pointer (top)
  // The pointer is at angle 3π/2 (top in canvas coords), so we need the selected segment's center there
  // Segment center is at: selectedIndex * segmentAngle + rotation + segmentAngle/2
  // So: selectedIndex * segmentAngle + rotation + segmentAngle/2 = 3π/2
  // Therefore: rotation = 3π/2 - segmentAngle * (selectedIndex + 0.5)
  const targetRotation = 3 * Math.PI / 2 - segmentAngle * (selectedIndex + 0.5);

  let currentRotation = 0;
  const startTime = Date.now();

  function animate() {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(elapsed / animationDuration, 1);

    // Ease out animation (cubic)
    const easeProgress = 1 - Math.pow(1 - progress, 3);
    const totalRotation = rotationsCount * Math.PI * 2 * easeProgress;
    // Add the target offset to position the selected segment at the pointer (top)
    currentRotation = (totalRotation + targetRotation) % (Math.PI * 2);

    drawWheel(currentRotation);

    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      // Animation complete - show the pre-selected game (already determined)
      // Show result
      const resultDiv = document.getElementById("wheelResult");
      const backgroundStyle = selectedGame.twitchId
        ? `style="background-image: url('https://static-cdn.jtvnw.net/ttv-boxart/${selectedGame.twitchId}-144x192.jpg')"`
        : "";
      const twitchClass = selectedGame.twitchId ? "has-twitch-image" : "";
      resultDiv.innerHTML = `
        <div class="result-game-card ${twitchClass}" ${backgroundStyle}>
          <h5><b>You got:</b> ${selectedGame.name}</h5>
          <div class="action-buttons">
        ${
          selectedGame.url
            ? `<a href="${selectedGame.url}" target="_blank" class="btn-icon" title="View on Archipelago.gg">
          <i class="fas fa-globe"></i>
        </a>`
            : ""
        }
        ${
          selectedGame.discordUrl
            ? `<a href="${selectedGame.discordUrl}" target="_blank" class="btn-icon" title="Go to Discord channel">
          <i class="fab fa-discord"></i>
        </a>`
            : ""
        }
        ${
          selectedGame.githubUrl
            ? `<a href="${selectedGame.githubUrl}" target="_blank" class="btn-icon" title="View on GitHub">
          <i class="fab fa-github"></i>
        </a>`
            : ""
        }
      </div>
        </div>
      `;
      result.classList.remove("hidden");

      // Validate Twitch images after rendering
      validateTwitchImages(".result-game-card.has-twitch-image");

      // Re-enable button
      spinBtn.disabled = false;
      spinBtn.style.opacity = "1";
    }
  }

  requestAnimationFrame(animate);
}

function closeWheelPopup() {
  const popup = document.getElementById("wheel-popup");
  if (popup) {
    popup.remove();
  }
}

// Show users modal
function showUsers(modalId) {
  // Close all other modals first
  document.querySelectorAll(".modal").forEach((modal) => {
    if (modal.id !== modalId) {
      modal.classList.add("hidden");
    }
  });

  // Toggle the target modal
  const modal = document.getElementById(modalId);
  if (modal.classList.contains("hidden")) {
    modal.classList.remove("hidden");
  } else {
    modal.classList.add("hidden");
  }
}

// Validate Twitch images and fallback if they fail to load
function validateTwitchImages(selector) {
  document.querySelectorAll(selector).forEach((card) => {
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
    globalThis.scrollTo({ top: 0, behavior: "smooth" });
  });
}

// Load games when page loads
document.addEventListener("DOMContentLoaded", () => {
  initDarkMode();

  // Set up dark mode toggle button
  const darkModeToggle = document.getElementById("darkModeToggle");
  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", toggleDarkMode);
  }

  loadGames();
});

// Close modals when clicking outside
document.addEventListener("click", (e) => {
  if (!e.target.closest(".user-bubble") && !e.target.closest(".modal")) {
    document.querySelectorAll(".modal").forEach((modal) => {
      modal.classList.add("hidden");
    });
  }
});

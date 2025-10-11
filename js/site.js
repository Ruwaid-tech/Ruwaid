const htmlEl = document.documentElement;
const themeToggle = document.getElementById("theme-toggle");
const menuToggle = document.querySelector(".menu-toggle");
const nav = document.querySelector(".nav");
const signInBtn = document.getElementById("sign-in-btn");
const signInModal = document.getElementById("sign-in-modal");
const signInEmail = document.getElementById("sign-in-email");
const toast = document.getElementById("toast");

const STORAGE_KEYS = {
  theme: "selfHavenTheme",
  email: "selfHavenEmail",
  journal: "selfHavenJournal",
  favorites: "selfHavenFavorites",
};

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("is-visible");
  setTimeout(() => toast.classList.remove("is-visible"), 2400);
}

function loadTheme() {
  const saved = localStorage.getItem(STORAGE_KEYS.theme);
  if (saved === "dark") {
    htmlEl.dataset.theme = "dark";
  }
}

function toggleTheme() {
  const next = htmlEl.dataset.theme === "dark" ? "light" : "dark";
  htmlEl.dataset.theme = next;
  localStorage.setItem(STORAGE_KEYS.theme, next);
  showToast(next === "dark" ? "Dark mode on" : "Light mode on");
}

function setupMenuToggle() {
  if (!menuToggle || !nav) return;
  menuToggle.setAttribute("aria-expanded", "false");
  menuToggle.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    menuToggle.setAttribute("aria-expanded", String(isOpen));
  });
  nav.querySelectorAll("a").forEach((link) =>
    link.addEventListener("click", () => {
      nav.classList.remove("is-open");
      menuToggle.setAttribute("aria-expanded", "false");
    })
  );
}

function setupSignIn() {
  if (!signInBtn || !signInModal || !signInEmail) return;
  const savedEmail = localStorage.getItem(STORAGE_KEYS.email) || "";
  if (savedEmail) {
    signInBtn.textContent = "Signed in";
  }

  signInBtn.addEventListener("click", () => {
    signInEmail.value = localStorage.getItem(STORAGE_KEYS.email) || "";
    signInModal.showModal();
  });

  signInModal.addEventListener("close", () => {
    if (signInModal.returnValue === "confirm") {
      const value = signInEmail.value.trim();
      if (value) {
        localStorage.setItem(STORAGE_KEYS.email, value);
        signInBtn.textContent = "Signed in";
        showToast("Email saved to this device");
      } else {
        localStorage.removeItem(STORAGE_KEYS.email);
        signInBtn.textContent = "Optional sign in";
        showToast("Email removed");
      }
    }
    signInEmail.value = "";
  });
}

function loadJournal() {
  const stored = localStorage.getItem(STORAGE_KEYS.journal);
  if (!stored) return {};
  try {
    return JSON.parse(stored);
  } catch (error) {
    console.error("Unable to parse journal store", error);
    return {};
  }
}

function saveJournal(journal) {
  localStorage.setItem(STORAGE_KEYS.journal, JSON.stringify(journal));
}

function setupJournalPrompts() {
  const areas = document.querySelectorAll("[data-journal-id]");
  if (!areas.length) return;
  const journal = loadJournal();
  areas.forEach((textarea) => {
    const id = textarea.dataset.journalId;
    if (journal[id]) {
      textarea.value = journal[id];
    }
    textarea.addEventListener("input", () => {
      journal[id] = textarea.value;
      saveJournal(journal);
    });
  });
}

function loadFavorites() {
  const stored = localStorage.getItem(STORAGE_KEYS.favorites);
  if (!stored) return [];
  try {
    return JSON.parse(stored);
  } catch (error) {
    console.error("Unable to parse favorites", error);
    return [];
  }
}

function saveFavorites(list) {
  localStorage.setItem(STORAGE_KEYS.favorites, JSON.stringify(list));
}

function toggleFavorite(card) {
  const id = card.dataset.favoriteId;
  const title = card.dataset.favoriteTitle;
  const type = card.dataset.favoriteType;
  if (!id || !title) return;

  let favorites = loadFavorites();
  const existingIndex = favorites.findIndex((item) => item.id === id);
  if (existingIndex >= 0) {
    favorites.splice(existingIndex, 1);
    card.querySelector(".add-favorite").classList.remove("is-active");
    card.querySelector(".add-favorite").textContent = "Save to favorites";
    showToast("Removed from favorites");
  } else {
    favorites.push({ id, title, type });
    card.querySelector(".add-favorite").classList.add("is-active");
    card.querySelector(".add-favorite").textContent = "Saved";
    showToast("Added to favorites");
  }
  saveFavorites(favorites);
  renderFavorites();
}

function setupFavorites() {
  const favoriteCards = document.querySelectorAll("[data-favorite-id]");
  if (!favoriteCards.length) return;
  const favorites = loadFavorites();
  favoriteCards.forEach((card) => {
    const id = card.dataset.favoriteId;
    const button = card.querySelector(".add-favorite");
    if (!button) return;
    if (favorites.some((fav) => fav.id === id)) {
      button.classList.add("is-active");
      button.textContent = "Saved";
    }
    button.addEventListener("click", () => toggleFavorite(card));
  });
  renderFavorites();
}

function renderFavorites() {
  const container = document.getElementById("favorites-list");
  const emptyText = document.getElementById("favorites-empty");
  if (!container) return;
  const favorites = loadFavorites();
  container.innerHTML = "";
  if (!favorites.length) {
    if (emptyText) emptyText.hidden = false;
    return;
  }
  if (emptyText) emptyText.hidden = true;
  favorites.forEach((fav) => {
    const pill = document.createElement("div");
    pill.className = "favorite-pill";
    pill.innerHTML = `
      <span>${fav.title}</span>
      <button type="button" aria-label="Remove ${fav.title} from favorites">×</button>
    `;
    pill.querySelector("button").addEventListener("click", () => {
      const next = favorites.filter((item) => item.id !== fav.id);
      saveFavorites(next);
      renderFavorites();
      const sourceCard = document.querySelector(`[data-favorite-id="${fav.id}"] .add-favorite`);
      if (sourceCard) {
        sourceCard.classList.remove("is-active");
        sourceCard.textContent = "Save to favorites";
      }
      showToast("Removed from favorites");
    });
    container.appendChild(pill);
  });
}

function setupAffirmations() {
  const stack = document.getElementById("affirmation-stack");
  const reminderList = document.getElementById("reminder-list");
  if (!stack && !reminderList) return;

  const affirmations = [
    "I am worthy of my own patience.",
    "My body is my teammate, not my rival.",
    "I am learning and that is enough.",
    "I can step back from screens and tune into myself.",
    "My uniqueness is my strength.",
    "I deserve rest and kindness.",
    "I belong in every room I enter.",
    "I can grow without rushing."
  ];

  const reminders = [
    "Comparison is a storyteller — I choose my own narrative.",
    "Today I will compliment a friend and myself.",
    "Offline moments recharge my creativity.",
    "My feelings are valid, and I allow them to pass gently.",
    "I celebrate progress over perfection.",
    "I am proud of the way I keep showing up."
  ];

  const today = new Date();
  const seed = today.getDate() + today.getMonth() * 3;
  const shuffle = (list) =>
    list
      .map((item, index) => ({ sort: (index + seed * 7) % list.length, value: item }))
      .sort((a, b) => a.sort - b.sort)
      .map((item) => item.value);

  const todaysAffirmations = shuffle(affirmations).slice(0, 3);
  const todaysReminders = shuffle(reminders).slice(0, reminders.length);

  if (stack) {
    todaysAffirmations.forEach((text, index) => {
      const card = document.createElement("article");
      card.className = "affirmation-card";
      card.innerHTML = `<h3>Affirmation ${index + 1}</h3><p>${text}</p>`;
      stack.appendChild(card);
    });
  }

  if (reminderList) {
    todaysReminders.forEach((text) => {
      const li = document.createElement("li");
      li.textContent = text;
      reminderList.appendChild(li);
    });
  }
}

function init() {
  loadTheme();
  if (themeToggle) themeToggle.addEventListener("click", toggleTheme);
  setupMenuToggle();
  setupSignIn();
  setupJournalPrompts();
  setupFavorites();
  setupAffirmations();
}

init();

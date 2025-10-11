import { registerRoute, initRouter, navigate } from "./router.js";
import { store } from "./store.js";
import {
  quotes,
  affirmations,
  soundscapes,
  positivityChallenges,
} from "../data/dailyContent.js";
import {
  journalPrompts,
  mindfulnessMoments,
  sleepChecklist,
  blockedWords,
} from "../data/activities.js";

const appEl = document.getElementById("app");
const toastEl = document.getElementById("notification-toast");
const signInModal = document.getElementById("sign-in-modal");
const signInBtn = document.getElementById("sign-in-btn");
const signInEmail = document.getElementById("sign-in-email");
const menuToggle = document.querySelector(".menu-toggle");
const nav = document.querySelector(".nav");

const blockedWordRegex = new RegExp(blockedWords.join("|"), "i");

function dayOfYear(date = new Date()) {
  const start = new Date(date.getFullYear(), 0, 0);
  const diff =
    date - start + (start.getTimezoneOffset() - date.getTimezoneOffset()) * 60000;
  return Math.floor(diff / 86400000);
}

function getDailyItem(items, offset = 0) {
  const index = (dayOfYear() + offset) % items.length;
  return items[index];
}

function clearApp() {
  appEl.innerHTML = "";
}

function createSection(className = "") {
  const section = document.createElement("section");
  section.className = `section ${className}`.trim();
  return section;
}

function renderHome() {
  clearApp();
  const heroSection = createSection("hero");
  const heroTitle = document.createElement("h1");
  heroTitle.textContent = "Find a softer rhythm for your day";
  const heroTagline = document.createElement("p");
  heroTagline.className = "hero__tagline";
  heroTagline.textContent =
    "Self Haven offers quick moments of calm, grounded journaling, and gentle challenges to help you reconnect with yourself—no sign up required.";
  const heroImage = document.createElement("div");
  heroImage.className = "hero__image";
  heroImage.innerHTML =
    "Wrap yourself in warmth today. Breathe in kindness. Exhale comparison.";

  heroSection.append(heroTitle, heroTagline, heroImage);

  const startersSection = createSection();
  const starterHeading = document.createElement("h2");
  starterHeading.textContent = "Starter activities";

  const starterGrid = document.createElement("div");
  starterGrid.className = "starter-grid";

  const quoteCard = document.createElement("article");
  quoteCard.className = "card";
  const dailyQuote = getDailyItem(quotes);
  quoteCard.innerHTML = `
    <span class="badge">Daily quote</span>
    <h3>"${dailyQuote.text}"</h3>
    <p>— ${dailyQuote.author}</p>
  `;

  const affirmationCard = document.createElement("article");
  affirmationCard.className = "card";
  const dailyAffirmation = getDailyItem(affirmations, 1);
  affirmationCard.innerHTML = `
    <span class="badge">Affirmation</span>
    <p>${dailyAffirmation}</p>
  `;

  const soundCard = document.createElement("article");
  soundCard.className = "card";
  const dailySound = getDailyItem(soundscapes, 2);
  soundCard.innerHTML = `
    <span class="badge">Soundscape</span>
    <h3>${dailySound.title}</h3>
    <p>${dailySound.description}</p>
    <button class="primary" data-route="/activities" data-activity="sounds">Play now</button>
  `;

  starterGrid.append(quoteCard, affirmationCard, soundCard);
  startersSection.append(starterHeading, starterGrid);

  appEl.append(heroSection, startersSection);

  starterGrid.querySelectorAll("[data-route]").forEach((btn) => {
    btn.addEventListener("click", () => {
      navigate("/activities");
      requestAnimationFrame(() => {
        const target = btn.dataset.activity;
        if (target) {
          showActivityTab(target);
        }
      });
    });
  });

  appEl.focus();
}

function renderActivities() {
  clearApp();
  const section = createSection();
  section.dataset.view = "activities";
  section.innerHTML = `
    <h1>Activities</h1>
    <p>Pick a path that feels supportive right now. Favorites stay saved on this device.</p>
    <div class="activity-tabs" role="tablist"></div>
    <div class="activity-panel" role="tabpanel"></div>
  `;

  const tabsEl = section.querySelector(".activity-tabs");
  const panelEl = section.querySelector(".activity-panel");

  const tabs = [
    { id: "sounds", label: "Soundscapes" },
    { id: "journal", label: "Journal" },
    { id: "mindfulness", label: "Mindfulness" },
    { id: "sleep", label: "Sleep support" },
    { id: "positivity", label: "Positivity" },
  ];

  tabs.forEach((tab, index) => {
    const btn = document.createElement("button");
    btn.textContent = tab.label;
    btn.dataset.tab = tab.id;
    btn.setAttribute("role", "tab");
    btn.setAttribute("aria-selected", index === 0);
    if (index === 0) btn.classList.add("active");
    btn.addEventListener("click", () => showActivityTab(tab.id));
    tabsEl.append(btn);
  });

  function renderSounds() {
    panelEl.innerHTML = "";
    soundscapes.forEach((sound) => {
      const card = document.createElement("article");
      card.className = "card audio-card";
      card.innerHTML = `
        <div>
          <h3>${sound.title}</h3>
          <p>${sound.description}</p>
          <p><strong>${sound.duration}</strong></p>
        </div>
        <audio controls preload="none" src="${sound.src}"></audio>
      `;
      const favBtn = createFavoriteButton({
        id: sound.id,
        type: "sound",
        title: sound.title,
        description: sound.description,
      });
      card.append(favBtn);
      panelEl.append(card);
    });
  }

  function renderJournal() {
    panelEl.innerHTML = "";
    const state = store.getState();
    const savedEntries = state.journalEntries;

    const promptList = document.createElement("div");
    promptList.className = "list";

    journalPrompts.forEach((prompt, index) => {
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <h3>${prompt.title}</h3>
        <p>${prompt.prompt}</p>
      `;

      const textarea = document.createElement("textarea");
      textarea.placeholder = "Write freely—your words stay on this device.";
      textarea.value = savedEntries[prompt.id] ?? "";
      textarea.setAttribute("aria-label", `${prompt.title} journal entry`);

      const warning = document.createElement("div");
      warning.className = "warning-banner";
      warning.hidden = true;
      warning.textContent =
        "If a word feels harsh, consider rephrasing with kindness. Your thoughts matter.";

      textarea.addEventListener("input", () => {
        const value = textarea.value;
        const hasBlocked = blockedWordRegex.test(value);
        warning.hidden = !hasBlocked;
      });

      if (textarea.value) {
        warning.hidden = !blockedWordRegex.test(textarea.value);
      }

      const buttonRow = document.createElement("div");
      buttonRow.className = "button-row";

      const saveBtn = document.createElement("button");
      saveBtn.className = "primary";
      saveBtn.textContent = "Save";
      saveBtn.addEventListener("click", () => {
        store.saveJournal(prompt.id, textarea.value);
        showToast("Saved in this browser.");
      });

      const exportBtn = document.createElement("button");
      exportBtn.className = "secondary";
      exportBtn.textContent = "Export .txt";
      exportBtn.addEventListener("click", () => {
        const blob = new Blob([
          `${prompt.title}\n\n${textarea.value}\n`,
        ]);
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `${prompt.id}.txt`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
      });

      const favBtn = createFavoriteButton({
        id: prompt.id,
        type: "journal",
        title: prompt.title,
        description: prompt.prompt,
      });

      buttonRow.append(saveBtn, exportBtn, favBtn);
      card.append(textarea, warning, buttonRow);
      promptList.append(card);
    });

    panelEl.append(promptList);
  }

  function renderMindfulness() {
    panelEl.innerHTML = "";
    mindfulnessMoments.forEach((moment) => {
      const card = document.createElement("article");
      card.className = "card";
      const timerDisplay = document.createElement("div");
      timerDisplay.className = "timer-display";
      timerDisplay.textContent = formatTime(moment.duration);

      const description = document.createElement("p");
      description.textContent = moment.description;

      const buttonRow = document.createElement("div");
      buttonRow.className = "button-row";
      const startBtn = document.createElement("button");
      startBtn.className = "primary";
      startBtn.textContent = "Start";
      const resetBtn = document.createElement("button");
      resetBtn.className = "secondary";
      resetBtn.textContent = "Reset";

      let intervalId = null;
      let remaining = moment.duration;

      function tick() {
        remaining -= 1;
        timerDisplay.textContent = formatTime(remaining);
        if (remaining <= 0) {
          clearInterval(intervalId);
          intervalId = null;
          showToast("Nice work—notice how you feel right now.");
        }
      }

      startBtn.addEventListener("click", () => {
        if (intervalId) return;
        remaining = moment.duration;
        timerDisplay.textContent = formatTime(remaining);
        intervalId = setInterval(() => {
          tick();
          if (remaining <= 0) {
            timerDisplay.textContent = "00:00";
          }
        }, 1000);
      });

      resetBtn.addEventListener("click", () => {
        if (intervalId) {
          clearInterval(intervalId);
          intervalId = null;
        }
        remaining = moment.duration;
        timerDisplay.textContent = formatTime(remaining);
      });

      const favBtn = createFavoriteButton({
        id: moment.id,
        type: "mindfulness",
        title: moment.title,
        description: moment.description,
      });

      card.innerHTML = `<h3>${moment.title}</h3>`;
      card.append(description, timerDisplay, buttonRow, favBtn);
      buttonRow.append(startBtn, resetBtn);
      panelEl.append(card);
    });
  }

  function renderSleep() {
    panelEl.innerHTML = "";
    const list = document.createElement("div");
    list.className = "list";
    const state = store.getState();

    sleepChecklist.forEach((item) => {
      const entry = document.createElement("label");
      entry.className = "checklist-item";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = Boolean(state.sleepChecklist[item.id]);
      checkbox.addEventListener("change", () => {
        store.toggleChecklist(item.id, checkbox.checked);
      });
      const span = document.createElement("span");
      span.textContent = item.label;
      entry.append(checkbox, span);
      list.append(entry);
    });

    panelEl.append(list);
  }

  function renderPositivity() {
    panelEl.innerHTML = "";
    const card = document.createElement("article");
    card.className = "card";
    const dailyChallenge = getDailyItem(positivityChallenges);
    const state = store.getState();
    const completedOn = state.positivityCompleted[dailyChallenge.id];
    const isCompletedToday =
      completedOn && new Date(completedOn).toDateString() === new Date().toDateString();

    card.innerHTML = `
      <h3>Daily positivity</h3>
      <p>${dailyChallenge.text}</p>
    `;

    const button = document.createElement("button");
    button.className = "primary";
    button.textContent = isCompletedToday ? "Completed today" : "Mark as done";
    button.disabled = isCompletedToday;
    button.addEventListener("click", () => {
      store.markPositivity(dailyChallenge.id);
      button.textContent = "Completed today";
      button.disabled = true;
      showToast("Saved—celebrate this moment! ✨");
    });

    const favBtn = createFavoriteButton({
      id: dailyChallenge.id,
      type: "positivity",
      title: "Daily positivity",
      description: dailyChallenge.text,
    });

    card.append(button, favBtn);
    panelEl.append(card);
  }

  const renderers = {
    sounds: renderSounds,
    journal: renderJournal,
    mindfulness: renderMindfulness,
    sleep: renderSleep,
    positivity: renderPositivity,
  };

  function show(tab) {
    tabsEl.querySelectorAll("button").forEach((btn) => {
      const isActive = btn.dataset.tab === tab;
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-selected", isActive);
    });
    renderers[tab]?.();
  }

  section.dataset.activeTab = "sounds";
  panelEl.dataset.active = "sounds";
  show(section.dataset.activeTab);

  appEl.append(section);
  appEl.focus();

  section.showTab = show;
}

function showActivityTab(tabId) {
  const section = appEl.querySelector('[data-view="activities"]');
  if (section && typeof section.showTab === "function") {
    section.showTab(tabId);
  }
}

function renderFavorites() {
  clearApp();
  const section = createSection();
  section.dataset.view = "favorites";
  section.innerHTML = `
    <h1>Favorites</h1>
    <p>Anything you heart will land here and stay on this device.</p>
    <div class="list" id="favorites-list"></div>
  `;

  const list = section.querySelector("#favorites-list");
  const favorites = store.getState().favorites;
  if (!favorites.length) {
    const empty = document.createElement("p");
    empty.textContent = "No favorites yet. Tap the heart on any activity.";
    list.append(empty);
  } else {
    favorites.forEach((item) => {
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <h3>${item.title}</h3>
        <p>${item.description}</p>
      `;
      const removeBtn = document.createElement("button");
      removeBtn.className = "secondary";
      removeBtn.textContent = "Remove";
      removeBtn.addEventListener("click", () => {
        store.toggleFavorite(item);
        renderFavorites();
      });
      card.append(removeBtn);
      list.append(card);
    });
  }

  appEl.append(section);
  appEl.focus();
}

function renderSettings() {
  clearApp();
  const state = store.getState();
  const section = createSection();
  section.dataset.view = "settings";
  section.innerHTML = `
    <h1>Settings</h1>
    <div class="list">
      <label class="checklist-item">
        <input type="checkbox" id="dark-mode-toggle" ${state.theme === "dark" ? "checked" : ""} />
        <span>Dark mode</span>
      </label>
      <label class="checklist-item">
        <input type="checkbox" id="notification-toggle" ${state.notificationOptIn ? "checked" : ""} />
        <span>Gentle daily reminder</span>
      </label>
      <button class="secondary" id="reset-data">Clear saved data</button>
    </div>
    <p>Notifications are stored locally and can be disabled anytime. If you choose reminders, we will ask for browser permission first.</p>
  `;

  const darkToggle = section.querySelector("#dark-mode-toggle");
  const notificationToggle = section.querySelector("#notification-toggle");
  const resetButton = section.querySelector("#reset-data");

  darkToggle.addEventListener("change", () => {
    const theme = darkToggle.checked ? "dark" : "light";
    applyTheme(theme);
    store.setTheme(theme);
  });

  if ("Notification" in window) {
    notificationToggle.addEventListener("change", async () => {
      if (notificationToggle.checked) {
        const permission = await Notification.requestPermission();
        if (permission !== "granted") {
          notificationToggle.checked = false;
          store.setNotificationOptIn(false);
          showToast("Notification permission denied.");
          return;
        }
        store.setNotificationOptIn(true);
        scheduleReminder();
        showToast("Daily reminder scheduled. You can disable anytime.");
      } else {
        store.setNotificationOptIn(false);
        store.updateNotificationTimestamp(null);
        showToast("Reminders turned off.");
      }
    });
  } else {
    notificationToggle.disabled = true;
    notificationToggle.nextElementSibling.textContent =
      "Gentle daily reminder (not supported in this browser)";
  }

  resetButton.addEventListener("click", () => {
    if (confirm("Clear all saved preferences and notes?")) {
      store.clearAll();
      applyTheme("light");
      renderSettings();
      showToast("All data cleared from this device.");
    }
  });

  appEl.append(section);
  appEl.focus();
}

function createFavoriteButton(item) {
  const button = document.createElement("button");
  button.className = "favorite-button";
  const icon = document.createElement("span");
  icon.setAttribute("aria-hidden", "true");
  const label = document.createElement("span");
  updateState();

  button.append(icon, label);

  button.addEventListener("click", () => {
    store.toggleFavorite(item);
    updateState();
    showToast(
      store.isFavorite(item) ? "Added to favorites." : "Removed from favorites."
    );
    document.dispatchEvent(new CustomEvent("favorites-updated"));
  });

  function updateState() {
    const isFav = store.isFavorite(item);
    button.classList.toggle("active", isFav);
    icon.textContent = isFav ? "❤️" : "🤍";
    label.textContent = isFav ? "Saved" : "Save";
  }

  return button;
}

function showToast(message) {
  toastEl.textContent = message;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 2600);
}

function formatTime(seconds) {
  const mins = String(Math.floor(seconds / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");
  return `${mins}:${secs}`;
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
}

function scheduleReminder() {
  if (!("Notification" in window)) return;
  const state = store.getState();
  if (!state.notificationOptIn) return;

  const lastTimestamp = state.notificationTimestamp
    ? new Date(state.notificationTimestamp)
    : null;
  const now = new Date();
  const next = new Date();
  next.setHours(19, 0, 0, 0);
  if (now > next) {
    next.setDate(next.getDate() + 1);
  }

  const timeout = next.getTime() - now.getTime();
  if (lastTimestamp && now - lastTimestamp < 23 * 3600 * 1000) {
    return;
  }

  setTimeout(() => {
    new Notification("Self Haven reminder", {
      body: "Take a minute to check in with yourself today. A little calm goes a long way.",
      silent: true,
    });
    store.updateNotificationTimestamp(new Date());
    scheduleReminder();
  }, timeout);
}

function attachGlobalListeners() {
  document.querySelectorAll(".nav__link").forEach((btn) => {
    btn.addEventListener("click", () => {
      navigate(btn.dataset.route);
      nav.classList.remove("open");
    });
  });

  menuToggle.addEventListener("click", () => {
    nav.classList.toggle("open");
  });

  document.addEventListener("click", (event) => {
    if (!nav.contains(event.target) && event.target !== menuToggle) {
      nav.classList.remove("open");
    }
  });

  if (signInBtn) {
    signInBtn.addEventListener("click", () => {
      const state = store.getState();
      if (state.pseudoUser?.email) {
        signInEmail.value = state.pseudoUser.email;
      } else {
        signInEmail.value = "";
      }
      signInModal.showModal();
    });
  }

  if (signInModal) {
    signInModal.addEventListener("close", () => {
      if (signInModal.returnValue === "confirm") {
        const email = signInEmail.value.trim();
        if (email) {
          store.savePseudoUser(email);
          showToast("Preference saved locally.");
        }
      }
    });
  }

  document.addEventListener("favorites-updated", () => {
    if (location.hash.replace(/^#/, "") === "/favorites") {
      renderFavorites();
    }
  });
}

function hydrateTheme() {
  const state = store.getState();
  applyTheme(state.theme || "light");
}

function hydrateNotifications() {
  if (store.getState().notificationOptIn) {
    scheduleReminder();
  }
}

registerRoute("/", renderHome);
registerRoute("/activities", renderActivities);
registerRoute("/favorites", renderFavorites);
registerRoute("/settings", renderSettings);
registerRoute("*", renderHome);

attachGlobalListeners();
hydrateTheme();
hydrateNotifications();

initRouter("/");

appEl.focus();

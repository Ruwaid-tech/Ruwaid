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

let audioContext;
let masterGain;
const activeSoundscapes = new Map();

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

function ensureAudioContext() {
  if (audioContext) return audioContext;
  const ContextClass = window.AudioContext || window.webkitAudioContext;
  if (!ContextClass) {
    return null;
  }
  audioContext = new ContextClass();
  masterGain = audioContext.createGain();
  masterGain.gain.value = 0.6;
  masterGain.connect(audioContext.destination);
  return audioContext;
}

function resumeAudioContext(context) {
  if (!context || context.state !== "suspended") return;
  context.resume().catch(() => {
    /* ignored */
  });
}

function createNoiseBuffer(context, duration, type) {
  const length = Math.max(1, Math.floor(duration * context.sampleRate));
  const buffer = context.createBuffer(1, length, context.sampleRate);
  const data = buffer.getChannelData(0);
  if (type === "brown") {
    let last = 0;
    for (let i = 0; i < length; i += 1) {
      const white = Math.random() * 2 - 1;
      last = (last + 0.02 * white) / 1.02;
      data[i] = last * 3.5;
    }
  } else if (type === "pink") {
    let b0 = 0;
    let b1 = 0;
    let b2 = 0;
    let b3 = 0;
    let b4 = 0;
    let b5 = 0;
    let b6 = 0;
    for (let i = 0; i < length; i += 1) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.969 * b2 + white * 0.153852;
      b3 = 0.8665 * b3 + white * 0.3104856;
      b4 = 0.55 * b4 + white * 0.5329522;
      b5 = -0.7616 * b5 - white * 0.016898;
      const pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
      b6 = white * 0.115926;
      data[i] = pink * 0.11;
    }
  } else {
    for (let i = 0; i < length; i += 1) {
      data[i] = Math.random() * 2 - 1;
    }
  }
  return buffer;
}

function createOceanSound(context) {
  const source = context.createBufferSource();
  source.buffer = createNoiseBuffer(context, 6, "brown");
  source.loop = true;

  const filter = context.createBiquadFilter();
  filter.type = "lowpass";
  filter.frequency.value = 420;

  const gain = context.createGain();
  gain.gain.value = 0.38;

  const lfo = context.createOscillator();
  lfo.type = "sine";
  lfo.frequency.value = 0.16;
  const lfoGain = context.createGain();
  lfoGain.gain.value = 0.18;
  lfo.connect(lfoGain).connect(gain.gain);

  source.connect(filter).connect(gain).connect(masterGain);
  source.start();
  lfo.start();

  return () => {
    try {
      source.stop();
    } catch (error) {
      /* noop */
    }
    try {
      lfo.stop();
    } catch (error) {
      /* noop */
    }
    source.disconnect();
    filter.disconnect();
    gain.disconnect();
    lfo.disconnect();
    lfoGain.disconnect();
  };
}

function createForestSound(context) {
  const ambience = context.createBufferSource();
  ambience.buffer = createNoiseBuffer(context, 5, "pink");
  ambience.loop = true;

  const bandpass = context.createBiquadFilter();
  bandpass.type = "bandpass";
  bandpass.frequency.value = 1500;
  bandpass.Q.value = 0.9;

  const ambienceGain = context.createGain();
  ambienceGain.gain.value = 0.24;

  ambience.connect(bandpass).connect(ambienceGain).connect(masterGain);

  const birdOsc = context.createOscillator();
  birdOsc.type = "sine";
  birdOsc.frequency.value = 1800;
  const birdGain = context.createGain();
  birdGain.gain.value = 0;
  birdOsc.connect(birdGain).connect(masterGain);
  birdOsc.start();

  let chirpTimer = setInterval(() => {
    const now = context.currentTime;
    const chirpGain = birdGain.gain;
    chirpGain.cancelScheduledValues(now);
    chirpGain.setValueAtTime(0.0001, now);
    chirpGain.linearRampToValueAtTime(0.18, now + 0.05);
    chirpGain.exponentialRampToValueAtTime(0.0001, now + 0.4);
    const startFreq = 1400 + Math.random() * 700;
    birdOsc.frequency.cancelScheduledValues(now);
    birdOsc.frequency.setValueAtTime(startFreq, now);
    birdOsc.frequency.linearRampToValueAtTime(startFreq + 250, now + 0.2);
  }, 3400);

  ambience.start();

  return () => {
    clearInterval(chirpTimer);
    chirpTimer = null;
    try {
      ambience.stop();
    } catch (error) {
      /* noop */
    }
    try {
      birdOsc.stop();
    } catch (error) {
      /* noop */
    }
    ambience.disconnect();
    bandpass.disconnect();
    ambienceGain.disconnect();
    birdOsc.disconnect();
    birdGain.disconnect();
  };
}

function createRainSound(context) {
  const shower = context.createBufferSource();
  shower.buffer = createNoiseBuffer(context, 4, "white");
  shower.loop = true;

  const highpass = context.createBiquadFilter();
  highpass.type = "highpass";
  highpass.frequency.value = 800;

  const rainGain = context.createGain();
  rainGain.gain.value = 0.32;

  const swayOsc = context.createOscillator();
  swayOsc.type = "sine";
  swayOsc.frequency.value = 0.2;
  const swayGain = context.createGain();
  swayGain.gain.value = 0.08;
  swayOsc.connect(swayGain).connect(rainGain.gain);

  shower.connect(highpass).connect(rainGain).connect(masterGain);

  const dropOsc = context.createOscillator();
  dropOsc.type = "triangle";
  dropOsc.frequency.value = 1200;
  const dropGain = context.createGain();
  dropGain.gain.value = 0;
  dropOsc.connect(dropGain).connect(masterGain);
  dropOsc.start();

  let dropTimer = setInterval(() => {
    const now = context.currentTime;
    dropGain.gain.cancelScheduledValues(now);
    dropGain.gain.setValueAtTime(0.0001, now);
    dropGain.gain.linearRampToValueAtTime(0.16, now + 0.015);
    dropGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);
    const base = 900 + Math.random() * 400;
    dropOsc.frequency.cancelScheduledValues(now);
    dropOsc.frequency.setValueAtTime(base, now);
    dropOsc.frequency.exponentialRampToValueAtTime(700, now + 0.3);
  }, 2100);

  shower.start();
  swayOsc.start();

  return () => {
    clearInterval(dropTimer);
    dropTimer = null;
    try {
      shower.stop();
    } catch (error) {
      /* noop */
    }
    try {
      swayOsc.stop();
    } catch (error) {
      /* noop */
    }
    try {
      dropOsc.stop();
    } catch (error) {
      /* noop */
    }
    shower.disconnect();
    highpass.disconnect();
    rainGain.disconnect();
    swayOsc.disconnect();
    swayGain.disconnect();
    dropOsc.disconnect();
    dropGain.disconnect();
  };
}

const SOUND_BUILDERS = {
  "ocean-flow": createOceanSound,
  "forest-glow": createForestSound,
  "rain-haven": createRainSound,
};

function stopSoundscape(id) {
  const active = activeSoundscapes.get(id);
  if (!active) return;
  try {
    active.stop();
  } catch (error) {
    console.error("Unable to stop soundscape", error);
  }
  active.button.textContent = `Play ${active.label}`;
  active.button.setAttribute("aria-pressed", "false");
  if (active.status) {
    active.status.textContent = `${active.label} is paused.`;
  }
  activeSoundscapes.delete(id);
}

function startSoundscape(id, button, status, label) {
  const context = ensureAudioContext();
  if (!context) {
    button.disabled = true;
    button.textContent = `${label} unavailable`;
    if (status) status.textContent = "Audio playback is not supported on this device.";
    return;
  }
  resumeAudioContext(context);
  const builder = SOUND_BUILDERS[id];
  if (!builder) return;
  const stop = builder(context);
  activeSoundscapes.set(id, { stop, button, status, label });
  button.textContent = `Pause ${label}`;
  button.setAttribute("aria-pressed", "true");
  if (status) {
    status.textContent = `${label} is playing softly.`;
  }
}

function stopAllSoundscapes() {
  const ids = Array.from(activeSoundscapes.keys());
  ids.forEach((id) => stopSoundscape(id));
}

function setupSoundscapes() {
  const toggles = document.querySelectorAll(".soundscape-toggle");
  if (!toggles.length) return;
  const hasAudioSupport = Boolean(window.AudioContext || window.webkitAudioContext);
  toggles.forEach((button) => {
    const id = button.dataset.soundId;
    const label = button.dataset.soundLabel || button.textContent.trim();
    const status = document.querySelector(`[data-sound-status="${id}"]`);
    if (!hasAudioSupport) {
      button.disabled = true;
      button.textContent = `${label} unavailable`;
      if (status) {
        status.textContent = "Audio playback is not supported on this device.";
      }
      return;
    }
    button.addEventListener("click", () => {
      if (activeSoundscapes.has(id)) {
        stopSoundscape(id);
      } else {
        startSoundscape(id, button, status, label);
      }
    });
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopAllSoundscapes();
    }
  });
  window.addEventListener("pagehide", stopAllSoundscapes);
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
  setupSoundscapes();
  setupAffirmations();
}

init();

const STORAGE_KEY = "self-haven-state";
const VERSION = 1;

const defaultState = {
  version: VERSION,
  favorites: [],
  journalEntries: {},
  sleepChecklist: {},
  positivityCompleted: {},
  theme: "light",
  notificationOptIn: false,
  notificationTimestamp: null,
  pseudoUser: null,
};

function migrateState(raw) {
  if (!raw || raw.version !== VERSION) {
    return { ...defaultState };
  }
  return { ...defaultState, ...raw };
}

function readState() {
  try {
    const text = localStorage.getItem(STORAGE_KEY);
    if (!text) return { ...defaultState };
    const parsed = JSON.parse(text);
    return migrateState(parsed);
  } catch (error) {
    console.warn("Unable to read storage", error);
    return { ...defaultState };
  }
}

function writeState(state) {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ ...state, version: VERSION })
  );
}

let currentState = readState();

export const store = {
  getState() {
    return currentState;
  },
  setState(partial) {
    currentState = { ...currentState, ...partial };
    writeState(currentState);
  },
  toggleFavorite(item) {
    const favorites = currentState.favorites;
    const exists = favorites.some(
      (fav) => fav.type === item.type && fav.id === item.id
    );
    const next = exists
      ? favorites.filter((fav) => !(fav.type === item.type && fav.id === item.id))
      : favorites.concat(item);
    this.setState({ favorites: next });
    return next;
  },
  isFavorite(item) {
    return currentState.favorites.some(
      (fav) => fav.type === item.type && fav.id === item.id
    );
  },
  saveJournal(id, text) {
    const journalEntries = { ...currentState.journalEntries, [id]: text };
    this.setState({ journalEntries });
  },
  toggleChecklist(id, checked) {
    const sleepChecklist = { ...currentState.sleepChecklist, [id]: checked };
    this.setState({ sleepChecklist });
  },
  markPositivity(id) {
    const positivityCompleted = {
      ...currentState.positivityCompleted,
      [id]: new Date().toISOString(),
    };
    this.setState({ positivityCompleted });
  },
  setTheme(theme) {
    this.setState({ theme });
  },
  setNotificationOptIn(value) {
    this.setState({ notificationOptIn: value });
  },
  updateNotificationTimestamp(date) {
    this.setState({ notificationTimestamp: date?.toISOString?.() ?? null });
  },
  savePseudoUser(email) {
    const pseudoUser = email
      ? {
          id: crypto.randomUUID?.() ?? Math.random().toString(36).slice(2),
          email,
          savedAt: new Date().toISOString(),
        }
      : null;
    this.setState({ pseudoUser });
    return pseudoUser;
  },
  clearAll() {
    currentState = { ...defaultState };
    writeState(currentState);
  },
};

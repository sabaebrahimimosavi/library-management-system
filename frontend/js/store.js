// js/store.js
// Small hand-rolled auth store using Vue's reactivity, shared by every
// component that imports it. No Vuex/Pinia needed at this scale.

const { reactive } = Vue;

const STORAGE_KEY = "library.auth";

function loadPersisted() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

const persisted = loadPersisted();

export const store = reactive({
  accessToken: persisted.accessToken || null,
  refreshToken: persisted.refreshToken || null,
  user: persisted.user || null, // { id, username, email, first_name, last_name, role, date_joined }

  get isAuthenticated() {
    return !!this.accessToken;
  },
  get isAdmin() {
    return this.user?.role === "ADMIN";
  },

  setTokens(access, refresh) {
    this.accessToken = access;
    this.refreshToken = refresh;
    this._persist();
  },
  setAccessToken(access) {
    this.accessToken = access;
    this._persist();
  },
  setUser(user) {
    this.user = user;
    this._persist();
  },
  clearAuth() {
    this.accessToken = null;
    this.refreshToken = null;
    this.user = null;
    localStorage.removeItem(STORAGE_KEY);
  },
  _persist() {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: this.accessToken,
        refreshToken: this.refreshToken,
        user: this.user,
      })
    );
  },
});

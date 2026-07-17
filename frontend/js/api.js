// js/api.js
// Thin fetch wrapper: attaches the JWT access token, transparently
// refreshes it once on a 401, and normalizes error bodies so views can
// just read `err.detail` / `err.fields`.

import { API_BASE_URL } from "./config.js";
import { store } from "./store.js";

class ApiError extends Error {
  constructor(status, body) {
    const detail =
      (body && (body.detail || body.non_field_errors?.[0])) ||
      "Something went wrong. Please try again.";
    super(detail);
    this.status = status;
    this.detail = detail;
    this.fields = body && typeof body === "object" ? body : {};
  }
}

let refreshInFlight = null;

async function doRefresh() {
  if (!store.refreshToken) throw new ApiError(401, { detail: "Session expired." });

  if (!refreshInFlight) {
    refreshInFlight = fetch(`${API_BASE_URL}/auth/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: store.refreshToken }),
    })
      .then(async (res) => {
        if (!res.ok) throw new ApiError(res.status, await safeJson(res));
        const data = await res.json();
        store.setAccessToken(data.access);
        return data.access;
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

async function safeJson(res) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * @param {string} path - e.g. "/books/books/"
 * @param {object} opts
 * @param {"GET"|"POST"|"PATCH"|"PUT"|"DELETE"} [opts.method]
 * @param {object} [opts.body]
 * @param {boolean} [opts.auth] - attach Authorization header (default true)
 * @param {boolean} [opts._retried] - internal, prevents infinite refresh loops
 */
export async function apiFetch(path, opts = {}) {
  const { method = "GET", body, auth = true, _retried = false } = opts;

  // FormData (used for the book cover-image upload) must NOT get a
  // Content-Type header set manually — the browser needs to add its own
  // multipart boundary — and must be sent as-is, not JSON.stringify'd.
  const isForm = typeof FormData !== "undefined" && body instanceof FormData;

  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";
  if (auth && store.accessToken) {
    headers["Authorization"] = `Bearer ${store.accessToken}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
  });

  if (res.status === 401 && auth && store.refreshToken && !_retried) {
    try {
      await doRefresh();
      return apiFetch(path, { ...opts, _retried: true });
    } catch {
      store.clearAuth();
      throw new ApiError(401, { detail: "Your session expired. Please log in again." });
    }
  }

  if (res.status === 204) return null;

  const data = await safeJson(res);

  if (!res.ok) {
    throw new ApiError(res.status, data);
  }
  return data;
}

function qs(params = {}) {
  const clean = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
  );
  const s = new URLSearchParams(clean).toString();
  return s ? `?${s}` : "";
}

export const auth = {
  register: (payload) => apiFetch("/auth/register/", { method: "POST", body: payload, auth: false }),
  login: (payload) => apiFetch("/auth/login/", { method: "POST", body: payload, auth: false }),
  clearAdminSession: () =>
    apiFetch(
      "/auth/clear-admin-session/",
      {
        method: "POST",
        auth: false,
      }
    ),
  me: () => apiFetch("/auth/me/"),
  updateMe: (payload) => apiFetch("/auth/me/", { method: "PATCH", body: payload }),
  logout: (refresh) => apiFetch("/auth/logout/", { method: "POST", body: { refresh } }),
  changePassword: (payload) => apiFetch("/auth/change-password/", { method: "POST", body: payload }),
  requestPasswordReset: (email) =>
    apiFetch("/auth/password-reset/", { method: "POST", body: { email }, auth: false }),
  confirmPasswordReset: (payload) =>
    apiFetch("/auth/password-reset/confirm/", { method: "POST", body: payload, auth: false }),
};

export const books = {
  list: (params) => apiFetch(`/books/books/${qs(params)}`),
  get: (id) => apiFetch(`/books/books/${id}/`),
  // `payload` may be a plain object (JSON) or a FormData instance (when a
  // cover image file is attached) — apiFetch handles both transparently.
  create: (payload) => apiFetch(`/books/books/`, { method: "POST", body: payload }),
  update: (id, payload) => apiFetch(`/books/books/${id}/`, { method: "PATCH", body: payload }),
  remove: (id) => apiFetch(`/books/books/${id}/`, { method: "DELETE" }),

  authors: (params) => apiFetch(`/books/authors/${qs(params)}`),
  createAuthor: (payload) => apiFetch(`/books/authors/`, { method: "POST", body: payload }),
  updateAuthor: (id, payload) => apiFetch(`/books/authors/${id}/`, { method: "PATCH", body: payload }),
  removeAuthor: (id) => apiFetch(`/books/authors/${id}/`, { method: "DELETE" }),

  genres: (params) => apiFetch(`/books/genres/${qs(params)}`),
  createGenre: (payload) => apiFetch(`/books/genres/`, { method: "POST", body: payload }),
  updateGenre: (id, payload) => apiFetch(`/books/genres/${id}/`, { method: "PATCH", body: payload }),
  removeGenre: (id) => apiFetch(`/books/genres/${id}/`, { method: "DELETE" }),

  publishers: (params) => apiFetch(`/books/publishers/${qs(params)}`),
  createPublisher: (payload) => apiFetch(`/books/publishers/`, { method: "POST", body: payload }),
  updatePublisher: (id, payload) => apiFetch(`/books/publishers/${id}/`, { method: "PATCH", body: payload }),
  removePublisher: (id) => apiFetch(`/books/publishers/${id}/`, { method: "DELETE" }),
};

export const reviews = {
  listForBook: (bookId) => apiFetch(`/books/${bookId}/reviews/`),
  create: (bookId, payload) => apiFetch(`/books/${bookId}/reviews/`, { method: "POST", body: payload }),
  update: (id, payload) => apiFetch(`/reviews/${id}/`, { method: "PATCH", body: payload }),
  remove: (id) => apiFetch(`/reviews/${id}/`, { method: "DELETE" }),
};

export const loans = {
  mine: (params) => apiFetch(`/loans/${qs(params)}`),
  borrow: (bookId) => apiFetch(`/loans/`, { method: "POST", body: { book: bookId } }),
  returnBook: (id) => apiFetch(`/loans/${id}/return_book/`, { method: "POST", body: {} }),
};

export const reservations = {
  mine: (params) => apiFetch(`/reservations/${qs(params)}`),
  create: (bookId) => apiFetch(`/reservations/`, { method: "POST", body: { book: bookId } }),
  cancel: (id) => apiFetch(`/reservations/${id}/cancel/`, { method: "POST", body: {} }),
};

export const fines = {
  mine: (params) => apiFetch(`/fines/${qs(params)}`),
  get: (id) => apiFetch(`/fines/${id}/`),
  // Admins call this with no body (marks paid directly); members must
  // supply { card_number } to go through the mock payment gateway.
  pay: (id, payload) => apiFetch(`/fines/${id}/pay/`, { method: "POST", body: payload || {} }),
  waive: (id) => apiFetch(`/fines/${id}/waive/`, { method: "POST", body: {} }),
  payments: (id) => apiFetch(`/fines/${id}/payments/`),
};

export const notifications = {
  list: (params) => apiFetch(`/notifications/${qs(params)}`),
  markRead: (id) => apiFetch(`/notifications/${id}/read/`, { method: "POST", body: {} }),
};

export const dashboard = {
  stats: () => apiFetch(`/dashboard/stats/`),
  mostBorrowed: (params) => apiFetch(`/dashboard/reports/most-borrowed/${qs(params)}`),
  mostActiveUsers: (params) => apiFetch(`/dashboard/reports/most-active-users/${qs(params)}`),
  overdueUsers: (params) => apiFetch(`/dashboard/reports/overdue-users/${qs(params)}`),
  monthlyBorrowing: (params) => apiFetch(`/dashboard/reports/monthly-borrowing/${qs(params)}`),
  popularBooks: (params) => apiFetch(`/dashboard/reports/popular-books/${qs(params)}`),
};

// Admin-only member directory. Promoting/demoting is a separate call
// from the list itself — see accounts.views.UserRoleUpdateView on the
// backend for why (dedicated guardrail against self-demotion).
export const members = {
  list: (params) => apiFetch(`/auth/users/${qs(params)}`),
  updateRole: (id, role) => apiFetch(`/auth/users/${id}/role/`, { method: "PATCH", body: { role } }),
};

export { ApiError };

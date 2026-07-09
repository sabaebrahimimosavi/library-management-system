import { store } from "../store.js";
import { notifications, ApiError } from "../api.js";

export default {
  name: "NotificationsView",
  template: /* html */ `
    <div class="container pb-5">
      <div class="d-flex justify-content-between align-items-end flex-wrap gap-2 mb-4">
        <div>
          <p class="eyebrow mb-1">Message slips</p>
          <h1 class="display-heading mb-0">Notifications</h1>
        </div>
        <div class="form-check form-switch">
          <input class="form-check-input" type="checkbox" id="unreadOnly" v-model="unreadOnly" />
          <label class="form-check-label text-mono small" for="unreadOnly">Unread only</label>
        </div>
      </div>

      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border" role="status"></div>
      </div>

      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

      <div v-else>
        <div v-if="filteredResults.length === 0" class="text-center py-5">
          <p class="fs-5">Nothing here{{ unreadOnly ? ' — you\\'re all caught up.' : ' yet.' }}</p>
        </div>

        <div v-else class="list-group">
          <div v-for="n in filteredResults" :key="n.id"
            class="list-group-item d-flex justify-content-between align-items-start gap-3"
            :class="{ 'bg-light': !n.is_read }">
            <div>
              <p class="mb-1">
                <strong class="text-mono small">{{ n.notification_type_display }}</strong>
                <span v-if="!n.is_read" class="stamp stamp-active ms-2">New</span>
              </p>
              <p class="mb-1 small">{{ n.subject }}</p>
              <p class="mb-1 text-muted small">{{ n.message }}</p>
              <p class="mb-0 text-mono small text-muted">{{ formatDate(n.created_at) }}</p>
            </div>
            <button v-if="!n.is_read" class="btn btn-sm btn-outline-primary flex-shrink-0"
              :disabled="markingId === n.id" @click="markRead(n)">
              <span v-if="markingId === n.id" class="spinner-border spinner-border-sm me-1"></span>
              Mark read
            </button>
          </div>
        </div>

        <nav v-if="totalPages > 1" class="d-flex justify-content-center mt-4" aria-label="Notification pages">
          <ul class="pagination">
            <li class="page-item" :class="{ disabled: page <= 1 }">
              <button class="page-link" @click="goToPage(page - 1)">Previous</button>
            </li>
            <li class="page-item disabled"><span class="page-link text-mono">{{ page }} / {{ totalPages }}</span></li>
            <li class="page-item" :class="{ disabled: page >= totalPages }">
              <button class="page-link" @click="goToPage(page + 1)">Next</button>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  `,
  data() {
    return {
      results: [],
      count: 0,
      page: 1,
      pageSize: 10,
      loading: true,
      error: "",
      unreadOnly: false,
      markingId: null,
    };
  },
  computed: {
    store() {
      return store;
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.count / this.pageSize));
    },
    filteredResults() {
      if (!this.unreadOnly) return this.results;
      return this.results.filter((n) => !n.is_read);
    },
  },
  async created() {
    await this.fetchNotifications();
  },
  methods: {
    formatDate(iso) {
      if (!iso) return "—";
      return new Date(iso).toLocaleString();
    },
    goToPage(p) {
      if (p < 1 || p > this.totalPages) return;
      this.page = p;
      this.fetchNotifications();
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    async fetchNotifications() {
      this.loading = true;
      this.error = "";
      try {
        const data = await notifications.list({ page: this.page });
        this.results = data.results ?? data;
        this.count = data.count ?? this.results.length;
      } catch (err) {
        this.error = err instanceof ApiError ? err.detail : "Could not load notifications.";
      } finally {
        this.loading = false;
      }
    },
    async markRead(n) {
      this.markingId = n.id;
      try {
        const updated = await notifications.markRead(n.id);
        const idx = this.results.findIndex((r) => r.id === n.id);
        if (idx !== -1) this.results.splice(idx, 1, updated);
      } catch {
        // Non-critical — leave it unread, user can retry.
      } finally {
        this.markingId = null;
      }
    },
  },
};

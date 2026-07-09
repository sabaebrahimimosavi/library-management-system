import { store } from "../store.js";
import { books, reservations, ApiError } from "../api.js";

export default {
  name: "MyReservationsView",
  template: /* html */ `
    <div class="container pb-5">
      <p class="eyebrow mb-1">Hold shelf</p>
      <h1 class="display-heading mb-4">{{ store.isAdmin ? 'All reservations' : 'My reservations' }}</h1>

      <div v-if="actionError" class="alert alert-danger py-2">{{ actionError }}</div>
      <div v-if="actionSuccess" class="alert alert-success py-2">{{ actionSuccess }}</div>

      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border" role="status"></div>
      </div>

      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

      <div v-else>
        <div v-if="results.length === 0" class="text-center py-5">
          <p class="fs-5">No reservations yet.</p>
          <router-link to="/books" class="btn btn-primary mt-2">Browse the catalog</router-link>
        </div>

        <div v-else class="row g-3">
          <div class="col-12 col-md-6" v-for="r in results" :key="r.id">
            <div class="card book-card p-3">
              <div class="d-flex justify-content-between align-items-start mb-1">
                <h2 class="book-title h6 mb-0">{{ bookTitle(r.book) }}</h2>
                <span class="stamp" :class="statusClass(r.status)">{{ r.status }}</span>
              </div>
              <p class="small text-muted mb-1">Reserved {{ formatDate(r.reserved_at) }}</p>
              <p v-if="r.expires_at" class="small text-muted mb-2">Expires {{ formatDate(r.expires_at) }}</p>
              <button v-if="r.status === 'PENDING' && !store.isAdmin" class="btn btn-sm btn-outline-danger align-self-start"
                :disabled="cancelingId === r.id" @click="cancelReservation(r)">
                <span v-if="cancelingId === r.id" class="spinner-border spinner-border-sm me-1"></span>
                Cancel reservation
              </button>
            </div>
          </div>
        </div>

        <nav v-if="totalPages > 1" class="d-flex justify-content-center mt-4" aria-label="Reservation pages">
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
      cancelingId: null,
      actionError: "",
      actionSuccess: "",
      bookTitles: {},
    };
  },
  computed: {
    store() {
      return store;
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.count / this.pageSize));
    },
  },
  async created() {
    await this.fetchReservations();
  },
  methods: {
    formatDate(iso) {
      if (!iso) return "—";
      return new Date(iso).toLocaleDateString();
    },
    statusClass(status) {
      if (status === "PENDING") return "stamp-active";
      if (status === "FULFILLED") return "stamp-available";
      if (status === "CANCELLED") return "stamp-unavailable";
      return "stamp-overdue"; // EXPIRED
    },
    bookTitle(bookId) {
      return this.bookTitles[bookId] || `Book #${bookId}`;
    },
    goToPage(p) {
      if (p < 1 || p > this.totalPages) return;
      this.page = p;
      this.fetchReservations();
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    async fetchReservations() {
      this.loading = true;
      this.error = "";
      try {
        const data = await reservations.mine({ page: this.page });
        this.results = data.results ?? data;
        this.count = data.count ?? this.results.length;
        // The reservation serializer only returns a book ID, not its
        // title — look each one up so the card can show something
        // readable instead of a bare number.
        await this.hydrateBookTitles();
      } catch (err) {
        this.error = err instanceof ApiError ? err.detail : "Could not load reservations.";
      } finally {
        this.loading = false;
      }
    },
    async hydrateBookTitles() {
      const missing = [...new Set(this.results.map((r) => r.book))].filter(
        (id) => !(id in this.bookTitles)
      );
      if (missing.length === 0) return;
      const fetched = await Promise.all(
        missing.map((id) => books.get(id).catch(() => null))
      );
      fetched.forEach((b, i) => {
        if (b) this.bookTitles[missing[i]] = b.title;
      });
    },
    async cancelReservation(r) {
      this.actionError = "";
      this.actionSuccess = "";
      this.cancelingId = r.id;
      try {
        await reservations.cancel(r.id);
        this.actionSuccess = `Reservation for "${this.bookTitle(r.book)}" cancelled.`;
        await this.fetchReservations();
      } catch (err) {
        this.actionError = err instanceof ApiError ? err.detail : "Could not cancel this reservation.";
      } finally {
        this.cancelingId = null;
      }
    },
  },
};

import { store } from "../store.js";
import { loans, ApiError } from "../api.js";

export default {
  name: "MyLoansView",
  template: /* html */ `
    <div class="container pb-5">
      <p class="eyebrow mb-1">Circulation desk</p>
      <h1 class="display-heading mb-4">{{ store.isAdmin ? 'All loans' : 'My loans' }}</h1>

      <div class="drawer-bar mb-4 d-flex flex-wrap gap-2 align-items-end">
        <div>
          <label class="form-label" for="statusFilter">Status</label>
          <select id="statusFilter" v-model="statusFilter" @change="onFilterChange" class="form-select form-select-sm">
            <option value="">All</option>
            <option value="ACTIVE">Active</option>
            <option value="OVERDUE">Overdue</option>
            <option value="RETURNED">Returned</option>
          </select>
        </div>
      </div>

      <div v-if="actionError" class="alert alert-danger py-2">{{ actionError }}</div>
      <div v-if="actionSuccess" class="alert alert-success py-2">{{ actionSuccess }}</div>

      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border" role="status"></div>
      </div>

      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

      <div v-else>
        <div v-if="filteredResults.length === 0" class="text-center py-5">
          <p class="fs-5">No loans match that filter.</p>
          <router-link to="/books" class="btn btn-primary mt-2">Browse the catalog</router-link>
        </div>

        <div v-else class="table-responsive">
          <table class="table align-middle">
            <thead>
              <tr class="text-mono small text-uppercase">
                <th>Title</th>
                <th v-if="store.isAdmin">Member</th>
                <th>Borrowed</th>
                <th>Due</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="loan in filteredResults" :key="loan.id">
                <td>
                  <router-link :to="'/books/' + loan.book">{{ loan.book_title }}</router-link>
                </td>
                <td v-if="store.isAdmin" class="text-mono small">{{ loan.username }}</td>
                <td class="small">{{ formatDate(loan.borrowed_at) }}</td>
                <td class="small">{{ loan.due_date }}</td>
                <td>
                  <span class="stamp" :class="statusClass(loan.status)">{{ loan.status }}</span>
                </td>
                <td class="text-end">
                  <button v-if="loan.status !== 'RETURNED' && !store.isAdmin" class="btn btn-sm btn-outline-primary"
                    :disabled="returningId === loan.id" @click="returnLoan(loan)">
                    <span v-if="returningId === loan.id" class="spinner-border spinner-border-sm me-1"></span>
                    Return
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <nav v-if="totalPages > 1" class="d-flex justify-content-center mt-4" aria-label="Loan pages">
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
      statusFilter: "",
      returningId: null,
      actionError: "",
      actionSuccess: "",
    };
  },
  computed: {
    store() {
      return store;
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.count / this.pageSize));
    },
    // NOTE: LoanViewSet doesn't define filterset_fields on the backend,
    // so a `?status=` query param is silently ignored there. Filtering
    // client-side over the current page instead — ask a backend dev to
    // add `filterset_fields = ["status"]` to LoanViewSet for a real fix.
    filteredResults() {
      if (!this.statusFilter) return this.results;
      return this.results.filter((l) => l.status === this.statusFilter);
    },
  },
  async created() {
    await this.fetchLoans();
  },
  methods: {
    formatDate(iso) {
      if (!iso) return "—";
      return new Date(iso).toLocaleDateString();
    },
    statusClass(status) {
      if (status === "OVERDUE") return "stamp-overdue";
      if (status === "RETURNED") return "stamp-returned";
      return "stamp-active";
    },
    onFilterChange() {
      // Client-side filter only (see filteredResults note above) — no
      // refetch needed, it just changes what's shown on this page.
    },
    goToPage(p) {
      if (p < 1 || p > this.totalPages) return;
      this.page = p;
      this.fetchLoans();
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    async fetchLoans() {
      this.loading = true;
      this.error = "";
      try {
        const data = await loans.mine({ page: this.page });
        this.results = data.results ?? data;
        this.count = data.count ?? this.results.length;
      } catch (err) {
        this.error = err instanceof ApiError ? err.detail : "Could not load loans.";
      } finally {
        this.loading = false;
      }
    },
    async returnLoan(loan) {
      this.actionError = "";
      this.actionSuccess = "";
      this.returningId = loan.id;
      try {
        await loans.returnBook(loan.id);
        this.actionSuccess = `"${loan.book_title}" marked as returned.`;
        await this.fetchLoans();
      } catch (err) {
        this.actionError = err instanceof ApiError ? err.detail : "Could not return this book.";
      } finally {
        this.returningId = null;
      }
    },
  },
};

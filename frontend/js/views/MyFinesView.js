import { store } from "../store.js";
import { fines, ApiError } from "../api.js";

export default {
  name: "MyFinesView",
  template: /* html */ `
    <div class="container pb-5">
      <p class="eyebrow mb-1">Ledger</p>
      <h1 class="display-heading mb-2">{{ store.isAdmin ? 'All fines' : 'My fines' }}</h1>
      <p v-if="!store.isAdmin && outstandingTotal > 0" class="fs-5 mb-4">
        Outstanding balance: <span class="text-mono fw-bold">\${{ outstandingTotal.toFixed(2) }}</span>
      </p>

      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border" role="status"></div>
      </div>

      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

      <div v-else>
        <div v-if="results.length === 0" class="text-center py-5">
          <p class="fs-5">No fines on record. Keep it that way!</p>
        </div>

        <div v-else class="table-responsive">
          <table class="table align-middle">
            <thead>
              <tr class="text-mono small text-uppercase">
                <th>Book</th>
                <th v-if="store.isAdmin">Member</th>
                <th>Due date</th>
                <th>Overdue days</th>
                <th>Amount</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="fine in results" :key="fine.id">
                <td>{{ fine.book_title }}</td>
                <td v-if="store.isAdmin" class="text-mono small">{{ fine.username }}</td>
                <td class="small">{{ fine.loan_due_date }}</td>
                <td class="small">{{ fine.overdue_days }}</td>
                <td class="text-mono">\${{ Number(fine.amount).toFixed(2) }}</td>
                <td>
                  <span class="stamp" :class="statusClass(fine.status)">{{ fine.status }}</span>
                </td>
                <td class="text-end">
                  <button v-if="fine.status === 'UNPAID' && !store.isAdmin" class="btn btn-sm btn-primary me-1"
                    @click="openPayModal(fine)">
                    Pay online
                  </button>
                  <button v-if="fine.status === 'UNPAID' && store.isAdmin" class="btn btn-sm btn-outline-danger me-1"
                    :disabled="waivingId === fine.id" @click="waiveFine(fine)">
                    <span v-if="waivingId === fine.id" class="spinner-border spinner-border-sm me-1"></span>
                    Waive
                  </button>
                  <button class="btn btn-sm btn-outline-secondary" @click="openHistory(fine)">
                    Payment history
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <nav v-if="totalPages > 1" class="d-flex justify-content-center mt-4" aria-label="Fine pages">
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

      <!-- Inline pay-online panel (no Bootstrap JS modal wiring — kept as a
           simple conditional card, consistent with the rest of this app) -->
      <div v-if="payTarget" class="membership-card p-4 mt-4">
        <h2 class="h5 mb-3">Pay fine for "{{ payTarget.book_title }}"</h2>
        <p class="text-mono mb-3">Amount due: \${{ Number(payTarget.amount).toFixed(2) }}</p>

        <div v-if="payError" class="alert alert-danger py-2">{{ payError }}</div>

        <form @submit.prevent="submitPayment">
          <div class="mb-2">
            <label class="form-label text-mono small">Card number</label>
            <input v-model="cardNumber" class="form-control" placeholder="4242 4242 4242 4242" required />
            <div class="form-text">Mock gateway — any number works except one ending in 0002 (always declines).</div>
          </div>
          <div class="d-flex gap-2 mt-2">
            <button type="submit" class="btn btn-primary" :disabled="paying">
              <span v-if="paying" class="spinner-border spinner-border-sm me-1"></span>
              Pay \${{ Number(payTarget.amount).toFixed(2) }}
            </button>
            <button type="button" class="btn btn-outline-secondary" @click="closePayModal">Cancel</button>
          </div>
        </form>
      </div>

      <!-- Payment attempt history panel -->
      <div v-if="historyTarget" class="membership-card p-4 mt-4">
        <div class="d-flex justify-content-between align-items-start">
          <h2 class="h5 mb-3">Payment history for "{{ historyTarget.book_title }}"</h2>
          <button type="button" class="btn-close" aria-label="Close" @click="closeHistory"></button>
        </div>

        <div v-if="historyLoading" class="text-center py-4">
          <div class="spinner-border spinner-border-sm" role="status"></div>
        </div>
        <div v-else-if="historyError" class="alert alert-danger py-2">{{ historyError }}</div>
        <div v-else-if="historyItems.length === 0" class="text-muted small py-2">
          No payment attempts have been made against this fine yet.
        </div>
        <div v-else class="table-responsive">
          <table class="table table-sm align-middle">
            <thead>
              <tr class="text-mono small text-uppercase">
                <th>Date</th>
                <th>Amount</th>
                <th>Method</th>
                <th>Status</th>
                <th>Reference</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in historyItems" :key="p.id">
                <td class="small">{{ new Date(p.created_at).toLocaleString() }}</td>
                <td class="text-mono">\${{ Number(p.amount).toFixed(2) }}</td>
                <td class="small">{{ p.method }}</td>
                <td>
                  <span class="stamp" :class="p.status === 'SUCCEEDED' ? 'stamp-available' : 'stamp-overdue'">{{ p.status }}</span>
                </td>
                <td class="text-mono small">{{ p.provider_reference || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
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
      payTarget: null,
      cardNumber: "",
      paying: false,
      payError: "",
      historyTarget: null,
      historyItems: [],
      historyLoading: false,
      historyError: "",
      waivingId: null,
    };
  },
  computed: {
    store() {
      return store;
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.count / this.pageSize));
    },
    outstandingTotal() {
      return this.results
        .filter((f) => f.status === "UNPAID")
        .reduce((sum, f) => sum + Number(f.amount), 0);
    },
  },
  async created() {
    await this.fetchFines();
  },
  methods: {
    statusClass(status) {
      if (status === "UNPAID") return "stamp-overdue";
      if (status === "PAID") return "stamp-available";
      return "stamp-active"; // WAIVED
    },
    goToPage(p) {
      if (p < 1 || p > this.totalPages) return;
      this.page = p;
      this.fetchFines();
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    async fetchFines() {
      this.loading = true;
      this.error = "";
      try {
        const data = await fines.mine({ page: this.page });
        this.results = data.results ?? data;
        this.count = data.count ?? this.results.length;
      } catch (err) {
        this.error = err instanceof ApiError ? err.detail : "Could not load fines.";
      } finally {
        this.loading = false;
      }
    },
    openPayModal(fine) {
      this.historyTarget = null;
      this.payTarget = fine;
      this.cardNumber = "";
      this.payError = "";
    },
    closePayModal() {
      this.payTarget = null;
      this.payError = "";
    },
    async submitPayment() {
      this.payError = "";
      this.paying = true;
      try {
        await fines.pay(this.payTarget.id, { card_number: this.cardNumber });
        this.payTarget = null;
        await this.fetchFines();
      } catch (err) {
        // 402 Payment Required is the mock gateway's decline response.
        this.payError = err instanceof ApiError ? err.detail : "Payment could not be processed.";
      } finally {
        this.paying = false;
      }
    },
    async waiveFine(fine) {
      if (!confirm(`Waive the \$${Number(fine.amount).toFixed(2)} fine for "${fine.book_title}"?`)) return;
      this.waivingId = fine.id;
      try {
        await fines.waive(fine.id);
        await this.fetchFines();
      } catch (err) {
        this.error = err instanceof ApiError ? err.detail : "Could not waive this fine.";
      } finally {
        this.waivingId = null;
      }
    },
    async openHistory(fine) {
      this.payTarget = null;
      this.historyTarget = fine;
      this.historyItems = [];
      this.historyError = "";
      this.historyLoading = true;
      try {
        this.historyItems = await fines.payments(fine.id);
      } catch (err) {
        this.historyError = err instanceof ApiError ? err.detail : "Could not load payment history.";
      } finally {
        this.historyLoading = false;
      }
    },
    closeHistory() {
      this.historyTarget = null;
    },
  },
};

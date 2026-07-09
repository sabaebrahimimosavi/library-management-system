import { dashboard, ApiError } from "../api.js";

export default {
  name: "AdminDashboardView",
  template: /* html */ `
    <div class="container pb-5">
      <p class="eyebrow mb-1">Librarian's desk</p>
      <h1 class="display-heading mb-4">Admin dashboard</h1>

      <ul class="nav nav-tabs mb-4">
        <li class="nav-item" v-for="t in tabs" :key="t.key">
          <button class="nav-link" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">
            {{ t.label }}
          </button>
        </li>
      </ul>

      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border" role="status"></div>
      </div>

      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

      <div v-else>
        <!-- Overview -->
        <div v-show="activeTab === 'overview'" class="row g-3">
          <div class="col-6 col-lg-3" v-for="card in statCards" :key="card.label">
            <div class="card book-card p-3 h-100">
              <p class="call-number mb-1">{{ card.label }}</p>
              <p class="display-heading h3 mb-0">{{ card.value }}</p>
            </div>
          </div>
        </div>

        <!-- Most borrowed books -->
        <div v-show="activeTab === 'borrowed'" class="table-responsive">
          <table class="table align-middle">
            <thead><tr class="text-mono small text-uppercase"><th>Book</th><th>Loans</th></tr></thead>
            <tbody>
              <tr v-for="b in mostBorrowed" :key="b.id">
                <td><router-link :to="'/books/' + b.id">{{ b.title }}</router-link></td>
                <td class="text-mono">{{ b.loan_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Most active users -->
        <div v-show="activeTab === 'active-users'" class="table-responsive">
          <table class="table align-middle">
            <thead><tr class="text-mono small text-uppercase"><th>Member</th><th>Email</th><th>Loans</th></tr></thead>
            <tbody>
              <tr v-for="u in mostActiveUsers" :key="u.id">
                <td class="text-mono">{{ u.username }}</td>
                <td class="small">{{ u.email }}</td>
                <td class="text-mono">{{ u.loan_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Overdue users -->
        <div v-show="activeTab === 'overdue'" class="table-responsive">
          <table class="table align-middle">
            <thead>
              <tr class="text-mono small text-uppercase">
                <th>Member</th><th>Email</th><th>Overdue loans</th><th>Outstanding fines</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in overdueUsers" :key="u.id">
                <td class="text-mono">{{ u.username }}</td>
                <td class="small">{{ u.email }}</td>
                <td><span class="stamp stamp-overdue">{{ u.overdue_loans }}</span></td>
                <td class="text-mono">\${{ u.outstanding_fines != null ? Number(u.outstanding_fines).toFixed(2) : '0.00' }}</td>
              </tr>
              <tr v-if="overdueUsers.length === 0"><td colspan="4" class="text-center text-muted py-4">No members currently overdue.</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Monthly borrowing -->
        <div v-show="activeTab === 'monthly'" class="table-responsive">
          <table class="table align-middle">
            <thead><tr class="text-mono small text-uppercase"><th>Month</th><th>Loans</th></tr></thead>
            <tbody>
              <tr v-for="m in monthlyBorrowing" :key="m.month">
                <td class="text-mono">{{ formatMonth(m.month) }}</td>
                <td>
                  <div class="d-flex align-items-center gap-2">
                    <div class="bg-primary" :style="{ height: '10px', width: barWidth(m.count) + 'px' }"></div>
                    <span class="text-mono small">{{ m.count }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Popular books -->
        <div v-show="activeTab === 'popular'" class="table-responsive">
          <table class="table align-middle">
            <thead><tr class="text-mono small text-uppercase"><th>Book</th><th>Avg rating</th><th>Reviews</th></tr></thead>
            <tbody>
              <tr v-for="b in popularBooks" :key="b.id">
                <td><router-link :to="'/books/' + b.id">{{ b.title }}</router-link></td>
                <td>
                  <span v-if="b.average_rating" class="text-mono">
                    <i class="bi bi-star-fill" style="color: var(--brass)"></i> {{ b.average_rating.toFixed(2) }}
                  </span>
                  <span v-else class="text-muted small">No ratings</span>
                </td>
                <td class="text-mono">{{ b.review_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      loading: true,
      error: "",
      activeTab: "overview",
      tabs: [
        { key: "overview", label: "Overview" },
        { key: "borrowed", label: "Most borrowed" },
        { key: "active-users", label: "Most active members" },
        { key: "overdue", label: "Overdue members" },
        { key: "monthly", label: "Monthly borrowing" },
        { key: "popular", label: "Popular books" },
      ],
      stats: null,
      mostBorrowed: [],
      mostActiveUsers: [],
      overdueUsers: [],
      monthlyBorrowing: [],
      popularBooks: [],
    };
  },
  computed: {
    statCards() {
      if (!this.stats) return [];
      const s = this.stats;
      return [
        { label: "Total books", value: s.total_books },
        { label: "Available copies", value: s.available_books },
        { label: "Total members", value: s.total_users },
        { label: "Active loans", value: s.active_loans },
        { label: "Overdue loans", value: s.overdue_loans },
        { label: "Pending reservations", value: s.pending_reservations },
        { label: "Fines collected", value: `$${Number(s.total_fines_collected).toFixed(2)}` },
        { label: "Fines outstanding", value: `$${Number(s.total_fines_outstanding).toFixed(2)}` },
      ];
    },
    maxMonthlyCount() {
      return Math.max(1, ...this.monthlyBorrowing.map((m) => m.count));
    },
  },
  async created() {
    await this.loadAll();
  },
  methods: {
    formatMonth(iso) {
      return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "long" });
    },
    barWidth(count) {
      return Math.round((count / this.maxMonthlyCount) * 160) + 4;
    },
    async loadAll() {
      this.loading = true;
      this.error = "";
      try {
        const [stats, borrowed, activeUsers, overdue, monthly, popular] = await Promise.all([
          dashboard.stats(),
          dashboard.mostBorrowed({ page_size: 20 }),
          dashboard.mostActiveUsers({ page_size: 20 }),
          dashboard.overdueUsers({ page_size: 100 }),
          dashboard.monthlyBorrowing({ page_size: 100 }),
          dashboard.popularBooks({ page_size: 20 }),
        ]);
        this.stats = stats;
        this.mostBorrowed = (borrowed.results ?? borrowed).slice(0, 20);
        this.mostActiveUsers = (activeUsers.results ?? activeUsers).slice(0, 20);
        this.overdueUsers = overdue.results ?? overdue;
        this.monthlyBorrowing = monthly.results ?? monthly;
        this.popularBooks = (popular.results ?? popular).slice(0, 20);
      } catch (err) {
        this.error = err instanceof ApiError ? err.detail : "Could not load dashboard data.";
      } finally {
        this.loading = false;
      }
    },
  },
};

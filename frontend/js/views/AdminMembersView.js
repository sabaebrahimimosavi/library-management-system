import { store } from "../store.js";
import { members, ApiError } from "../api.js";

export default {
  name: "AdminMembersView",
  template: /* html */ `
    <div class="container pb-5">
      <p class="eyebrow mb-1">Membership office</p>
      <h1 class="display-heading mb-4">Members</h1>

      <div class="row g-2 mb-4">
        <div class="col-12 col-md-6">
          <input v-model="search" @input="debouncedSearch" class="form-control"
            placeholder="Search by name, username or email&hellip;" />
        </div>
        <div class="col-6 col-md-3">
          <select v-model="roleFilter" @change="fetchMembers(1)" class="form-select">
            <option value="">All roles</option>
            <option value="ADMIN">Administrators</option>
            <option value="MEMBER">Members</option>
          </select>
        </div>
      </div>

      <div v-if="notice" class="alert py-2" :class="notice.ok ? 'alert-success' : 'alert-danger'">{{ notice.text }}</div>

      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border" role="status"></div>
      </div>

      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

      <div v-else>
        <div v-if="results.length === 0" class="text-center py-5">
          <p class="fs-5">No members match that search.</p>
        </div>

        <div v-else class="table-responsive">
          <table class="table align-middle">
            <thead>
              <tr class="text-mono small text-uppercase">
                <th>Username</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Joined</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in results" :key="u.id">
                <td class="text-mono">{{ u.username }}</td>
                <td>{{ (u.first_name || u.last_name) ? (u.first_name + ' ' + u.last_name) : '—' }}</td>
                <td class="small">{{ u.email }}</td>
                <td><span class="stamp" :class="u.role === 'ADMIN' ? 'stamp-active' : 'stamp-available'">{{ u.role }}</span></td>
                <td class="small">{{ formatDate(u.date_joined) }}</td>
                <td class="text-end">
                  <button v-if="u.id === store.user?.id" class="btn btn-sm btn-outline-secondary" disabled
                    title="You can't change your own role">You</button>
                  <button v-else class="btn btn-sm" :class="u.role === 'ADMIN' ? 'btn-outline-secondary' : 'btn-outline-primary'"
                    :disabled="savingId === u.id" @click="toggleRole(u)">
                    <span v-if="savingId === u.id" class="spinner-border spinner-border-sm me-1"></span>
                    {{ u.role === 'ADMIN' ? 'Demote to member' : 'Promote to admin' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <nav v-if="totalPages > 1" class="d-flex justify-content-center mt-4" aria-label="Member pages">
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
      search: "",
      roleFilter: "",
      loading: true,
      error: "",
      savingId: null,
      notice: null,
      _searchTimer: null,
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
    await this.fetchMembers();
  },
  methods: {
    formatDate(d) {
      if (!d) return "—";
      return new Date(d).toLocaleDateString();
    },
    debouncedSearch() {
      clearTimeout(this._searchTimer);
      this._searchTimer = setTimeout(() => this.fetchMembers(1), 350);
    },
    goToPage(p) {
      if (p < 1 || p > this.totalPages) return;
      this.fetchMembers(p);
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    async fetchMembers(page = this.page) {
      this.page = page;
      this.loading = true;
      this.error = "";
      try {
        const data = await members.list({
          page: this.page,
          search: this.search || undefined,
          role: this.roleFilter || undefined,
        });
        this.results = data.results ?? data;
        this.count = data.count ?? this.results.length;
      } catch (err) {
        this.error = err instanceof ApiError ? err.detail : "Could not load members.";
      } finally {
        this.loading = false;
      }
    },
    async toggleRole(u) {
      const nextRole = u.role === "ADMIN" ? "MEMBER" : "ADMIN";
      const verb = nextRole === "ADMIN" ? "promote" : "demote";
      if (!confirm(`Really ${verb} ${u.username} to ${nextRole}?`)) return;

      this.savingId = u.id;
      this.notice = null;
      try {
        const updated = await members.updateRole(u.id, nextRole);
        const idx = this.results.findIndex((r) => r.id === u.id);
        if (idx !== -1) this.results[idx] = updated;
        this.notice = { ok: true, text: `${u.username} is now ${nextRole === "ADMIN" ? "an administrator" : "a member"}.` };
      } catch (err) {
        this.notice = { ok: false, text: err instanceof ApiError ? err.detail : "Could not update role." };
      } finally {
        this.savingId = null;
      }
    },
  },
};

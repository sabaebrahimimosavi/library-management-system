import { books } from "../api.js";

export default {
  name: "BookListView",
  template: /* html */ `
    <div class="container pb-5">
      <div class="mb-4">
        <p class="eyebrow mb-1">Card catalog</p>
        <h1 class="display-heading">Browse the collection</h1>
      </div>

      <div class="drawer-bar row g-3 align-items-end mb-4">
        <div class="col-12 col-md-4">
          <label class="form-label" for="search">Search title / author / ISBN</label>
          <input id="search" v-model="filters.search" @input="onFilterChange"
            type="text" class="form-control" placeholder="e.g. Orwell, 1984, 978..." />
        </div>
        <div class="col-6 col-md-2">
          <label class="form-label" for="genre">Genre</label>
          <select id="genre" v-model="filters.genre" @change="onFilterChange" class="form-select">
            <option value="">All</option>
            <option v-for="g in genres" :key="g.id" :value="g.id">{{ g.name }}</option>
          </select>
        </div>
        <div class="col-6 col-md-3">
          <label class="form-label" for="author">Author</label>
          <select id="author" v-model="filters.author" @change="onFilterChange" class="form-select">
            <option value="">All</option>
            <option v-for="a in authors" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
        </div>
        <div class="col-6 col-md-2">
          <label class="form-label" for="year">Year</label>
          <input id="year" v-model="filters.publication_year" @input="onFilterChange"
            type="number" class="form-control" placeholder="Any" />
        </div>
        <div class="col-6 col-md-1">
          <label class="form-label" for="ordering">Sort</label>
          <select id="ordering" v-model="filters.ordering" @change="onFilterChange" class="form-select">
            <option value="title">Title</option>
            <option value="-publication_year">Newest</option>
            <option value="publication_year">Oldest</option>
          </select>
        </div>
      </div>

      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border" role="status"></div>
      </div>

      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

      <div v-else>
        <p class="text-mono small text-muted mb-3">{{ count }} title{{ count === 1 ? '' : 's' }} found</p>

        <div v-if="results.length === 0" class="text-center py-5">
          <p class="fs-5">No books match that search.</p>
          <p class="text-muted">Try clearing a filter — the shelf might just be organized differently.</p>
        </div>

        <div class="row g-3">
          <div class="col-12 col-sm-6 col-lg-4 col-xl-3" v-for="book in results" :key="book.id">
            <router-link :to="'/books/' + book.id" class="text-decoration-none">
              <div class="card book-card p-3">
                <img v-if="book.cover_image" :src="book.cover_image" class="mb-2 rounded" style="width:100%;height:140px;object-fit:cover" />
                <p class="call-number mb-1">ISBN {{ book.isbn }} &middot; {{ book.publication_year }}</p>
                <h2 class="book-title h5 mb-1">{{ book.title }}</h2>
                <p class="small text-muted mb-2">{{ book.author_name }}</p>
                <div class="d-flex justify-content-between align-items-center mt-auto">
                  <span class="stamp" :class="book.available_copies > 0 ? 'stamp-available' : 'stamp-unavailable'">
                    {{ book.available_copies > 0 ? 'Available' : 'All checked out' }}
                  </span>
                  <span v-if="book.average_rating" class="small text-mono">
                    <i class="bi bi-star-fill" style="color: var(--brass)"></i> {{ book.average_rating }}
                  </span>
                </div>
              </div>
            </router-link>
          </div>
        </div>

        <nav v-if="totalPages > 1" class="d-flex justify-content-center mt-4" aria-label="Catalog pages">
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
      authors: [],
      genres: [],
      filters: {
        search: "",
        genre: "",
        author: "",
        publication_year: "",
        ordering: "title",
      },
      _debounce: null,
    };
  },
  computed: {
    totalPages() {
      return Math.max(1, Math.ceil(this.count / this.pageSize));
    },
  },
  async created() {
    this.loadFilterOptions();
    await this.fetchBooks();
  },
  methods: {
    async loadFilterOptions() {
      try {
        const [a, g] = await Promise.all([books.authors({ page_size: 200 }), books.genres({ page_size: 200 })]);
        this.authors = a.results ?? a;
        this.genres = g.results ?? g;
      } catch {
        // Filter dropdowns are a nice-to-have; catalog still works without them.
      }
    },
    onFilterChange() {
      clearTimeout(this._debounce);
      this._debounce = setTimeout(() => {
        this.page = 1;
        this.fetchBooks();
      }, 300);
    },
    goToPage(p) {
      if (p < 1 || p > this.totalPages) return;
      this.page = p;
      this.fetchBooks();
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    async fetchBooks() {
      this.loading = true;
      this.error = "";
      try {
        const params = { ...this.filters, page: this.page };
        const data = await books.list(params);
        this.results = data.results ?? data;
        this.count = data.count ?? this.results.length;
      } catch (err) {
        this.error = err.detail || "Could not load the catalog.";
      } finally {
        this.loading = false;
      }
    },
  },
};

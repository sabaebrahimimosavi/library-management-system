import { books } from "../api.js";

export default {
  name: "BookListView",

  template: /* html */ `
    <div class="container pb-5">
      <div class="mb-4">
        <p class="eyebrow mb-1">Card catalog</p>
        <h1 class="display-heading">Browse the collection</h1>
      </div>

      <!-- Filters -->
      <div class="drawer-bar row g-3 align-items-end mb-4">
        <div class="col-12 col-md-4">
          <label class="form-label" for="search">
            Search title / author / ISBN
          </label>

          <input
            id="search"
            v-model="filters.search"
            @input="onFilterChange"
            type="text"
            class="form-control"
            placeholder="e.g. Orwell, 1984, 978..."
          />
        </div>

        <div class="col-6 col-md-2">
          <label class="form-label" for="genre">
            Genre
          </label>

          <select
            id="genre"
            v-model="filters.genre"
            @change="onFilterChange"
            class="form-select"
          >
            <option value="">All</option>

            <option
              v-for="genre in genres"
              :key="genre.id"
              :value="String(genre.id)"
            >
              {{ genre.name }}
            </option>
          </select>
        </div>

        <div class="col-6 col-md-3">
          <label class="form-label" for="author">
            Author
          </label>

          <select
            id="author"
            v-model="filters.author"
            @change="onFilterChange"
            class="form-select"
          >
            <option value="">All</option>

            <option
              v-for="author in authors"
              :key="author.id"
              :value="String(author.id)"
            >
              {{ author.name }}
            </option>
          </select>
        </div>

        <div class="col-6 col-md-2">
          <label class="form-label" for="year">
            Year
          </label>

          <input
            id="year"
            v-model="filters.publication_year"
            @input="onFilterChange"
            type="number"
            class="form-control"
            placeholder="Any"
          />
        </div>

        <div class="col-6 col-md-1">
          <label class="form-label" for="ordering">
            Sort
          </label>

          <select
            id="ordering"
            v-model="filters.ordering"
            @change="onFilterChange"
            class="form-select"
          >
            <option value="title">Title</option>
            <option value="-publication_year">Newest</option>
            <option value="publication_year">Oldest</option>
          </select>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">
            Loading books...
          </span>
        </div>
      </div>

      <!-- Error -->
      <div
        v-else-if="error"
        class="alert alert-danger"
      >
        {{ error }}
      </div>

      <!-- Results -->
      <div v-else>
        <p class="text-mono small text-muted mb-3">
          {{ count }}
          title{{ count === 1 ? '' : 's' }}
          found
        </p>

        <!-- No results -->
        <div
          v-if="results.length === 0"
          class="text-center py-5"
        >
          <p class="fs-5">
            No books match that search.
          </p>

          <p class="text-muted">
            Try clearing a filter — the shelf might
            just be organized differently.
          </p>
        </div>

        <!-- Book cards -->
        <div class="row g-3">
          <div
            v-for="book in results"
            :key="book.id"
            class="col-12 col-sm-6 col-lg-4 col-xl-3"
          >
            <router-link
              :to="bookDetailRoute(book.id)"
              class="text-decoration-none"
            >
              <div class="card book-card p-3 h-100">
                <img
                  v-if="book.cover_image"
                  :src="book.cover_image"
                  :alt="book.title + ' cover'"
                  loading="lazy"
                  decoding="async"
                  class="mb-2 rounded"
                  style="
                    width: 100%;
                    height: 140px;
                    object-fit: cover;
                  "
                />

                <p class="call-number mb-1">
                  ISBN {{ book.isbn }}
                  &middot;
                  {{ book.publication_year }}

                  <span v-if="book.pages">
                    &middot;
                    {{ book.pages }} pages
                  </span>
                </p>

                <h2 class="book-title h5 mb-1">
                  {{ book.title }}
                </h2>

                <p class="small text-muted mb-2">
                  {{ book.author_name }}
                </p>

                <div
                  class="
                    d-flex
                    justify-content-between
                    align-items-center
                    mt-auto
                  "
                >
                  <span
                    class="stamp"
                    :class="
                      book.available_copies > 0
                        ? 'stamp-available'
                        : 'stamp-unavailable'
                    "
                  >
                    {{
                      book.available_copies > 0
                        ? 'Available'
                        : 'All checked out'
                    }}
                  </span>

                  <span
                    v-if="
                      book.average_rating !== null &&
                      book.average_rating !== undefined
                    "
                    class="small text-mono"
                  >
                    <i
                      class="bi bi-star-fill"
                      style="color: var(--brass)"
                    ></i>

                    {{ book.average_rating }}
                  </span>
                </div>
              </div>
            </router-link>
          </div>
        </div>

        <!-- Pagination -->
        <nav
          v-if="totalPages > 1"
          class="d-flex justify-content-center mt-4"
          aria-label="Catalog pages"
        >
          <div
            class="d-flex align-items-center gap-2 flex-wrap justify-content-center"
          >
            <button
              type="button"
              class="btn btn-outline-primary"
              :disabled="page <= 1"
              @click="goToPage(page - 1)"
            >
              Previous
            </button>

            <div class="d-flex align-items-center gap-2">
              <span class="text-mono">Page</span>

              <input
                v-model.number="jumpPage"
                type="number"
                class="form-control text-center"
                style="width: 85px"
                min="1"
                :max="totalPages"
                aria-label="Page number"
                @keyup.enter="goToTypedPage"
              />

              <span class="text-mono">
                / {{ totalPages }}
              </span>

              <button
                type="button"
                class="btn btn-outline-secondary"
                @click="goToTypedPage"
              >
                Go
              </button>
            </div>

            <button
              type="button"
              class="btn btn-outline-primary"
              :disabled="page >= totalPages"
              @click="goToPage(page + 1)"
            >
              Next
            </button>
          </div>
        </nav>
      </div>
    </div>
  `,

  data() {
    return {
      results: [],
      count: 0,

      page: 1,
      jumpPage: 1,
      pageSize: 20,

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
      _bookRequestId: 0,
    };
  },

  computed: {
    totalPages() {
      return Math.max(
        1,
        Math.ceil(this.count / this.pageSize)
      );
    },
  },

  async created() {
    this.restoreCatalogState();

    // Load dropdown options separately.
    // A failure here will not stop the books request.
    this.loadFilterOptions();

    await this.fetchBooks();
  },

  beforeUnmount() {
    clearTimeout(this._debounce);
  },

  methods: {
    /*
     * Restore the catalog page and filters
     * from the URL.
     *
     * Example:
     * /books?page=3&genre=2
     */
    restoreCatalogState() {
      const query = this.$route.query;

      const parsedPage = Number.parseInt(
        query.page,
        10
      );

      this.page =
        Number.isInteger(parsedPage) &&
        parsedPage > 0
          ? parsedPage
          : 1;

      this.jumpPage = this.page;

      this.filters.search =
        typeof query.search === "string"
          ? query.search
          : "";

      this.filters.genre =
        typeof query.genre === "string"
          ? query.genre
          : "";

      this.filters.author =
        typeof query.author === "string"
          ? query.author
          : "";

      this.filters.publication_year =
        typeof query.publication_year === "string"
          ? query.publication_year
          : "";

      this.filters.ordering = [
        "title",
        "-publication_year",
        "publication_year",
      ].includes(query.ordering)
        ? query.ordering
        : "title";
    },

    /*
     * Create the catalog query parameters
     * that will be stored in the URL.
     */
    catalogQuery() {
      const query = {};

      if (this.page > 1) {
        query.page = String(this.page);
      }

      if (this.filters.search) {
        query.search =
          this.filters.search;
      }

      if (this.filters.genre) {
        query.genre = String(
          this.filters.genre
        );
      }

      if (this.filters.author) {
        query.author = String(
          this.filters.author
        );
      }

      if (this.filters.publication_year) {
        query.publication_year = String(
          this.filters.publication_year
        );
      }

      if (
        this.filters.ordering !== "title"
      ) {
        query.ordering =
          this.filters.ordering;
      }

      return query;
    },

    /*
     * Update the catalog URL without
     * reloading the entire browser page.
     */
    syncCatalogRoute() {
      return this.$router.replace({
        name: "books",
        query: this.catalogQuery(),
      });
    },

    /*
     * Add the current catalog URL to the
     * book detail link.
     *
     * This allows the Back button to return
     * to the previous catalog page.
     */
    bookDetailRoute(bookId) {
      return {
        name: "book-detail",

        params: {
          id: bookId,
        },

        query: {
          from: this.$route.fullPath,
        },
      };
    },

    /*
     * Load authors and genres for filters.
     */
    async loadFilterOptions() {
      try {
        const [
          authorData,
          genreData,
        ] = await Promise.all([
          books.authors({
            page_size: 200,
          }),

          books.genres({
            page_size: 200,
          }),
        ]);

        this.authors =
          authorData.results ??
          authorData;

        this.genres =
          genreData.results ??
          genreData;
      } catch (error) {
        console.warn(
          "Could not load catalog filter options:",
          error
        );
      }
    },

    /*
     * Wait 300 ms before requesting books
     * while the user is typing.
     */
    onFilterChange() {
      clearTimeout(this._debounce);

      this._debounce = setTimeout(
        async () => {
          this.page = 1;

          await this.syncCatalogRoute();
          await this.fetchBooks();
        },
        300
      );
    },

    /*
     * Go to another catalog page.
     */
    async goToPage(newPage) {
      const targetPage = Number.parseInt(
        newPage,
        10
      );

      if (
        !Number.isInteger(targetPage) ||
        targetPage < 1 ||
        targetPage > this.totalPages
      ) {
        this.jumpPage = this.page;
        return;
      }

      if (targetPage === this.page) {
        this.jumpPage = this.page;
        return;
      }

      this.page = targetPage;
      this.jumpPage = targetPage;

      await this.syncCatalogRoute();
      await this.fetchBooks();

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    },

    async goToTypedPage() {
        const requestedPage = Number.parseInt(
          this.jumpPage,
          10
        );

        if (
          !Number.isInteger(requestedPage) ||
          requestedPage < 1 ||
          requestedPage > this.totalPages
        ) {
          this.jumpPage = this.page;
          return;
        }

        await this.goToPage(requestedPage);
      },

    /*
     * Request one page of books.
     *
     * Only 20 books are requested,
     * even when the database has 500 books.
     */
    async fetchBooks() {
      const requestId =
        ++this._bookRequestId;

      this.loading = true;
      this.error = "";

      try {
        const params = {
          ...this.filters,

          page: this.page,

          page_size:
            this.pageSize,
        };

        const data =
          await books.list(params);

        /*
         * Ignore an outdated request when
         * a newer request has already started.
         */
        if (
          requestId !==
          this._bookRequestId
        ) {
          return;
        }

        this.results =
          Array.isArray(data)
            ? data
            : data.results ?? [];

        this.count =
          Array.isArray(data)
            ? data.length
            : data.count ??
              this.results.length;

        /*
         * Handle a URL containing a page
         * greater than the last available page.
         */
        const lastPage = Math.max(
          1,
          Math.ceil(
            this.count /
              this.pageSize
          )
        );

        if (this.page > lastPage) {
          this.page = lastPage;

          await this.syncCatalogRoute();
          await this.fetchBooks();
        }
      } catch (error) {
        /*
         * Ignore an error from an old request
         * when a newer request is active.
         */
        if (
          requestId !==
          this._bookRequestId
        ) {
          return;
        }

        console.error(
          "Could not load catalog:",
          error
        );

        this.results = [];
        this.count = 0;

        this.error =
          error.detail ||
          "Could not load the catalog.";
      } finally {
        if (
          requestId ===
          this._bookRequestId
        ) {
          this.loading = false;
        }
      }
    },
  },
};
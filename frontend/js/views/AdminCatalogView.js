import { books, ApiError } from "../api.js";

const emptyBookForm = () => ({
  id: null,
  title: "",
  isbn: "",
  publication_year: new Date().getFullYear(),
  description: "",
  copies: 1,
  available_copies: 1,
  author: "",
  genre: "",
  publisher: "",
});

export default {
  name: "AdminCatalogView",
  template: /* html */ `
    <div class="container pb-5">
      <p class="eyebrow mb-1">Cataloging room</p>
      <h1 class="display-heading mb-4">Catalog manager</h1>

      <ul class="nav nav-tabs mb-4">
        <li class="nav-item" v-for="t in tabs" :key="t.key">
          <button class="nav-link" :class="{ active: activeTab === t.key }" @click="switchTab(t.key)">
            {{ t.label }}
          </button>
        </li>
      </ul>

      <div v-if="notice" class="alert py-2" :class="notice.ok ? 'alert-success' : 'alert-danger'">{{ notice.text }}</div>

      <!-- ============ BOOKS ============ -->
      <div v-show="activeTab === 'books'">
        <button class="btn btn-primary mb-3" @click="startNewBook">
          <i class="bi bi-plus-lg me-1"></i> Add book
        </button>

        <div v-if="bookForm" class="membership-card p-4 mb-4">
          <h2 class="h5 mb-3">{{ bookForm.id ? 'Edit book' : 'New book' }}</h2>
          <div v-if="bookFieldErrors && Object.keys(bookFieldErrors).length" class="alert alert-danger py-2 small">
            Please fix the highlighted fields.
          </div>
          <form @submit.prevent="saveBook">
            <div class="row g-2 mb-2">
              <div class="col-12 col-md-6">
                <label class="form-label text-mono small">Title</label>
                <input v-model="bookForm.title" class="form-control" :class="{ 'is-invalid': bookFieldErrors.title }" required />
                <div class="invalid-feedback">{{ bookFieldErrors.title?.[0] }}</div>
              </div>
              <div class="col-6 col-md-3">
                <label class="form-label text-mono small">ISBN</label>
                <input v-model="bookForm.isbn" class="form-control" :class="{ 'is-invalid': bookFieldErrors.isbn }" required />
                <div class="invalid-feedback">{{ bookFieldErrors.isbn?.[0] }}</div>
              </div>
              <div class="col-6 col-md-3">
                <label class="form-label text-mono small">Publication year</label>
                <input v-model.number="bookForm.publication_year" type="number" class="form-control"
                  :class="{ 'is-invalid': bookFieldErrors.publication_year }" required />
                <div class="invalid-feedback">{{ bookFieldErrors.publication_year?.[0] }}</div>
              </div>
            </div>

            <div class="row g-2 mb-2">
              <div class="col-12 col-md-4">
                <label class="form-label text-mono small">Author</label>
                <select v-model="bookForm.author" class="form-select" :class="{ 'is-invalid': bookFieldErrors.author }" required>
                  <option value="" disabled>Select author</option>
                  <option v-for="a in authors" :key="a.id" :value="a.id">{{ a.name }}</option>
                </select>
                <div class="invalid-feedback">{{ bookFieldErrors.author?.[0] }}</div>
              </div>
              <div class="col-12 col-md-4">
                <label class="form-label text-mono small">Genre</label>
                <select v-model="bookForm.genre" class="form-select" :class="{ 'is-invalid': bookFieldErrors.genre }" required>
                  <option value="" disabled>Select genre</option>
                  <option v-for="g in genres" :key="g.id" :value="g.id">{{ g.name }}</option>
                </select>
                <div class="invalid-feedback">{{ bookFieldErrors.genre?.[0] }}</div>
              </div>
              <div class="col-12 col-md-4">
                <label class="form-label text-mono small">Publisher</label>
                <select v-model="bookForm.publisher" class="form-select" :class="{ 'is-invalid': bookFieldErrors.publisher }" required>
                  <option value="" disabled>Select publisher</option>
                  <option v-for="p in publishers" :key="p.id" :value="p.id">{{ p.name }}</option>
                </select>
                <div class="invalid-feedback">{{ bookFieldErrors.publisher?.[0] }}</div>
              </div>
            </div>

            <div class="row g-2 mb-2">
              <div class="col-6 col-md-3">
                <label class="form-label text-mono small">Total copies</label>
                <input v-model.number="bookForm.copies" type="number" min="0" class="form-control"
                  :class="{ 'is-invalid': bookFieldErrors.copies }" required />
                <div class="invalid-feedback">{{ bookFieldErrors.copies?.[0] }}</div>
              </div>
              <div class="col-6 col-md-3">
                <label class="form-label text-mono small">Available copies</label>
                <input v-model.number="bookForm.available_copies" type="number" min="0" class="form-control"
                  :class="{ 'is-invalid': bookFieldErrors.available_copies }" required />
                <div class="invalid-feedback">{{ bookFieldErrors.available_copies?.[0] }}</div>
              </div>
              <div class="col-12 col-md-6">
                <label class="form-label text-mono small">Cover image</label>
                <input type="file" accept="image/*" class="form-control" @change="onCoverChange" />
                <div class="invalid-feedback d-block" v-if="bookFieldErrors.cover_image">{{ bookFieldErrors.cover_image?.[0] }}</div>
                <img v-if="coverPreview" :src="coverPreview" class="mt-2 rounded" style="max-height:80px" />
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label text-mono small">Description</label>
              <textarea v-model="bookForm.description" class="form-control" rows="2"></textarea>
            </div>

            <div class="d-flex gap-2">
              <button type="submit" class="btn btn-primary" :disabled="savingBook">
                <span v-if="savingBook" class="spinner-border spinner-border-sm me-1"></span>
                {{ bookForm.id ? 'Save changes' : 'Create book' }}
              </button>
              <button type="button" class="btn btn-outline-secondary" @click="cancelBookForm">Cancel</button>
            </div>
          </form>
        </div>

        <div v-if="loadingBooks" class="text-center py-5"><div class="spinner-border" role="status"></div></div>
        <div v-else class="table-responsive">
          <table class="table align-middle">
            <thead>
              <tr class="text-mono small text-uppercase">
                <th>Cover</th><th>Title</th><th>Author</th><th>Genre</th><th>Copies</th><th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in bookList" :key="b.id">
                <td>
                  <img v-if="b.cover_image" :src="b.cover_image" style="width:40px;height:56px;object-fit:cover" class="rounded" />
                  <span v-else class="text-muted small">—</span>
                </td>
                <td><router-link :to="'/books/' + b.id">{{ b.title }}</router-link></td>
                <td class="small">{{ b.author_name }}</td>
                <td class="small">{{ b.genre_name }}</td>
                <td class="text-mono small">{{ b.available_copies }} / {{ b.copies }}</td>
                <td class="text-end">
                  <button class="btn btn-sm btn-outline-primary me-1" @click="editBook(b)">Edit</button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteBook(b)">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <nav v-if="bookTotalPages > 1" class="d-flex justify-content-center mt-3">
          <ul class="pagination">
            <li class="page-item" :class="{ disabled: bookPage <= 1 }">
              <button class="page-link" @click="goToBookPage(bookPage - 1)">Previous</button>
            </li>
            <li class="page-item disabled"><span class="page-link text-mono">{{ bookPage }} / {{ bookTotalPages }}</span></li>
            <li class="page-item" :class="{ disabled: bookPage >= bookTotalPages }">
              <button class="page-link" @click="goToBookPage(bookPage + 1)">Next</button>
            </li>
          </ul>
        </nav>
      </div>

      <!-- ============ AUTHORS / GENRES / PUBLISHERS (shared layout) ============ -->
      <div v-for="res in ['authors', 'genres', 'publishers']" :key="res" v-show="activeTab === res">
        <button class="btn btn-primary mb-3" @click="startNewSimple(res)">
          <i class="bi bi-plus-lg me-1"></i> Add {{ singular(res) }}
        </button>

        <div v-if="simpleForm && simpleForm.resource === res" class="membership-card p-4 mb-4">
          <h2 class="h5 mb-3">{{ simpleForm.id ? 'Edit' : 'New' }} {{ singular(res) }}</h2>
          <form @submit.prevent="saveSimple(res)">
            <div class="mb-2">
              <label class="form-label text-mono small">Name</label>
              <input v-model="simpleForm.name" class="form-control"
                :class="{ 'is-invalid': simpleFieldErrors.name }" required />
              <div class="invalid-feedback">{{ simpleFieldErrors.name?.[0] }}</div>
            </div>

            <template v-if="res === 'authors'">
              <div class="mb-2">
                <label class="form-label text-mono small">Biography</label>
                <textarea v-model="simpleForm.biography" class="form-control" rows="2"></textarea>
              </div>
              <div class="row g-2">
                <div class="col-6">
                  <label class="form-label text-mono small">Birth date</label>
                  <input v-model="simpleForm.birth_date" type="date" class="form-control" />
                </div>
                <div class="col-6">
                  <label class="form-label text-mono small">Nationality</label>
                  <input v-model="simpleForm.nationality" class="form-control" />
                </div>
              </div>
            </template>

            <template v-if="res === 'genres'">
              <div class="mb-2">
                <label class="form-label text-mono small">Description</label>
                <textarea v-model="simpleForm.description" class="form-control" rows="2"></textarea>
              </div>
            </template>

            <template v-if="res === 'publishers'">
              <div class="row g-2 mb-2">
                <div class="col-6"><label class="form-label text-mono small">Website</label>
                  <input v-model="simpleForm.website" class="form-control" /></div>
                <div class="col-6"><label class="form-label text-mono small">Email</label>
                  <input v-model="simpleForm.email" type="email" class="form-control" /></div>
              </div>
              <div class="row g-2 mb-2">
                <div class="col-6"><label class="form-label text-mono small">Phone</label>
                  <input v-model="simpleForm.phone" class="form-control" /></div>
                <div class="col-6"><label class="form-label text-mono small">Address</label>
                  <input v-model="simpleForm.address" class="form-control" /></div>
              </div>
            </template>

            <div class="d-flex gap-2 mt-2">
              <button type="submit" class="btn btn-primary" :disabled="savingSimple">
                <span v-if="savingSimple" class="spinner-border spinner-border-sm me-1"></span>
                {{ simpleForm.id ? 'Save changes' : 'Create' }}
              </button>
              <button type="button" class="btn btn-outline-secondary" @click="simpleForm = null">Cancel</button>
            </div>
          </form>
        </div>

        <div v-if="simpleLoading[res]" class="text-center py-5"><div class="spinner-border" role="status"></div></div>
        <div v-else class="table-responsive">
          <table class="table align-middle">
            <thead><tr class="text-mono small text-uppercase"><th>Name</th><th></th></tr></thead>
            <tbody>
              <tr v-for="item in simpleLists[res]" :key="item.id">
                <td>{{ item.name }}</td>
                <td class="text-end">
                  <button class="btn btn-sm btn-outline-primary me-1" @click="editSimple(res, item)">Edit</button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteSimple(res, item)">Delete</button>
                </td>
              </tr>
              <tr v-if="simpleLists[res].length === 0">
                <td colspan="2" class="text-center text-muted py-4">None yet.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      activeTab: "books",
      tabs: [
        { key: "books", label: "Books" },
        { key: "authors", label: "Authors" },
        { key: "genres", label: "Genres" },
        { key: "publishers", label: "Publishers" },
      ],
      notice: null,

      // Books
      bookList: [],
      bookCount: 0,
      bookPage: 1,
      bookPageSize: 10,
      loadingBooks: true,
      bookForm: null,
      bookFieldErrors: {},
      savingBook: false,
      coverFile: null,
      coverPreview: "",

      // Lookup lists used by the book form's selects
      authors: [],
      genres: [],
      publishers: [],

      // Shared authors/genres/publishers CRUD state
      simpleLists: { authors: [], genres: [], publishers: [] },
      simpleLoading: { authors: true, genres: true, publishers: true },
      simpleForm: null,
      simpleFieldErrors: {},
      savingSimple: false,
    };
  },
  computed: {
    bookTotalPages() {
      return Math.max(1, Math.ceil(this.bookCount / this.bookPageSize));
    },
  },
  async created() {
    await Promise.all([this.fetchBooks(), this.fetchLookups(), this.fetchSimple("authors"), this.fetchSimple("genres"), this.fetchSimple("publishers")]);
  },
  methods: {
    switchTab(key) {
      this.activeTab = key;
      this.notice = null;
    },
    singular(res) {
      return { authors: "author", genres: "genre", publishers: "publisher" }[res];
    },
    flash(ok, text) {
      this.notice = { ok, text };
      setTimeout(() => {
        if (this.notice && this.notice.text === text) this.notice = null;
      }, 4000);
    },

    // ---------- Books ----------
    async fetchBooks() {
      this.loadingBooks = true;
      try {
        const data = await books.list({ page: this.bookPage, page_size: this.bookPageSize });
        this.bookList = data.results ?? data;
        this.bookCount = data.count ?? this.bookList.length;
      } catch (err) {
        this.flash(false, err instanceof ApiError ? err.detail : "Could not load books.");
      } finally {
        this.loadingBooks = false;
      }
    },
    async fetchLookups() {
      try {
        const [a, g, p] = await Promise.all([
          books.authors({ page_size: 200 }),
          books.genres({ page_size: 200 }),
          books.publishers({ page_size: 200 }),
        ]);
        this.authors = a.results ?? a;
        this.genres = g.results ?? g;
        this.publishers = p.results ?? p;
      } catch {
        // Book form selects will just be empty; the table itself still works.
      }
    },
    goToBookPage(p) {
      if (p < 1 || p > this.bookTotalPages) return;
      this.bookPage = p;
      this.fetchBooks();
    },
    startNewBook() {
      this.bookForm = emptyBookForm();
      this.bookFieldErrors = {};
      this.coverFile = null;
      this.coverPreview = "";
    },
    editBook(b) {
      this.bookForm = {
        id: b.id,
        title: b.title,
        isbn: b.isbn,
        publication_year: b.publication_year,
        description: b.description || "",
        copies: b.copies,
        available_copies: b.available_copies,
        author: b.author,
        genre: b.genre,
        publisher: b.publisher,
      };
      this.bookFieldErrors = {};
      this.coverFile = null;
      this.coverPreview = b.cover_image || "";
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    cancelBookForm() {
      this.bookForm = null;
      this.bookFieldErrors = {};
    },
    onCoverChange(e) {
      const file = e.target.files?.[0];
      this.coverFile = file || null;
      this.coverPreview = file ? URL.createObjectURL(file) : this.coverPreview;
    },
    buildBookPayload() {
      // Only use multipart/FormData when a new cover file was actually
      // picked — plain JSON is simpler and works fine otherwise.
      if (this.coverFile) {
        const fd = new FormData();
        Object.entries(this.bookForm).forEach(([k, v]) => {
          if (k === "id" || v === null || v === undefined) return;
          fd.append(k, v);
        });
        fd.append("cover_image", this.coverFile);
        return fd;
      }
      const { id, ...rest } = this.bookForm;
      return rest;
    },
    async saveBook() {
      this.savingBook = true;
      this.bookFieldErrors = {};
      try {
        const payload = this.buildBookPayload();
        if (this.bookForm.id) {
          await books.update(this.bookForm.id, payload);
          this.flash(true, "Book updated.");
        } else {
          await books.create(payload);
          this.flash(true, "Book created.");
        }
        this.bookForm = null;
        await this.fetchBooks();
      } catch (err) {
        if (err instanceof ApiError && err.status === 400) {
          this.bookFieldErrors = err.fields;
        }
        this.flash(false, err instanceof ApiError ? err.detail : "Could not save this book.");
      } finally {
        this.savingBook = false;
      }
    },
    async deleteBook(b) {
      if (!confirm(`Delete "${b.title}"? This cannot be undone.`)) return;
      try {
        await books.remove(b.id);
        this.flash(true, "Book deleted.");
        await this.fetchBooks();
      } catch (err) {
        this.flash(false, err instanceof ApiError ? err.detail : "Could not delete this book.");
      }
    },

    // ---------- Authors / Genres / Publishers ----------
    apiFor(res) {
      return {
        authors: { create: books.createAuthor, update: books.updateAuthor, remove: books.removeAuthor },
        genres: { create: books.createGenre, update: books.updateGenre, remove: books.removeGenre },
        publishers: { create: books.createPublisher, update: books.updatePublisher, remove: books.removePublisher },
      }[res];
    },
    async fetchSimple(res) {
      this.simpleLoading[res] = true;
      try {
        const fetcher = { authors: books.authors, genres: books.genres, publishers: books.publishers }[res];
        const data = await fetcher({ page_size: 200 });
        this.simpleLists[res] = data.results ?? data;
      } catch (err) {
        this.flash(false, err instanceof ApiError ? err.detail : `Could not load ${res}.`);
      } finally {
        this.simpleLoading[res] = false;
      }
    },
    startNewSimple(res) {
      const base = { resource: res, id: null, name: "" };
      if (res === "authors") Object.assign(base, { biography: "", birth_date: "", nationality: "" });
      if (res === "genres") Object.assign(base, { description: "" });
      if (res === "publishers") Object.assign(base, { website: "", email: "", phone: "", address: "" });
      this.simpleForm = base;
      this.simpleFieldErrors = {};
    },
    editSimple(res, item) {
      this.simpleForm = { resource: res, ...item };
      this.simpleFieldErrors = {};
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    async saveSimple(res) {
      this.savingSimple = true;
      this.simpleFieldErrors = {};
      try {
        const { resource, id, ...payload } = this.simpleForm;
        const api = this.apiFor(res);
        if (id) {
          await api.update(id, payload);
          this.flash(true, `${this.singular(res)} updated.`);
        } else {
          await api.create(payload);
          this.flash(true, `${this.singular(res)} created.`);
        }
        this.simpleForm = null;
        await this.fetchSimple(res);
        await this.fetchLookups();
      } catch (err) {
        if (err instanceof ApiError && err.status === 400) {
          this.simpleFieldErrors = err.fields;
        }
        this.flash(false, err instanceof ApiError ? err.detail : `Could not save this ${this.singular(res)}.`);
      } finally {
        this.savingSimple = false;
      }
    },
    async deleteSimple(res, item) {
      if (!confirm(`Delete "${item.name}"? This cannot be undone.`)) return;
      try {
        await this.apiFor(res).remove(item.id);
        this.flash(true, `${this.singular(res)} deleted.`);
        await this.fetchSimple(res);
        await this.fetchLookups();
      } catch (err) {
        // Likely a 400/409 from Book's on_delete=PROTECT if books still reference it.
        this.flash(false, err instanceof ApiError ? err.detail : `Could not delete this ${this.singular(res)}.`);
      }
    },
  },
};

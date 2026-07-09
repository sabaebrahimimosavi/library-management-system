import { store } from "../store.js";
import { books, reviews, loans, reservations, ApiError } from "../api.js";

export default {
  name: "BookDetailView",
  template: /* html */ `
    <div class="container pb-5" v-if="book">
      <router-link to="/books" class="small text-mono d-inline-block mb-3">&larr; Back to catalog</router-link>

      <div class="row g-4">
        <div class="col-12 col-lg-8">
          <img v-if="book.cover_image" :src="book.cover_image" class="rounded mb-3" style="max-height:280px;object-fit:cover" />
          <p class="call-number mb-1">ISBN {{ book.isbn }} &middot; {{ book.publication_year }}</p>
          <h1 class="display-heading">{{ book.title }}</h1>
          <p class="fs-5 text-muted mb-3">by {{ book.author_name }}</p>

          <div class="d-flex gap-2 flex-wrap mb-3">
            <span class="stamp" :class="book.available_copies > 0 ? 'stamp-available' : 'stamp-unavailable'">
              {{ book.available_copies }} / {{ book.copies }} copies available
            </span>
            <span class="stamp stamp-active">{{ book.genre_name }}</span>
            <span v-if="book.average_rating" class="stamp stamp-returned">
              <i class="bi bi-star-fill"></i> {{ book.average_rating }} ({{ book.review_count }})
            </span>
          </div>

          <p>{{ book.description || 'No description available for this title yet.' }}</p>
          <p class="small text-muted">Publisher: {{ book.publisher_name }}</p>

          <hr class="my-4" />

          <h2 class="h4 mb-3">Member reviews</h2>

          <div v-if="store.isAuthenticated" class="card mb-4 p-3 border-0" style="background: var(--paper-0)">
            <p class="text-mono small mb-2">{{ myReview ? 'Update your review' : 'Write a review' }}</p>
            <div v-if="reviewError" class="alert alert-danger py-2">{{ reviewError }}</div>
            <div class="star-rating mb-2">
              <i v-for="n in 5" :key="n" class="bi fs-4 me-1" role="button"
                :class="n <= reviewForm.rating ? 'bi-star-fill' : 'bi-star'"
                @click="reviewForm.rating = n"></i>
            </div>
            <textarea v-model="reviewForm.comment" class="form-control mb-2" rows="2"
              placeholder="Optional comment"></textarea>
            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-primary" :disabled="!reviewForm.rating || submittingReview"
                @click="submitReview">
                {{ myReview ? 'Update review' : 'Post review' }}
              </button>
              <button v-if="myReview" class="btn btn-sm btn-outline-danger" @click="removeReview">Delete</button>
            </div>
          </div>

          <div v-if="reviewList.length === 0" class="text-muted small mb-3">No reviews yet — be the first.</div>
          <div v-for="r in reviewList" :key="r.id" class="mb-3 pb-3 border-bottom">
            <div class="d-flex justify-content-between">
              <strong class="text-mono small">{{ r.username }}</strong>
              <span class="star-rating small">
                <i v-for="n in 5" :key="n" class="bi" :class="n <= r.rating ? 'bi-star-fill' : 'bi-star'"></i>
              </span>
            </div>
            <p class="mb-0 small">{{ r.comment }}</p>
          </div>
        </div>

        <div class="col-12 col-lg-4">
          <div class="membership-card p-4">
            <p class="eyebrow mb-2">Circulation</p>

            <div v-if="actionError" class="alert alert-danger py-2 small">{{ actionError }}</div>
            <div v-if="actionSuccess" class="alert alert-success py-2 small">{{ actionSuccess }}</div>

            <div v-if="!store.isAuthenticated">
              <p class="small text-muted">Log in to borrow or reserve this title.</p>
              <router-link class="btn btn-primary w-100" :to="{ path: '/login', query: { redirect: $route.fullPath } }">
                Log in
              </router-link>
            </div>

            <div v-else-if="store.isAdmin">
              <p class="small text-muted mb-0">
                Admins manage the catalog and members but don't borrow or reserve books through this account.
              </p>
            </div>

            <div v-else>
              <button v-if="book.available_copies > 0" class="btn btn-primary w-100 mb-2"
                :disabled="acting" @click="handleBorrow">
                <span v-if="acting" class="spinner-border spinner-border-sm me-1"></span>
                Borrow this book
              </button>
              <button v-else class="btn btn-outline-primary w-100 mb-2" :disabled="acting" @click="handleReserve">
                <span v-if="acting" class="spinner-border spinner-border-sm me-1"></span>
                Reserve — notify me when available
              </button>
              <p class="small text-muted mb-0">
                Loans run for a standard borrowing period from the day you check out.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="loading" class="text-center py-5">
      <div class="spinner-border" role="status"></div>
    </div>

    <div v-else class="container py-5 text-center">
      <p class="fs-5">This title isn't in the catalog.</p>
      <router-link to="/books">Back to catalog</router-link>
    </div>
  `,
  data() {
    return {
      book: null,
      loading: true,
      reviewList: [],
      reviewForm: { rating: 0, comment: "" },
      reviewError: "",
      submittingReview: false,
      acting: false,
      actionError: "",
      actionSuccess: "",
    };
  },
  computed: {
    store() {
      return store;
    },
    myReview() {
      return this.reviewList.find((r) => r.username === store.user?.username) || null;
    },
  },
  async created() {
    await this.loadBook();
  },
  watch: {
    "$route.params.id"() {
      this.loadBook();
    },
  },
  methods: {
    async loadBook() {
      this.loading = true;
      this.book = null;
      const id = this.$route.params.id;
      try {
        const [book, reviewData] = await Promise.all([books.get(id), reviews.listForBook(id)]);
        this.book = book;
        this.reviewList = reviewData.results ?? reviewData;
        if (this.myReview) {
          this.reviewForm = { rating: this.myReview.rating, comment: this.myReview.comment };
        }
      } catch {
        this.book = null;
      } finally {
        this.loading = false;
      }
    },
    async submitReview() {
      this.reviewError = "";
      this.submittingReview = true;
      try {
        if (this.myReview) {
          const updated = await reviews.update(this.myReview.id, this.reviewForm);
          const idx = this.reviewList.findIndex((r) => r.id === this.myReview.id);
          this.reviewList.splice(idx, 1, updated);
        } else {
          const created = await reviews.create(this.book.id, this.reviewForm);
          this.reviewList.unshift(created);
        }
      } catch (err) {
        this.reviewError =
          err instanceof ApiError ? err.detail : "Could not save your review right now.";
      } finally {
        this.submittingReview = false;
      }
    },
    async removeReview() {
      if (!this.myReview) return;
      try {
        await reviews.remove(this.myReview.id);
        this.reviewList = this.reviewList.filter((r) => r.id !== this.myReview.id);
        this.reviewForm = { rating: 0, comment: "" };
      } catch (err) {
        this.reviewError = err.detail || "Could not delete your review.";
      }
    },
    async handleBorrow() {
      this.actionError = "";
      this.actionSuccess = "";
      this.acting = true;
      try {
        await loans.borrow(this.book.id);
        this.actionSuccess = "Borrowed! Check My Loans in your profile for the due date.";
        await this.loadBook();
      } catch (err) {
        this.actionError = err instanceof ApiError ? err.detail : "Could not borrow this book.";
      } finally {
        this.acting = false;
      }
    },
    async handleReserve() {
      this.actionError = "";
      this.actionSuccess = "";
      this.acting = true;
      try {
        await reservations.create(this.book.id);
        this.actionSuccess = "Reserved. We'll notify you when a copy is available.";
      } catch (err) {
        this.actionError = err instanceof ApiError ? err.detail : "Could not reserve this book.";
      } finally {
        this.acting = false;
      }
    },
  },
};

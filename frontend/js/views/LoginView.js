import { store } from "../store.js";
import { auth, ApiError } from "../api.js";

export default {
  name: "LoginView",
  template: /* html */ `
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-12">
          <div class="membership-card mx-auto p-4 p-md-5">
            <p class="eyebrow mb-1">Member access</p>
            <h1 class="h3 mb-4">Log in to your account</h1>

            <div v-if="errorMsg" class="alert alert-danger py-2" role="alert">{{ errorMsg }}</div>

            <form @submit.prevent="handleSubmit" novalidate>
              <div class="mb-3">
                <label class="form-label text-mono small" for="username">Username</label>
                <input
                  id="username"
                  v-model.trim="form.username"
                  type="text"
                  class="form-control"
                  autocomplete="username"
                  required
                />
              </div>
              <div class="mb-4">
                <label class="form-label text-mono small" for="password">Password</label>
                <input
                  id="password"
                  v-model="form.password"
                  type="password"
                  class="form-control"
                  autocomplete="current-password"
                  required
                />
                <div class="text-end mt-1">
                  <router-link to="/forgot-password" class="small">Forgot your password?</router-link>
                </div>
              </div>
              <button type="submit" class="btn btn-primary w-100" :disabled="submitting">
                <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
                Log in
              </button>
            </form>

            <p class="text-center mt-4 mb-0 small">
              New here?
              <router-link to="/register">Create a membership</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      form: { username: "", password: "" },
      submitting: false,
      errorMsg: "",
    };
  },
  methods: {
    async handleSubmit() {
      this.errorMsg = "";
      this.submitting = true;
      try {
        const tokens = await auth.login(this.form);
        store.setTokens(tokens.access, tokens.refresh);
        const me = await auth.me();
        store.setUser(me);
        const redirect = this.$route.query.redirect || "/books";
        this.$router.push(redirect);
      } catch (err) {
        this.errorMsg =
          err instanceof ApiError
            ? err.status === 401
              ? "Incorrect username or password."
              : err.detail
            : "Could not reach the server. Is the backend running?";
      } finally {
        this.submitting = false;
      }
    },
  },
};

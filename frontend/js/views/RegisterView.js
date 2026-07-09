import { auth, ApiError } from "../api.js";

export default {
  name: "RegisterView",
  template: /* html */ `
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-12">
          <div class="membership-card mx-auto p-4 p-md-5">
            <p class="eyebrow mb-1">New membership</p>
            <h1 class="h3 mb-4">Create your library account</h1>

            <div v-if="successMsg" class="alert alert-success py-2">{{ successMsg }}</div>
            <div v-if="errorMsg" class="alert alert-danger py-2">{{ errorMsg }}</div>

            <form @submit.prevent="handleSubmit" novalidate>
              <div class="mb-3">
                <label class="form-label text-mono small" for="username">Username</label>
                <input id="username" v-model.trim="form.username" type="text" class="form-control"
                  :class="{ 'is-invalid': fieldErrors.username }" required autocomplete="username" />
                <div class="invalid-feedback">{{ fieldErrors.username?.[0] }}</div>
              </div>
              <div class="mb-3">
                <label class="form-label text-mono small" for="email">Email</label>
                <input id="email" v-model.trim="form.email" type="email" class="form-control"
                  :class="{ 'is-invalid': fieldErrors.email }" required autocomplete="email" />
                <div class="invalid-feedback">{{ fieldErrors.email?.[0] }}</div>
              </div>
              <div class="mb-4">
                <label class="form-label text-mono small" for="password">Password</label>
                <input id="password" v-model="form.password" type="password" class="form-control"
                  :class="{ 'is-invalid': fieldErrors.password }" required autocomplete="new-password" />
                <div class="invalid-feedback">{{ fieldErrors.password?.[0] }}</div>
                <div class="form-text">At least 8 characters; avoid common passwords.</div>
              </div>
              <button type="submit" class="btn btn-primary w-100" :disabled="submitting">
                <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
                Create account
              </button>
            </form>

            <p class="text-center mt-4 mb-0 small">
              Already a member?
              <router-link to="/login">Log in</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      form: { username: "", email: "", password: "" },
      submitting: false,
      errorMsg: "",
      successMsg: "",
      fieldErrors: {},
    };
  },
  methods: {
    async handleSubmit() {
      this.errorMsg = "";
      this.successMsg = "";
      this.fieldErrors = {};
      this.submitting = true;
      try {
        await auth.register(this.form);
        this.successMsg = "Account created. You can log in now.";
        setTimeout(() => this.$router.push("/login"), 1200);
      } catch (err) {
        if (err instanceof ApiError && err.status === 400) {
          this.fieldErrors = err.fields;
          this.errorMsg = "Please fix the highlighted fields.";
        } else {
          this.errorMsg = err.detail || "Could not reach the server.";
        }
      } finally {
        this.submitting = false;
      }
    },
  },
};

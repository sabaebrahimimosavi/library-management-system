import { auth, ApiError } from "../api.js";

export default {
  name: "ForgotPasswordView",
  template: /* html */ `
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-12">
          <div class="membership-card mx-auto p-4 p-md-5">
            <p class="eyebrow mb-1">Member access</p>
            <h1 class="h3 mb-4">Reset your password</h1>

            <div v-if="submitted" class="alert alert-success py-2">
              If that email is on file, a reset link is on its way. Check your inbox.
            </div>

            <template v-else>
              <p class="small text-muted mb-4">
                Enter the email on your account and we'll send you a link to set a new password.
              </p>

              <div v-if="errorMsg" class="alert alert-danger py-2" role="alert">{{ errorMsg }}</div>

              <form @submit.prevent="handleSubmit" novalidate>
                <div class="mb-4">
                  <label class="form-label text-mono small" for="email">Email</label>
                  <input
                    id="email"
                    v-model.trim="email"
                    type="email"
                    class="form-control"
                    autocomplete="email"
                    required
                  />
                </div>
                <button type="submit" class="btn btn-primary w-100" :disabled="submitting">
                  <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
                  Send reset link
                </button>
              </form>
            </template>

            <p class="text-center mt-4 mb-0 small">
              <router-link to="/login">Back to log in</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      email: "",
      submitting: false,
      submitted: false,
      errorMsg: "",
    };
  },
  methods: {
    async handleSubmit() {
      this.errorMsg = "";
      this.submitting = true;
      try {
        await auth.requestPasswordReset(this.email);
        // The backend intentionally never reveals whether the email
        // exists (mitigates user enumeration), so this always succeeds
        // from the UI's point of view.
        this.submitted = true;
      } catch (err) {
        this.errorMsg =
          err instanceof ApiError ? err.detail : "Could not reach the server. Is the backend running?";
      } finally {
        this.submitting = false;
      }
    },
  },
};

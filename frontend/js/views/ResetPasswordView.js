import { auth, ApiError } from "../api.js";

export default {
  name: "ResetPasswordView",
  props: ["uidb64", "token"],
  template: /* html */ `
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-12">
          <div class="membership-card mx-auto p-4 p-md-5">
            <p class="eyebrow mb-1">Member access</p>
            <h1 class="h3 mb-4">Set a new password</h1>

            <div v-if="done" class="alert alert-success py-2">
              Your password has been reset.
              <router-link to="/login">Log in</router-link> with your new password.
            </div>

            <template v-else>
              <div v-if="errorMsg" class="alert alert-danger py-2" role="alert">{{ errorMsg }}</div>

              <form @submit.prevent="handleSubmit" novalidate>
                <div class="mb-3">
                  <label class="form-label text-mono small" for="new_password">New password</label>
                  <input
                    id="new_password"
                    v-model="newPassword"
                    type="password"
                    class="form-control"
                    autocomplete="new-password"
                    required
                  />
                </div>
                <div class="mb-4">
                  <label class="form-label text-mono small" for="confirm_password">Confirm new password</label>
                  <input
                    id="confirm_password"
                    v-model="confirmPassword"
                    type="password"
                    class="form-control"
                    autocomplete="new-password"
                    required
                  />
                  <div class="form-text" v-if="confirmPassword && confirmPassword !== newPassword">
                    Passwords don't match yet.
                  </div>
                </div>
                <button type="submit" class="btn btn-primary w-100"
                  :disabled="submitting || !newPassword || newPassword !== confirmPassword">
                  <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
                  Set new password
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
      newPassword: "",
      confirmPassword: "",
      submitting: false,
      done: false,
      errorMsg: "",
    };
  },
  methods: {
    async handleSubmit() {
      this.errorMsg = "";
      this.submitting = true;
      try {
        await auth.confirmPasswordReset({
          uidb64: this.uidb64,
          token: this.token,
          new_password: this.newPassword,
        });
        this.done = true;
      } catch (err) {
        this.errorMsg =
          err instanceof ApiError
            ? err.detail || "This reset link is invalid or has expired."
            : "Could not reach the server. Is the backend running?";
      } finally {
        this.submitting = false;
      }
    },
  },
};

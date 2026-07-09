import { store } from "../store.js";
import { auth, ApiError } from "../api.js";

export default {
  name: "ProfileView",
  template: /* html */ `
    <div class="container pb-5">
      <p class="eyebrow mb-1">Your membership</p>
      <h1 class="display-heading mb-4">Profile</h1>

      <div class="row g-4">
        <div class="col-12 col-lg-6">
          <div class="membership-card p-4 h-100">
            <h2 class="h5 mb-3">Account details</h2>
            <div v-if="profileMsg" class="alert py-2" :class="profileMsg.ok ? 'alert-success' : 'alert-danger'">
              {{ profileMsg.text }}
            </div>
            <form @submit.prevent="saveProfile">
              <div class="row g-2 mb-2">
                <div class="col-6">
                  <label class="form-label text-mono small">First name</label>
                  <input v-model="profileForm.first_name" class="form-control" />
                </div>
                <div class="col-6">
                  <label class="form-label text-mono small">Last name</label>
                  <input v-model="profileForm.last_name" class="form-control" />
                </div>
              </div>
              <div class="mb-2">
                <label class="form-label text-mono small">Email</label>
                <input v-model="profileForm.email" type="email" class="form-control" />
              </div>
              <p class="small text-muted">
                Username: <span class="text-mono">{{ store.user?.username }}</span> &middot;
                Role: <span class="text-mono">{{ store.user?.role }}</span>
              </p>
              <button class="btn btn-primary" :disabled="savingProfile">Save changes</button>
            </form>
          </div>
        </div>

        <div class="col-12 col-lg-6">
          <div class="membership-card p-4 h-100">
            <h2 class="h5 mb-3">Change password</h2>
            <div v-if="passwordMsg" class="alert py-2" :class="passwordMsg.ok ? 'alert-success' : 'alert-danger'">
              {{ passwordMsg.text }}
            </div>
            <form @submit.prevent="changePassword">
              <div class="mb-2">
                <label class="form-label text-mono small">Current password</label>
                <input v-model="passwordForm.old_password" type="password" class="form-control" required />
              </div>
              <div class="mb-3">
                <label class="form-label text-mono small">New password</label>
                <input v-model="passwordForm.new_password" type="password" class="form-control" required />
              </div>
              <button class="btn btn-outline-primary" :disabled="savingPassword">Update password</button>
            </form>
          </div>
        </div>
      </div>

      <div class="row g-3 mt-1">
        <div class="col-6 col-md-3">
          <router-link to="/loans" class="btn btn-outline-primary w-100">
            <i class="bi bi-journal-text d-block mb-1"></i> My Loans
          </router-link>
        </div>
        <div class="col-6 col-md-3">
          <router-link to="/reservations" class="btn btn-outline-primary w-100">
            <i class="bi bi-bookmark-star d-block mb-1"></i> Reservations
          </router-link>
        </div>
        <div class="col-6 col-md-3">
          <router-link to="/fines" class="btn btn-outline-primary w-100">
            <i class="bi bi-cash-coin d-block mb-1"></i> Fines
          </router-link>
        </div>
        <div class="col-6 col-md-3">
          <router-link to="/notifications" class="btn btn-outline-primary w-100">
            <i class="bi bi-bell d-block mb-1"></i> Notifications
          </router-link>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      profileForm: { first_name: "", last_name: "", email: "" },
      passwordForm: { old_password: "", new_password: "" },
      profileMsg: null,
      passwordMsg: null,
      savingProfile: false,
      savingPassword: false,
    };
  },
  computed: {
    store() {
      return store;
    },
  },
  created() {
    const u = store.user || {};
    this.profileForm = { first_name: u.first_name || "", last_name: u.last_name || "", email: u.email || "" };
  },
  methods: {
    async saveProfile() {
      this.profileMsg = null;
      this.savingProfile = true;
      try {
        const updated = await auth.updateMe(this.profileForm);
        store.setUser(updated);
        this.profileMsg = { ok: true, text: "Profile updated." };
      } catch (err) {
        this.profileMsg = { ok: false, text: err instanceof ApiError ? err.detail : "Could not save profile." };
      } finally {
        this.savingProfile = false;
      }
    },
    async changePassword() {
      this.passwordMsg = null;
      this.savingPassword = true;
      try {
        await auth.changePassword(this.passwordForm);
        this.passwordMsg = { ok: true, text: "Password changed." };
        this.passwordForm = { old_password: "", new_password: "" };
      } catch (err) {
        this.passwordMsg = { ok: false, text: err instanceof ApiError ? err.detail : "Could not change password." };
      } finally {
        this.savingPassword = false;
      }
    },
  },
};

import { store } from "../store.js";
import { auth } from "../api.js";

export default {
  name: "AppNavbar",
  template: /* html */ `
    <nav class="navbar navbar-expand-md catalog-nav navbar-dark mb-4">
      <div class="container">
        <router-link class="navbar-brand" to="/books">
          <i class="bi bi-journal-bookmark-fill me-1"></i> Library
        </router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navMenu">
          <ul class="navbar-nav me-auto mb-2 mb-md-0">
            <li class="nav-item">
              <router-link class="nav-link" to="/books">Catalog</router-link>
            </li>
            <template v-if="store.isAuthenticated && !store.isAdmin">
              <li class="nav-item">
                <router-link class="nav-link" to="/loans">My Loans</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" to="/reservations">Reservations</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" to="/fines">Fines</router-link>
              </li>
            </template>
            <li class="nav-item" v-if="store.isAuthenticated">
              <router-link class="nav-link" to="/notifications">
                <i class="bi bi-bell"></i> Notifications
              </router-link>
            </li>
            <li class="nav-item dropdown" v-if="store.isAdmin">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                Admin
              </a>
              <ul class="dropdown-menu">
                <li>
                  <router-link class="dropdown-item" to="/admin">
                    Dashboard
                  </router-link>
                </li>

                <li>
                  <router-link class="dropdown-item" to="/admin/catalog">
                    Catalog manager
                  </router-link>
                </li>

                <li>
                  <router-link class="dropdown-item" to="/admin/members">
                    Members
                  </router-link>
                </li>

                <li>
                  <router-link class="dropdown-item" to="/loans">
                    All loans
                  </router-link>
                </li>

                <li>
                  <router-link class="dropdown-item" to="/reservations">
                    All reservations
                  </router-link>
                </li>

                <li>
                  <router-link class="dropdown-item" to="/fines">
                    All fines
                  </router-link>
                </li>

                <li>
                  <hr class="dropdown-divider">
                </li>

                <li>
                  <a
                    class="dropdown-item"
                    href="/django-admin/"
                  >
                    <i class="bi bi-shield-lock me-1"></i>
                    Django Admin
                  </a>
                </li>
              </ul>
            </li>
          </ul>
          <ul class="navbar-nav align-items-md-center">
            <template v-if="store.isAuthenticated">
              <li class="nav-item me-2">
                <span class="nav-link disabled text-mono small">
                  {{ store.user?.username }}
                  <span v-if="store.isAdmin" class="stamp stamp-active ms-1">Admin</span>
                </span>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" to="/profile">Profile</router-link>
              </li>
              <li class="nav-item">
                <button class="btn btn-sm btn-outline-light ms-md-2 mt-2 mt-md-0" @click="handleLogout">
                  Log out
                </button>
              </li>
            </template>
            <template v-else>
              <li class="nav-item">
                <router-link class="nav-link" to="/login">Log in</router-link>
              </li>
              <li class="nav-item">
                <router-link class="btn btn-sm btn-outline-light ms-md-2 mt-2 mt-md-0" to="/register">
                  Join the library
                </router-link>
              </li>
            </template>
          </ul>
        </div>
      </div>
    </nav>
  `,
  setup() {
    return { store };
  },
  methods: {
    async handleLogout() {
      try {
        if (store.refreshToken) await auth.logout(store.refreshToken);
      } catch {
        // ignore — we clear local state regardless
      }
      store.clearAuth();
      this.$router.push("/login");
    },
  },
};

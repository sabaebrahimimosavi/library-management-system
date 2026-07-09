import { router } from "./router.js";
import AppNavbar from "./components/AppNavbar.js";
import { store } from "./store.js";
import { auth } from "./api.js";

const { createApp } = Vue;

const RootComponent = {
  components: { AppNavbar },
  template: /* html */ `
    <AppNavbar />
    <router-view />
  `,
};

const app = createApp(RootComponent);
app.use(router);
app.mount("#app");

// Revalidate the session on load: if we have a stored access token but it's
// stale/expired, this either refreshes it (via api.js's 401 handling) or
// clears auth so the UI doesn't show a logged-in state that no longer works.
if (store.accessToken) {
  auth
    .me()
    .then((user) => store.setUser(user))
    .catch(() => store.clearAuth());
}

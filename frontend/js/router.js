import { store } from "./store.js";
import { auth } from "./api.js";
import LoginView from "./views/LoginView.js";
import RegisterView from "./views/RegisterView.js";
import ForgotPasswordView from "./views/ForgotPasswordView.js";
import ResetPasswordView from "./views/ResetPasswordView.js";
import BookListView from "./views/BookListView.js";
import BookDetailView from "./views/BookDetailView.js";
import ProfileView from "./views/ProfileView.js";
import NotFoundView from "./views/NotFoundView.js";
import MyLoansView from "./views/MyLoansView.js";
import MyReservationsView from "./views/MyReservationsView.js";
import MyFinesView from "./views/MyFinesView.js";
import NotificationsView from "./views/NotificationsView.js";
import AdminDashboardView from "./views/AdminDashboardView.js";
import AdminCatalogView from "./views/AdminCatalogView.js";
import AdminMembersView from "./views/AdminMembersView.js";

const { createRouter, createWebHashHistory } = VueRouter;

const routes = [
  { path: "/", redirect: "/books" },
  { path: "/login", name: "login", component: LoginView, meta: { guestOnly: true } },
  { path: "/register", name: "register", component: RegisterView, meta: { guestOnly: true } },
  { path: "/forgot-password", name: "forgot-password", component: ForgotPasswordView, meta: { guestOnly: true } },
  { path: "/reset-password/:uidb64/:token", name: "reset-password", component: ResetPasswordView, props: true, meta: { guestOnly: true } },
  { path: "/books", name: "books", component: BookListView, meta: { requiresAuth: true } },
  { path: "/books/:id", name: "book-detail", component: BookDetailView, props: true, meta: { requiresAuth: true } },

  { path: "/profile", name: "profile", component: ProfileView, meta: { requiresAuth: true } },

  { path: "/loans", name: "my-loans", component: MyLoansView, meta: { requiresAuth: true } },
  { path: "/reservations", name: "my-reservations", component: MyReservationsView, meta: { requiresAuth: true } },
  { path: "/fines", name: "my-fines", component: MyFinesView, meta: { requiresAuth: true } },
  { path: "/notifications", name: "notifications", component: NotificationsView, meta: { requiresAuth: true } },

  { path: "/admin", name: "admin-dashboard", component: AdminDashboardView, meta: { requiresAuth: true, adminOnly: true } },
  { path: "/admin/catalog", name: "admin-catalog", component: AdminCatalogView, meta: { requiresAuth: true, adminOnly: true } },
  { path: "/admin/members", name: "admin-members", component: AdminMembersView, meta: { requiresAuth: true, adminOnly: true } },

  { path: "/:pathMatch(.*)*", name: "not-found", component: NotFoundView },
];

// Hash history (#/books) is used deliberately: these are plain static
// files with no server-side routing/rewrite rules configured, so a
// browser refresh on e.g. /books/3 must not 404 against the file system.
export const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach(async (to) => {
  if (
    to.meta.requiresAuth &&
    !store.isAuthenticated
  ) {
    return {
      path: "/login",
      query: {
        redirect: to.fullPath,
      },
    };
  }

  if (to.meta.guestOnly) {
    if (store.isAuthenticated) {
      return {
        path: "/books",
      };
    }

    /*
     * A guest page means there should not be
     * an active Django administrator session.
     */
    try {
      await auth.clearAdminSession();
    } catch (error) {
      console.warn(
        "Could not clear the Django Admin session:",
        error
      );
    }
  }

  if (
    to.meta.adminOnly &&
    !store.isAdmin
  ) {
    return {
      path: "/books",
    };
  }

  return true;
});

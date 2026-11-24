# Online Library Management System — Frontend Beginner Cheat Sheet

> A simple, project-specific guide to your Vue 3 frontend.
>
> This document assumes you understand only basic HTML, CSS, and JavaScript.

---

# 1. What the frontend is

The **frontend** is the part of the system that the user sees and interacts with.

It includes:

- Pages
- Forms
- Buttons
- Tables
- Search boxes
- Book cards
- Navigation
- Loading spinners
- Error messages
- Success messages

The frontend does **not** directly read or write PostgreSQL.

Instead, it sends HTTP requests to the Django REST API.

```text
User
  ↓
Vue frontend
  ↓ HTTP request
Django REST API
  ↓
PostgreSQL
```

The response returns in the opposite direction:

```text
PostgreSQL
  ↓
Django converts data to JSON
  ↓
Vue receives JSON
  ↓
Vue updates the screen
```

## The most important sentence

> The frontend displays data and collects user actions. The backend owns the real business rules and database.

For example, the frontend can show a **Borrow** button, but Django decides whether borrowing is actually allowed.

---

# 2. What technology this frontend uses

Your frontend uses:

- **HTML** for the base page
- **CSS** for appearance
- **Bootstrap 5** for layout and ready-made styles
- **Bootstrap Icons** for icons
- **Vue 3** for interactive pages
- **Vue Router** for navigation
- **JavaScript ES modules** for organizing files
- The browser's built-in `fetch()` function for API requests

## Important: this is not a normal npm Vue project

Your project does **not** currently use:

- Node.js
- npm
- Vite
- Webpack
- `.vue` files
- A compilation/build step

Vue and Vue Router are loaded from a CDN in `index.html`.

```html
<script src="https://cdn.jsdelivr.net/npm/vue@3.4.21/dist/vue.global.prod.js"></script>
<script src="https://cdn.jsdelivr.net/npm/vue-router@4.3.0/dist/vue-router.global.js"></script>
```

Your own application starts with:

```html
<script type="module" src="js/app.js"></script>
```

This makes the project easier to run because Django can serve the frontend files directly.

## Advantage

You do not need to run:

```bash
npm install
npm run dev
npm run build
```

## Limitation

The browser must be able to reach the CDN URLs for Vue, Bootstrap, icons, and fonts.

---

# 3. Frontend folder structure

```text
frontend/
├── index.html
├── css/
│   └── theme.css
└── js/
    ├── app.js
    ├── router.js
    ├── store.js
    ├── api.js
    ├── config.js
    ├── components/
    │   └── AppNavbar.js
    └── views/
        ├── LoginView.js
        ├── RegisterView.js
        ├── ForgotPasswordView.js
        ├── ResetPasswordView.js
        ├── BookListView.js
        ├── BookDetailView.js
        ├── ProfileView.js
        ├── MyLoansView.js
        ├── MyReservationsView.js
        ├── MyFinesView.js
        ├── NotificationsView.js
        ├── AdminDashboardView.js
        ├── AdminCatalogView.js
        ├── AdminMembersView.js
        └── NotFoundView.js
```

Think of the folders like this:

```text
index.html       → the empty building
app.js           → opens the building
router.js        → decides which room to show
views/           → the rooms/pages
components/      → reusable furniture
store.js         → shared memory
api.js           → telephone to Django
theme.css        → colors and appearance
config.js        → simple configuration
```

---

# 4. How the frontend starts

The startup process is:

```text
Browser opens the website
        ↓
Django serves frontend/index.html
        ↓
index.html loads Bootstrap, Vue, Vue Router, and theme.css
        ↓
index.html loads js/app.js
        ↓
app.js creates the Vue application
        ↓
app.js installs the router
        ↓
app.js mounts Vue inside <div id="app">
        ↓
Vue Router chooses the correct view
```

---

# 5. `index.html` — the base document

File:

```text
frontend/index.html
```

This is the only real HTML document.

The important body is:

```html
<body>
  <div id="app"></div>

  <script src="...vue..."></script>
  <script src="...vue-router..."></script>
  <script src="...bootstrap..."></script>
  <script type="module" src="js/app.js"></script>
</body>
```

## What is `<div id="app"></div>`?

At first, it is empty.

Vue takes control of this element:

```javascript
app.mount("#app");
```

After Vue starts, it places the navbar and the current page inside it.

Before Vue:

```html
<div id="app"></div>
```

After Vue:

```html
<div id="app">
  <nav>...</nav>
  <main>current page...</main>
</div>
```

## Why `type="module"`?

```html
<script type="module" src="js/app.js"></script>
```

It allows JavaScript files to use:

```javascript
import ...
export ...
```

For example:

```javascript
import { router } from "./router.js";
```

---

# 6. `app.js` — the frontend entry point

File:

```text
frontend/js/app.js
```

This is the first file in your own frontend code that runs.

The important structure is:

```javascript
import { router } from "./router.js";
import AppNavbar from "./components/AppNavbar.js";

const { createApp } = Vue;

const RootComponent = {
  components: { AppNavbar },
  template: `
    <AppNavbar />
    <router-view />
  `,
};

const app = createApp(RootComponent);
app.use(router);
app.mount("#app");
```

## What does it mean?

### 1. Create the Vue application

```javascript
const app = createApp(RootComponent);
```

This creates the frontend application.

### 2. Install Vue Router

```javascript
app.use(router);
```

This allows page navigation.

### 3. Attach Vue to the page

```javascript
app.mount("#app");
```

Vue takes control of:

```html
<div id="app"></div>
```

## What is `<AppNavbar />`?

It displays the reusable navigation bar.

## What is `<router-view />`?

It is a placeholder for the current page.

Example:

```text
URL: #/login
<router-view /> shows LoginView
```

```text
URL: #/books
<router-view /> shows BookListView
```

The navbar stays visible while the content inside `<router-view />` changes.

---

# 7. The shape of a Vue view

Most pages in your project have this shape:

```javascript
export default {
  name: "ExampleView",

  template: `
    HTML goes here
  `,

  data() {
    return {
      message: "",
      loading: false,
    };
  },

  computed: {
    calculatedValue() {
      return "...";
    },
  },

  async created() {
    await this.loadData();
  },

  methods: {
    async loadData() {
      // Do work
    },
  },
};
```

## Simple meaning

| Part | Meaning |
|---|---|
| `name` | Name of the Vue page/component |
| `template` | HTML shown to the user |
| `data()` | Changeable local variables |
| `computed` | Values calculated from other data |
| `created()` | Code run when the page starts |
| `methods` | Functions used by the page |
| `watch` | Code run when a watched value changes |
| `props` | Values passed into the page/component |

---

# 8. `data()` — the page's local memory

Example from the login page:

```javascript
data() {
  return {
    form: {
      username: "",
      password: "",
    },
    submitting: false,
    errorMsg: "",
    showPassword: false,
  };
}
```

This means the page remembers:

- The typed username
- The typed password
- Whether the request is running
- The error message
- Whether the password is visible

## Why use `this`?

Inside Vue methods:

```javascript
this.errorMsg = "";
this.submitting = true;
```

`this` means:

> This current Vue page.

So:

```javascript
this.form.username
```

means:

> The username stored in this page's data.

---

# 9. `computed` — automatically calculated values

A computed value is based on other state.

Example:

```javascript
computed: {
  totalPages() {
    return Math.max(
      1,
      Math.ceil(this.count / this.pageSize)
    );
  },
}
```

Suppose:

```text
count = 95
pageSize = 10
```

Then:

```text
totalPages = 10
```

If `count` changes, Vue recalculates `totalPages` automatically.

## Difference between `data` and `computed`

```javascript
data() {
  return {
    count: 95,
    pageSize: 10,
  };
}
```

These are stored values.

```javascript
computed: {
  totalPages() {
    return Math.ceil(this.count / this.pageSize);
  },
}
```

This is a calculated value.

---

# 10. `methods` — actions the page can perform

Example:

```javascript
methods: {
  async fetchLoans() {
    const data = await loans.mine({
      page: this.page,
    });

    this.results = data.results;
  },
}
```

A method may be called:

- When the page opens
- When a button is clicked
- When a form is submitted
- When a filter changes
- From another method

Template example:

```html
<button @click="fetchLoans">
  Reload
</button>
```

When the button is clicked, Vue runs:

```javascript
fetchLoans()
```

---

# 11. Vue template syntax used in your project

## 11.1 Text interpolation: `{{ }}`

```html
<h1>{{ book.title }}</h1>
```

If:

```javascript
book.title = "1984";
```

the browser shows:

```text
1984
```

---

## 11.2 `v-if`

Show an element only when a condition is true.

```html
<div v-if="loading">
  Loading...
</div>
```

If `loading` is false, Vue removes the element.

---

## 11.3 `v-else-if` and `v-else`

```html
<div v-if="loading">
  Loading...
</div>

<div v-else-if="error">
  {{ error }}
</div>

<div v-else>
  Results
</div>
```

Only one branch is displayed.

This pattern appears in many pages:

```text
Loading?
  yes → spinner
  no  → error?
           yes → error message
           no  → show data
```

---

## 11.4 `v-show`

```html
<div v-show="activeTab === 'overview'">
```

`v-show` keeps the element in the page but hides it with CSS.

Difference:

```text
v-if   → creates/removes the element
v-show → keeps it and only hides/shows it
```

Your admin dashboard uses `v-show` for tabs because the tab sections are already loaded.

---

## 11.5 `v-for`

Repeat HTML for every item.

```html
<tr
  v-for="loan in results"
  :key="loan.id"
>
  <td>{{ loan.book_title }}</td>
</tr>
```

If `results` contains 10 loans, Vue creates 10 rows.

### Why `:key="loan.id"`?

It gives every repeated row a unique identity.

Vue uses it to update the correct row efficiently.

---

## 11.6 `v-model`

Connect an input to JavaScript state.

```html
<input v-model="form.username" />
```

When the user types:

```text
sam
```

Vue automatically changes:

```javascript
this.form.username = "sam";
```

It also works in the other direction. If JavaScript changes the value, the input updates.

This is called **two-way binding**.

---

## 11.7 `v-model.trim`

```html
<input v-model.trim="form.username" />
```

`.trim` removes spaces at the beginning and end.

```text
"  sam  " → "sam"
```

---

## 11.8 `v-model.number`

```html
<input
  type="number"
  v-model.number="jumpPage"
/>
```

`.number` tries to store the value as a number instead of a string.

---

## 11.9 `@click`

```html
<button @click="handleBorrow">
```

`@click` means:

```text
When clicked, run handleBorrow()
```

Long form:

```html
<button v-on:click="handleBorrow">
```

Short form used by your project:

```html
<button @click="handleBorrow">
```

---

## 11.10 `@submit.prevent`

```html
<form @submit.prevent="handleSubmit">
```

It means:

1. Listen for form submission.
2. Prevent the browser's normal page reload.
3. Run `handleSubmit()`.

Without `.prevent`, the browser would reload the page.

---

## 11.11 `:disabled`

```html
<button :disabled="submitting">
```

The colon means the value is JavaScript, not plain text.

When:

```javascript
submitting = true;
```

the button is disabled.

This prevents accidental duplicate requests.

---

## 11.12 `:class`

```html
<span
  class="stamp"
  :class="statusClass(loan.status)"
>
```

The normal class is always present:

```text
stamp
```

The calculated class is added:

```text
stamp-active
stamp-overdue
stamp-returned
```

Another example:

```html
<div :class="{ 'bg-light': !n.is_read }">
```

This means:

```text
Add bg-light when n.is_read is false.
```

---

## 11.13 `:to`

```html
<router-link :to="'/books/' + loan.book">
```

The colon makes the route dynamic.

Example:

```javascript
loan.book = 27;
```

Result:

```text
/books/27
```

---

## 11.14 `:src`

```html
<img :src="book.cover_image" />
```

The image URL comes from JavaScript data.

---

## 11.15 `?.` optional chaining

```javascript
store.user?.username
```

It means:

```text
Read username if user exists.
Do not crash if user is null.
```

---

## 11.16 `??` nullish fallback

```javascript
this.results = data.results ?? data;
```

It means:

```text
Use data.results if it exists.
Otherwise use data.
```

This lets the frontend handle both:

```javascript
{
  count: 10,
  results: [...]
}
```

and:

```javascript
[...]
```

---

# 12. `router.js` — navigation

File:

```text
frontend/js/router.js
```

The router connects URLs to Vue pages.

Example:

```javascript
{
  path: "/login",
  name: "login",
  component: LoginView,
}
```

This means:

```text
#/login → show LoginView
```

## Your route table

| Frontend URL | View | Access |
|---|---|---|
| `#/` | Redirects to books | — |
| `#/login` | `LoginView` | Guest only |
| `#/register` | `RegisterView` | Guest only |
| `#/forgot-password` | `ForgotPasswordView` | Guest only |
| `#/reset-password/:uidb64/:token` | `ResetPasswordView` | Guest only |
| `#/books` | `BookListView` | Logged-in user |
| `#/books/:id` | `BookDetailView` | Logged-in user |
| `#/profile` | `ProfileView` | Logged-in user |
| `#/loans` | `MyLoansView` | Logged-in user |
| `#/reservations` | `MyReservationsView` | Logged-in user |
| `#/fines` | `MyFinesView` | Logged-in user |
| `#/notifications` | `NotificationsView` | Logged-in user |
| `#/admin` | `AdminDashboardView` | Admin only |
| `#/admin/catalog` | `AdminCatalogView` | Admin only |
| `#/admin/members` | `AdminMembersView` | Admin only |
| Any unknown path | `NotFoundView` | — |

---

# 13. Why the URL contains `#`

Your router uses:

```javascript
createWebHashHistory()
```

Therefore URLs look like:

```text
http://127.0.0.1:8000/#/books
```

Split it:

```text
http://127.0.0.1:8000/ → Django address
#/books                → Vue page
```

The browser sends only `/` to Django.

Vue reads the part after `#`.

## Simple analogy

```text
Django URL = building address
Vue hash route = room inside the building
```

## Why it helps

Opening this directly:

```text
http://127.0.0.1:8000/books
```

could make Django search for a backend `/books` HTML route.

Opening this:

```text
http://127.0.0.1:8000/#/books
```

loads the frontend root, then Vue handles `/books`.

## Remember

```text
# → Vue frontend route
? → query parameters
```

Example:

```text
#/books?page=3&genre=2
```

- `#/books` tells Vue which page to show.
- `page=3&genre=2` stores page/filter state.

---

# 14. Route parameters

This route contains a dynamic parameter:

```javascript
{
  path: "/books/:id",
  component: BookDetailView,
}
```

If the URL is:

```text
#/books/42
```

then:

```javascript
this.$route.params.id
```

is:

```text
42
```

The book detail page uses it:

```javascript
const id = this.$route.params.id;
const book = await books.get(id);
```

---

# 15. Route query parameters

Your book catalog stores filters and page number in the frontend URL.

Example:

```text
#/books?page=3&genre=2&ordering=-publication_year
```

You read query values using:

```javascript
this.$route.query.page
this.$route.query.genre
this.$route.query.ordering
```

## Why keep catalog state in the URL?

Suppose the user:

1. Searches for Orwell.
2. Goes to page 3.
3. Opens a book.
4. Presses Back.

Because the state is in the URL, the catalog can return to the same search and page.

---

# 16. `<router-link>` versus normal `<a>`

Vue navigation:

```html
<router-link to="/books">
  Catalog
</router-link>
```

This changes the view without reloading the full browser page.

Normal link:

```html
<a href="/django-admin/">
  Django Admin
</a>
```

This performs a normal browser navigation because Django Admin is not a Vue page.

## Rule

Use:

```text
router-link → Vue page
<a href>     → separate Django/server page or external website
```

---

# 17. Route guards — protecting pages

Your router has:

```javascript
router.beforeEach(async (to) => {
  ...
});
```

This runs before every frontend navigation.

It checks route metadata.

Example route:

```javascript
{
  path: "/admin",
  component: AdminDashboardView,
  meta: {
    requiresAuth: true,
    adminOnly: true,
  },
}
```

## Check 1: must be logged in

```javascript
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
```

Meaning:

```text
Protected page requested
        ↓
Not logged in
        ↓
Send user to login
        ↓
Remember original page in redirect
```

## Check 2: guest-only pages

Login and registration are guest-only:

```javascript
meta: {
  guestOnly: true,
}
```

If a logged-in user opens login:

```text
#/login
```

the router sends them to:

```text
#/books
```

## Check 3: administrator pages

```javascript
if (
  to.meta.adminOnly &&
  !store.isAdmin
) {
  return {
    path: "/books",
  };
}
```

A regular member cannot open the admin frontend pages.

## Important security lesson

Frontend route guards improve the user experience, but they are **not enough for security**.

A malicious user can bypass JavaScript.

Therefore Django must also check permissions.

```text
Vue guard    → hides/blocks frontend page
Django       → provides real security
```

---

# 18. `store.js` — shared frontend memory

File:

```text
frontend/js/store.js
```

Most page data is local to one page.

Authentication data must be shared by every page.

The store holds:

```javascript
accessToken
refreshToken
user
```

Example user:

```javascript
{
  id: 3,
  username: "sara",
  email: "sara@example.com",
  first_name: "Sara",
  last_name: "Lee",
  role: "MEMBER",
}
```

## Why is it called a store?

It stores global application state.

```text
Login page writes user information
Navbar reads user information
Router reads authentication state
Profile page reads and updates user information
API layer reads the access token
```

Without shared state, every page would have a separate idea of who is logged in.

---

# 19. Vue reactivity in the store

Your store uses:

```javascript
const { reactive } = Vue;
```

and:

```javascript
export const store = reactive({
  ...
});
```

`reactive()` tells Vue:

> Watch these values. When they change, update every place that uses them.

Example:

```javascript
store.setUser(me);
```

The navbar automatically changes from:

```text
Log in
```

to:

```text
sara | Profile | Log out
```

No manual HTML update is required.

---

# 20. Store getters

```javascript
get isAuthenticated() {
  return !!this.accessToken;
}
```

Meaning:

```text
There is an access token → authenticated
No access token          → guest
```

```javascript
get isAdmin() {
  return this.user?.role === "ADMIN";
}
```

Meaning:

```text
User role is ADMIN → true
Otherwise          → false
```

---

# 21. `localStorage` — remembering login after refresh

Browser memory normally disappears when the page reloads.

Your project saves authentication state in:

```javascript
localStorage
```

Key:

```javascript
"library.auth"
```

Saved data:

```javascript
{
  accessToken,
  refreshToken,
  user
}
```

## Why?

Without `localStorage`:

```text
User logs in
User refreshes browser
Frontend forgets login
```

With `localStorage`:

```text
User logs in
Tokens saved
User refreshes browser
Store loads saved tokens
Session continues
```

## Important warning

`localStorage` is accessible to JavaScript.

Therefore avoiding cross-site scripting vulnerabilities is important.

For a student presentation, say:

> The project persists JWT authentication in browser localStorage for convenience. A production security review may consider stronger token-storage strategies.

---

# 22. Login flow

The login page does:

```javascript
const tokens = await auth.login(this.form);
store.setTokens(tokens.access, tokens.refresh);

const me = await auth.me();
store.setUser(me);

this.$router.push(redirect);
```

Step by step:

```text
1. User enters username/password.
2. Vue sends POST /api/v1/auth/login/.
3. Django checks credentials.
4. Django returns access and refresh tokens.
5. Vue saves tokens in the store and localStorage.
6. Vue requests /api/v1/auth/me/.
7. Django returns user profile and role.
8. Vue saves the user.
9. Router opens the requested page or catalog.
```

## Why request `/auth/me/` after login?

The token proves identity, but the frontend also needs user information:

- Username
- Email
- First name
- Last name
- Role

The navbar and route guards use this information.

---

# 23. Access token and refresh token

## Access token

Used for normal protected requests.

```http
Authorization: Bearer <access-token>
```

It normally expires relatively quickly.

## Refresh token

Used to request a new access token.

It normally lasts longer.

## Simple analogy

```text
Access token  = short-term entry pass
Refresh token = card used to obtain a new entry pass
```

---

# 24. Revalidating the stored session

At the bottom of `app.js`:

```javascript
if (store.accessToken) {
  auth
    .me()
    .then((user) => store.setUser(user))
    .catch(() => store.clearAuth());
}
```

Meaning:

```text
Stored token exists
      ↓
Ask Django: who am I?
      ↓
Request succeeds → update user
Request fails    → clear fake/stale login
```

This prevents the interface from pretending the user is logged in when the session is no longer valid.

---

# 25. `config.js` — API base address

File:

```text
frontend/js/config.js
```

It contains:

```javascript
export const API_BASE_URL = "/api/v1";
```

Therefore:

```javascript
apiFetch("/loans/")
```

requests:

```text
/api/v1/loans/
```

Because the frontend and backend use the same domain, a relative path is enough.

It works with:

```text
http://127.0.0.1:8000
```

and another deployed hostname without hardcoding it.

---

# 26. `api.js` — the frontend's telephone to Django

File:

```text
frontend/js/api.js
```

Views should not repeat raw `fetch()` logic everywhere.

Instead, `api.js` provides named functions:

```javascript
auth.login(...)
books.list(...)
loans.borrow(...)
fines.pay(...)
```

The view asks for an action.

`api.js` handles the HTTP details.

## Mental model

```text
View says: "borrow book 12"
        ↓
api.js converts it into HTTP
        ↓
POST /api/v1/loans/
Body: { "book": 12 }
```

---

# 27. The central `apiFetch()` function

Simplified version:

```javascript
export async function apiFetch(path, opts = {}) {
  const {
    method = "GET",
    body,
    auth = true,
  } = opts;

  const res = await fetch(
    `${API_BASE_URL}${path}`,
    {
      method,
      headers,
      body,
    }
  );

  return responseData;
}
```

The real function also:

- Adds the access token
- Converts objects to JSON
- Handles `FormData`
- Refreshes expired tokens
- Handles empty `204` responses
- Normalizes errors

---

# 28. HTTP methods used by the frontend

| Method | Meaning | Example |
|---|---|---|
| `GET` | Read data | Get books |
| `POST` | Create or perform an action | Borrow book |
| `PATCH` | Partially update data | Edit profile |
| `DELETE` | Delete data | Delete review |

Examples from your API layer:

```javascript
books.get(id)
```

uses:

```http
GET /api/v1/books/books/<id>/
```

```javascript
loans.borrow(bookId)
```

uses:

```http
POST /api/v1/loans/
```

```javascript
auth.updateMe(payload)
```

uses:

```http
PATCH /api/v1/auth/me/
```

```javascript
reviews.remove(id)
```

uses:

```http
DELETE /api/v1/reviews/<id>/
```

---

# 29. JSON request bodies

Example:

```javascript
loans.borrow(12)
```

calls:

```javascript
apiFetch("/loans/", {
  method: "POST",
  body: {
    book: 12,
  },
});
```

`apiFetch()` converts the object to:

```json
{
  "book": 12
}
```

and sends:

```http
Content-Type: application/json
```

---

# 30. Attaching the JWT token

For protected requests:

```javascript
headers["Authorization"] =
  `Bearer ${store.accessToken}`;
```

The request becomes:

```http
Authorization: Bearer eyJ...
```

Django REST Framework reads this token to identify the user.

Public requests use:

```javascript
auth: false
```

Example:

```javascript
auth.login(payload)
```

A person cannot already have a token before logging in.

---

# 31. Automatic token refresh

If Django returns:

```text
401 Unauthorized
```

the API layer checks whether a refresh token exists.

Then:

```text
Request fails with 401
        ↓
POST refresh token
        ↓
Receive new access token
        ↓
Save new access token
        ↓
Repeat original request once
```

The `_retried` flag prevents an infinite loop.

```javascript
_retried: true
```

means:

> This request has already been retried once.

---

# 32. Why `refreshInFlight` exists

Suppose five API calls fail with `401` at the same moment.

Without protection:

```text
5 requests fail
→ 5 refresh requests are sent
```

Your code uses:

```javascript
let refreshInFlight = null;
```

All failed requests share one refresh operation:

```text
5 requests fail
→ 1 refresh request
→ all continue after it succeeds
```

This avoids unnecessary duplicate refresh requests.

---

# 33. API error handling

The project defines:

```javascript
class ApiError extends Error
```

It stores:

```javascript
status
detail
fields
```

Example backend error:

```json
{
  "password": [
    "This password is too common."
  ]
}
```

Frontend can use:

```javascript
err.fields.password
```

A general backend error:

```json
{
  "detail": "No copies are available."
}
```

Frontend can use:

```javascript
err.detail
```

Example:

```javascript
catch (err) {
  this.error =
    err instanceof ApiError
      ? err.detail
      : "Could not load loans.";
}
```

---

# 34. Query strings with `qs()`

The helper:

```javascript
qs({
  page: 2,
  status: "OVERDUE",
})
```

creates:

```text
?page=2&status=OVERDUE
```

Then:

```javascript
loans.mine({
  page: 2,
  status: "OVERDUE",
})
```

requests:

```text
/api/v1/loans/?page=2&status=OVERDUE
```

Empty values are removed.

Example:

```javascript
{
  page: 1,
  status: "",
}
```

becomes:

```text
?page=1
```

not:

```text
?page=1&status=
```

---

# 35. `AppNavbar.js` — reusable navigation

File:

```text
frontend/js/components/AppNavbar.js
```

It is the only general reusable component in the uploaded frontend.

The navbar changes based on authentication and role.

## Guest sees

```text
Catalog | Log in | Join the library
```

## Member sees

```text
Catalog | My Loans | Reservations | Fines |
Notifications | Profile | Log out
```

## Administrator sees

```text
Catalog | Notifications | Admin menu |
Profile | Log out
```

The Admin menu contains:

- Dashboard
- Catalog manager
- Members
- All loans
- All reservations
- All fines
- Django Admin

## How it reads global state

```javascript
setup() {
  return {
    store,
  };
}
```

This makes `store` available inside the template.

Example:

```html
<template v-if="store.isAuthenticated">
```

---

# 36. Logout flow

```javascript
async handleLogout() {
  try {
    if (store.refreshToken) {
      await auth.logout(store.refreshToken);
    }
  } catch {
    // Ignore server logout failure
  }

  store.clearAuth();
  this.$router.push("/login");
}
```

Step by step:

```text
1. Ask Django to blacklist/invalidate refresh token.
2. Even if the request fails, clear local authentication.
3. Remove localStorage data.
4. Navigate to login.
```

Why clear local state even if the backend request fails?

Because the user asked to log out from this browser. The frontend should stop treating them as logged in.

---

# 37. View versus component

In this project:

```text
views/      → full pages connected to routes
components/ → reusable pieces used inside pages
```

Examples:

```text
BookListView      → a complete page
AdminDashboardView → a complete page
AppNavbar         → reused on every page
```

A view is still technically a Vue component. The folder names simply describe their purpose.

---

# 38. Authentication pages

## `LoginView.js`

Purpose:

- Accept username and password
- Request JWT tokens
- Load current user
- Redirect to the correct page
- Show credential/server errors

Main state:

```javascript
form
submitting
errorMsg
showPassword
```

Main method:

```javascript
handleSubmit()
```

Main API calls:

```javascript
auth.login()
auth.me()
```

---

## `RegisterView.js`

Purpose:

- Create a new member account
- Display field-specific backend validation errors
- Redirect to login after success

Main state:

```javascript
form
submitting
errorMsg
successMsg
fieldErrors
showPassword
```

Main API call:

```javascript
auth.register()
```

Important template:

```html
:class="{ 'is-invalid': fieldErrors.password }"
```

This adds Bootstrap's red invalid style when the backend reports a password error.

---

## `ForgotPasswordView.js`

Purpose:

- Accept an email address
- Ask Django to send a reset email

Main API call:

```javascript
auth.requestPasswordReset(email)
```

For security, password reset systems usually avoid revealing whether an email account exists.

---

## `ResetPasswordView.js`

Route:

```text
#/reset-password/:uidb64/:token
```

The router passes the route parameters as props:

```javascript
props: true
```

The view receives:

```javascript
props: ["uidb64", "token"]
```

It sends:

```javascript
{
  uidb64,
  token,
  new_password,
}
```

to Django.

It also checks that the two typed passwords match before enabling submission.

---

# 39. `BookListView.js` — catalog page

This is one of the most important frontend files.

Purpose:

- Show paginated books
- Search by text
- Filter by genre
- Filter by author
- Filter by publication year
- Sort books
- Preserve filters/page in the URL
- Link to book details
- Prevent old search requests from replacing newer results

Main state:

```javascript
results
count
page
jumpPage
pageSize
loading
error
authors
genres
filters
_debounce
_bookRequestId
```

---

# 40. Catalog filters

The filters object is:

```javascript
filters: {
  search: "",
  genre: "",
  author: "",
  publication_year: "",
  ordering: "title",
}
```

It is sent to Django:

```javascript
const params = {
  ...this.filters,
  page: this.page,
  page_size: this.pageSize,
};

const data = await books.list(params);
```

Example request:

```text
/api/v1/books/books/
  ?search=orwell
  &genre=3
  &publication_year=1949
  &ordering=title
  &page=1
  &page_size=20
```

Django filters the full database before returning one page.

---

# 41. Catalog pagination

The server response normally looks like:

```json
{
  "count": 500,
  "next": "...",
  "previous": null,
  "results": [
    
  ]
}
```

The frontend stores:

```javascript
this.results = data.results;
this.count = data.count;
```

Then calculates:

```javascript
totalPages() {
  return Math.ceil(
    this.count / this.pageSize
  );
}
```

Only one page of books is stored in the browser.

This is good for performance.

```text
Database has 500 books
Frontend asks for 20
Django returns 20
```

---

# 42. Search debounce

If the user types:

```text
o
or
orw
orwe
orwel
orwell
```

sending six API requests immediately is wasteful.

Your code waits 300 milliseconds:

```javascript
onFilterChange() {
  clearTimeout(this._debounce);

  this._debounce = setTimeout(
    async () => {
      this.page = 1;
      await this.syncCatalogRoute();
      await this.fetchBooks();
    },
    300
  );
}
```

This is called **debouncing**.

Simple meaning:

> Wait until the user pauses typing before searching.

---

# 43. Preventing outdated search responses

Internet requests may finish in a different order.

Example:

```text
Request A: search "or"
Request B: search "orwell"

B finishes first
A finishes later
```

Without protection, the old `"or"` results could replace the newer `"orwell"` results.

Your code creates a request ID:

```javascript
const requestId =
  ++this._bookRequestId;
```

Before using the result:

```javascript
if (
  requestId !==
  this._bookRequestId
) {
  return;
}
```

Meaning:

> Ignore this result if a newer request has started.

This is a strong frontend detail to mention during your presentation.

---

# 44. Catalog state in the route

Methods:

```javascript
restoreCatalogState()
catalogQuery()
syncCatalogRoute()
bookDetailRoute()
```

They work together.

## `restoreCatalogState()`

Reads page and filters from:

```javascript
this.$route.query
```

## `catalogQuery()`

Creates a clean query object from current state.

## `syncCatalogRoute()`

Updates the URL without reloading:

```javascript
this.$router.replace(...)
```

## `bookDetailRoute(bookId)`

Adds the current catalog location to the detail link:

```javascript
query: {
  from: this.$route.fullPath,
}
```

This allows the Back link to return to the same catalog state.

---

# 45. Book card rendering

Books are repeated with:

```html
<div
  v-for="book in results"
  :key="book.id"
>
```

Availability class:

```html
:class="
  book.available_copies > 0
    ? 'stamp-available'
    : 'stamp-unavailable'
"
```

Meaning:

```text
available_copies > 0 → green Available
available_copies = 0 → red All checked out
```

Images use:

```html
loading="lazy"
decoding="async"
```

These help performance by delaying image loading and decoding.

---

# 46. `BookDetailView.js`

Purpose:

- Load one book
- Load its reviews
- Show availability and details
- Let a member borrow or reserve
- Let a member create/update/delete a review
- Let an administrator view details without borrowing
- Return to the previous catalog state

Main API calls:

```javascript
books.get()
reviews.listForBook()
reviews.create()
reviews.update()
reviews.remove()
loans.borrow()
reservations.create()
```

---

# 47. Loading book and reviews together

```javascript
const [book, reviewData] =
  await Promise.all([
    books.get(id),
    reviews.listForBook(id),
  ]);
```

`Promise.all()` starts both requests at the same time.

Without it:

```text
Load book
wait
Load reviews
wait
```

With it:

```text
Load book and reviews together
wait for both
```

This usually loads faster.

---

# 48. Finding the current user's review

Computed value:

```javascript
myReview() {
  return (
    this.reviewList.find(
      (review) =>
        review.username ===
        store.user?.username
    ) || null
  );
}
```

It searches the review list for the logged-in username.

Then the template changes:

```text
No existing review → "Write a review"
Existing review    → "Update your review"
```

The same form is reused for create and update.

---

# 49. Borrow flow in the frontend

```javascript
async handleBorrow() {
  this.acting = true;

  try {
    await loans.borrow(this.book.id);
    this.actionSuccess = "Borrowed!";
    await this.loadBook();
  } catch (err) {
    this.actionError = err.detail;
  } finally {
    this.acting = false;
  }
}
```

Full flow:

```text
User clicks Borrow
      ↓
acting = true
      ↓
Button disables and spinner appears
      ↓
POST /api/v1/loans/
      ↓
Django checks rules and updates database
      ↓
Success message
      ↓
Reload book
      ↓
Available copies update
```

Important:

> The frontend does not decrease `available_copies` by itself. It reloads the book from the backend, which is the source of truth.

---

# 50. Reserve flow

If:

```javascript
book.available_copies === 0
```

the template shows a Reserve button instead of Borrow.

The method sends:

```javascript
reservations.create(this.book.id)
```

The backend decides whether the reservation is valid.

---

# 51. Review create/update pattern

```javascript
if (this.myReview) {
  await reviews.update(...);
} else {
  await reviews.create(...);
}
```

One form performs two jobs:

```text
Review exists     → PATCH
Review not exists → POST
```

After a successful update:

```javascript
this.reviewList.splice(
  index,
  1,
  updated
);
```

This replaces one item in the reactive array, so Vue updates only that review.

After create:

```javascript
this.reviewList.unshift(created);
```

This adds the new review to the beginning.

---

# 52. Watching route changes

Book detail has:

```javascript
watch: {
  "$route.params.id"() {
    this.loadBook();
  },
}
```

Suppose the user is already on:

```text
#/books/5
```

and Vue changes the route to:

```text
#/books/8
```

The same component may be reused.

The watcher notices that the `id` changed and loads the new book.

---

# 53. `ProfileView.js`

Purpose:

- Show current username and role
- Edit first name, last name, and email
- Change password
- Provide quick links to member pages

Main state:

```javascript
profileForm
passwordForm
profileMsg
passwordMsg
savingProfile
savingPassword
```

On page creation:

```javascript
const u = store.user || {};

this.profileForm = {
  first_name: u.first_name || "",
  last_name: u.last_name || "",
  email: u.email || "",
};
```

After saving:

```javascript
const updated =
  await auth.updateMe(this.profileForm);

store.setUser(updated);
```

This updates:

- The profile page
- The navbar
- `localStorage`

because all use the same reactive store.

---

# 54. `MyLoansView.js`

Purpose:

- Show the member's loans
- Show all loans for an administrator
- Filter by status
- Paginate results
- Let members return books

Main state:

```javascript
results
count
page
pageSize
loading
error
statusFilter
returningId
actionError
actionSuccess
```

Role-dependent title:

```html
{{ store.isAdmin ? 'All loans' : 'My loans' }}
```

Role-dependent member column:

```html
<th v-if="store.isAdmin">
  Member
</th>
```

Role-dependent Return button:

```html
v-if="
  loan.status !== 'RETURNED' &&
  !store.isAdmin
"
```

---

# 55. Backend loan filtering

When status changes:

```javascript
onFilterChange() {
  this.page = 1;
  this.fetchLoans();
}
```

Request parameters:

```javascript
const params = {
  page: this.page,
};

if (this.statusFilter) {
  params.status =
    this.statusFilter;
}
```

Example:

```text
/api/v1/loans/?page=1&status=OVERDUE
```

This is correct server-side filtering:

```text
Django filters every loan
then paginates
then returns current page
```

---

# 56. Per-row loading state

When one loan is being returned:

```javascript
returningId = loan.id;
```

The template checks:

```html
:disabled="returningId === loan.id"
```

Only the clicked row's button shows a spinner.

This is better than disabling every row.

The same pattern is used in several pages:

```text
returningId
cancelingId
markingId
waivingId
savingId
```

---

# 57. `MyReservationsView.js`

Purpose:

- Show reservations
- Show all reservations for an administrator
- Load readable book titles
- Let members cancel pending reservations
- Show reservation status

Main API calls:

```javascript
reservations.mine()
reservations.cancel()
books.get()
```

## Why does it load book titles separately?

The reservation response currently contains a book ID.

Example:

```json
{
  "id": 8,
  "book": 34,
  "status": "PENDING"
}
```

The frontend wants to show:

```text
The Hobbit
```

not:

```text
Book #34
```

So it requests missing books:

```javascript
await books.get(id)
```

and stores titles in:

```javascript
bookTitles: {}
```

Example:

```javascript
{
  34: "The Hobbit",
  52: "1984",
}
```

This process is called **hydrating** the display data.

## Better future API design

The backend serializer could directly include:

```json
{
  "book": 34,
  "book_title": "The Hobbit"
}
```

Then the frontend would not need extra book requests.

---

# 58. Reservation statuses

The frontend maps statuses to styles:

```text
PENDING   → active/amber
FULFILLED → available/green
CANCELLED → unavailable/red
EXPIRED   → overdue/red
```

The UI allows cancellation only when:

```javascript
r.status === "PENDING"
```

and the user is not an administrator.

---

# 59. Deleted-book frontend note

Your currently uploaded `MyReservationsView.js` expects `r.book` to contain an ID.

If you later change the backend so deleted books produce:

```json
{
  "book": null,
  "book_title": "Old Book",
  "status": "EXPIRED"
}
```

update the frontend to prefer `book_title` and avoid calling:

```javascript
books.get(null)
```

This belongs to the later reservation-expiration change, not the basic current flow.

---

# 60. `MyFinesView.js`

Purpose:

- Show fines
- Show all fines for an administrator
- Let members pay unpaid fines
- Let administrators waive fines
- Show payment attempt history
- Paginate the fine list

Main API calls:

```javascript
fines.mine()
fines.pay()
fines.waive()
fines.payments()
```

Main state includes two simple modal-like panels:

```javascript
payTarget
historyTarget
```

If `payTarget` has a fine, the payment panel is displayed.

If `historyTarget` has a fine, the history panel is displayed.

---

# 61. Member versus administrator fine actions

Member:

```text
UNPAID fine → Pay button
```

Administrator:

```text
UNPAID fine → Waive button
```

Both can view payment history.

The template checks:

```javascript
store.isAdmin
```

to decide which actions to show.

Again, Django must also enforce permissions.

---

# 62. Payment flow

```text
Member clicks Pay
      ↓
openPayModal(fine)
      ↓
payTarget stores selected fine
      ↓
Member enters card number
      ↓
submitPayment()
      ↓
POST /fines/<id>/pay/
      ↓
Reload fines
```

The frontend handles a mock decline like any API error:

```javascript
this.payError = err.detail;
```

The actual payment decision belongs to the backend/payment gateway.

---

# 63. Calculating the visible outstanding total

```javascript
outstandingTotal() {
  return this.results
    .filter(
      (fine) =>
        fine.status === "UNPAID"
    )
    .reduce(
      (sum, fine) =>
        sum + Number(fine.amount),
      0
    );
}
```

Important:

> This value is the total of unpaid fines on the currently loaded page, unless the backend provides a separate overall total.

The backend is the correct place to calculate a true global total across every page.

---

# 64. `NotificationsView.js`

Purpose:

- Display notifications
- Show read/unread status
- Let the user mark a notification read
- Paginate notifications

Main state:

```javascript
results
count
page
pageSize
loading
error
unreadOnly
markingId
```

After marking read:

```javascript
const idx =
  this.results.findIndex(
    (r) => r.id === n.id
  );

this.results.splice(
  idx,
  1,
  updated
);
```

Vue immediately updates the selected notification.

---

# 65. Current unread-filter behavior

In the uploaded frontend, unread filtering is currently:

```javascript
filteredResults() {
  if (!this.unreadOnly) {
    return this.results;
  }

  return this.results.filter(
    (n) => !n.is_read
  );
}
```

This filters only the notifications already loaded on the current page.

It does **not** currently request:

```text
?is_read=false
```

from Django.

For a full server-side filter, the switch should refetch with an `is_read` query parameter, similar to `MyLoansView`.

This is an important distinction:

```text
Current notification filter → current page only
Loan status filter          → full backend result set
```

---

# 66. `AdminDashboardView.js`

Purpose:

- Show high-level statistics
- Show report tabs
- Load several reports together
- Display simple monthly bars

Main reports:

- Overview
- Most borrowed books
- Most active members
- Overdue members
- Monthly borrowing
- Popular books

All dashboard requests start together:

```javascript
await Promise.all([
  dashboard.stats(),
  dashboard.mostBorrowed(...),
  dashboard.mostActiveUsers(...),
  dashboard.overdueUsers(...),
  dashboard.monthlyBorrowing(...),
  dashboard.popularBooks(...),
]);
```

This is faster than waiting for each report one by one.

---

# 67. Dashboard stat cards

The backend returns a statistics object.

The computed property transforms it:

```javascript
statCards() {
  return [
    {
      label: "Total books",
      value: this.stats.total_books,
    },
    ...
  ];
}
```

Then one template loop renders all cards:

```html
<div
  v-for="card in statCards"
>
  {{ card.label }}
  {{ card.value }}
</div>
```

This avoids writing eight nearly identical cards manually.

---

# 68. Monthly bars without a chart library

The frontend calculates the biggest monthly count:

```javascript
maxMonthlyCount()
```

Then converts each value into a width:

```javascript
barWidth(count) {
  return Math.round(
    count /
    this.maxMonthlyCount *
    160
  ) + 4;
}
```

The template applies it:

```html
<div
  :style="{
    width: barWidth(m.count) + 'px'
  }"
></div>
```

This creates a simple bar chart without Chart.js.

---

# 69. `AdminMembersView.js`

Purpose:

- List users
- Search members
- Filter by role
- Paginate users
- Promote a member to administrator
- Demote an administrator to member
- Prevent self-role changes in the interface

Main API calls:

```javascript
members.list()
members.updateRole()
```

## Debounced member search

It uses a timeout so it does not request after every keystroke immediately.

```text
User types
→ wait briefly
→ fetch page 1
```

## Role change

```javascript
const nextRole =
  user.role === "ADMIN"
    ? "MEMBER"
    : "ADMIN";
```

Then:

```javascript
await members.updateRole(
  user.id,
  nextRole
);
```

The backend still performs the final authorization and self-demotion protection.

---

# 70. `AdminCatalogView.js`

This is the largest admin frontend page.

Purpose:

- Manage books
- Manage authors
- Manage genres
- Manage publishers
- Upload book covers
- Paginate books
- Display backend field errors
- Reuse shared CRUD logic for simple resources

Tabs:

```text
Books
Authors
Genres
Publishers
```

Main state is divided into:

```text
Book CRUD state
Lookup dropdown data
Shared simple-resource CRUD state
Notice messages
```

---

# 71. Book create/edit form reuse

The same form handles creation and editing.

When creating:

```javascript
bookForm.id = null;
```

When editing:

```javascript
bookForm.id = existingBook.id;
```

Save logic:

```javascript
if (this.bookForm.id) {
  await books.update(...);
} else {
  await books.create(...);
}
```

This is a common frontend pattern:

```text
ID exists    → edit
No ID exists → create
```

---

# 72. Why `emptyBookForm()` exists

A helper creates a new clean book form.

It prevents repeated code and makes reset behavior predictable.

Conceptually:

```javascript
function emptyBookForm() {
  return {
    id: null,
    title: "",
    isbn: "",
    ...
  };
}
```

When the administrator clicks New Book:

```javascript
this.bookForm =
  emptyBookForm();
```

---

# 73. File uploads and `FormData`

Normal requests use JSON.

Files cannot be sent properly as ordinary JSON.

If the administrator selects a cover:

```javascript
this.coverFile = file;
```

The code builds:

```javascript
const fd = new FormData();
```

Then appends fields:

```javascript
fd.append("title", title);
fd.append("isbn", isbn);
fd.append("cover_image", file);
```

`apiFetch()` detects `FormData`:

```javascript
body instanceof FormData
```

and does **not** manually set `Content-Type`.

The browser must create the multipart boundary itself.

## Rule

```text
Normal text/number data → JSON
Request containing file → FormData
```

---

# 74. Image preview

When a file is selected:

```javascript
URL.createObjectURL(file)
```

creates a temporary browser URL for previewing the image before upload.

This does not upload the file.

It only lets the browser display the selected local file.

---

# 75. Shared CRUD for authors, genres, and publishers

Instead of writing three completely separate systems, the page uses:

```javascript
apiFor(resource)
```

Example:

```javascript
apiFor("authors")
```

returns:

```javascript
{
  create: books.createAuthor,
  update: books.updateAuthor,
  remove: books.removeAuthor,
}
```

This lets one method handle several resource types:

```javascript
saveSimple("authors")
saveSimple("genres")
saveSimple("publishers")
```

This is called **reducing duplication**.

---

# 76. Lookup data

The book form needs dropdown lists:

```text
author
genre
publisher
```

The page loads up to 1,000 items:

```javascript
books.authors({
  page_size: 1000,
})
```

and similarly for genres and publishers.

These are stored separately from the resource-management tables because the book form needs them as select options.

---

# 77. Flash messages

Admin catalog uses:

```javascript
flash(ok, text)
```

It stores:

```javascript
notice = {
  ok: true/false,
  text: "...",
}
```

Then removes it after four seconds:

```javascript
setTimeout(...)
```

This avoids leaving old success messages on the screen forever.

---

# 78. Loading, error, empty, and success states

Good frontend pages usually need at least four states.

## Loading

```javascript
loading = true
```

Show spinner.

## Error

```javascript
error = "Could not load books."
```

Show red message.

## Empty

```javascript
results.length === 0
```

Show friendly empty-state text.

## Success/data

Show table, cards, or detail page.

Common template:

```html
<div v-if="loading">
  Spinner
</div>

<div v-else-if="error">
  Error
</div>

<div v-else-if="results.length === 0">
  Empty
</div>

<div v-else>
  Results
</div>
```

---

# 79. The `try/catch/finally` request pattern

Many methods use:

```javascript
async fetchData() {
  this.loading = true;
  this.error = "";

  try {
    const data = await apiCall();
    this.results = data.results;
  } catch (err) {
    this.error = err.detail;
  } finally {
    this.loading = false;
  }
}
```

Meaning:

```text
Before request → start loading
Try            → perform request
Catch          → handle failure
Finally        → stop loading whether success or failure
```

`finally` always runs.

---

# 80. Why disable buttons during requests?

Example:

```html
<button :disabled="submitting">
```

Without disabling:

```text
User clicks Pay five times
→ five requests may be sent
```

With disabling:

```text
First click
→ button disabled
→ request finishes
→ button enabled
```

This protects the user and backend from accidental duplicates.

The backend must still protect against duplicate operations.

---

# 81. Client state versus server state

## Client/local state

Temporary UI information:

```javascript
showPassword
activeTab
loading
error
payTarget
coverPreview
```

The database does not need to know these.

## Shared client state

Used across pages:

```javascript
store.user
store.accessToken
store.refreshToken
```

## Server state

Real business data:

```text
Books
Loans
Reservations
Fines
Reviews
Users
Notifications
```

The backend/database is the source of truth for server state.

---

# 82. Why reload data after actions?

After return:

```javascript
await loans.returnBook(id);
await this.fetchLoans();
```

After borrow:

```javascript
await loans.borrow(bookId);
await this.loadBook();
```

After fine payment:

```javascript
await fines.pay(...);
await this.fetchFines();
```

Why not manually guess every field change?

Because one backend operation may change multiple things:

```text
Loan status
Book inventory
Fine status
Reservation state
Notification creation
```

Reloading asks the backend for the authoritative result.

---

# 83. CSS and Bootstrap

## Bootstrap

Bootstrap provides classes such as:

```text
container
row
col-12
btn
btn-primary
form-control
table
alert
spinner-border
d-flex
mb-4
```

Example:

```html
<div class="row g-3">
```

- `row` creates a Bootstrap row.
- `g-3` adds gaps.

```html
<div class="col-12 col-md-6">
```

- Full width on small screens.
- Half width on medium and larger screens.

This makes the site responsive.

---

# 84. `theme.css`

File:

```text
frontend/css/theme.css
```

It creates a custom library/card-catalog appearance.

It defines CSS variables:

```css
:root {
  --ink-900: #1b2a4a;
  --paper-0: #faf7f0;
  --stamp-red: #7a2e2e;
  --brass: #b6862c;
}
```

Then uses them:

```css
.btn-primary {
  background: var(--ink-900);
}
```

Benefits:

```text
Change one variable
→ update many parts of the theme
```

---

# 85. Important custom CSS classes

| Class | Purpose |
|---|---|
| `.catalog-nav` | Dark library navbar |
| `.book-card` | Card-catalog book card |
| `.stamp` | Status label base |
| `.stamp-available` | Green status |
| `.stamp-unavailable` | Red unavailable status |
| `.stamp-overdue` | Red overdue status |
| `.stamp-active` | Amber active status |
| `.stamp-returned` | Green returned status |
| `.drawer-bar` | Dark filter/search area |
| `.membership-card` | Form/detail card |
| `.eyebrow` | Small section label |
| `.text-mono` | Monospace metadata style |
| `.display-heading` | Display font heading |

---

# 86. Responsive design

Bootstrap breakpoint examples:

```html
col-12 col-md-6 col-lg-4
```

Meaning:

```text
Small screen  → 1 column
Medium screen → 2 columns
Large screen  → 3 columns
```

Navbar:

```html
navbar-expand-md
```

Meaning:

```text
Below medium width → collapsed menu button
Medium and above   → full navigation
```

---

# 87. Accessibility details already present

Your frontend includes several good accessibility details:

```html
<label for="username">
<input id="username">
```

This connects labels to inputs.

```html
aria-label="Catalog pages"
```

helps screen readers.

```html
<span class="visually-hidden">
  Loading books...
</span>
```

provides spinner meaning.

```css
:focus-visible {
  outline: 3px solid var(--brass);
}
```

makes keyboard focus visible.

```css
@media (prefers-reduced-motion: reduce)
```

reduces animation for users who request it.

---

# 88. Frontend API map

## Authentication

```javascript
auth.register(payload)
auth.login(payload)
auth.me()
auth.updateMe(payload)
auth.logout(refreshToken)
auth.changePassword(payload)
auth.requestPasswordReset(email)
auth.confirmPasswordReset(payload)
auth.clearAdminSession()
```

## Books

```javascript
books.list(params)
books.get(id)
books.create(payload)
books.update(id, payload)
books.remove(id)
```

## Authors

```javascript
books.authors(params)
books.createAuthor(payload)
books.updateAuthor(id, payload)
books.removeAuthor(id)
```

## Genres

```javascript
books.genres(params)
books.createGenre(payload)
books.updateGenre(id, payload)
books.removeGenre(id)
```

## Publishers

```javascript
books.publishers(params)
books.createPublisher(payload)
books.updatePublisher(id, payload)
books.removePublisher(id)
```

## Reviews

```javascript
reviews.listForBook(bookId)
reviews.create(bookId, payload)
reviews.update(id, payload)
reviews.remove(id)
```

## Loans

```javascript
loans.mine(params)
loans.borrow(bookId)
loans.returnBook(id)
```

## Reservations

```javascript
reservations.mine(params)
reservations.create(bookId)
reservations.cancel(id)
```

## Fines

```javascript
fines.mine(params)
fines.get(id)
fines.pay(id, payload)
fines.waive(id)
fines.payments(id)
```

## Notifications

```javascript
notifications.list(params)
notifications.markRead(id)
```

## Dashboard

```javascript
dashboard.stats()
dashboard.mostBorrowed(params)
dashboard.mostActiveUsers(params)
dashboard.overdueUsers(params)
dashboard.monthlyBorrowing(params)
dashboard.popularBooks(params)
```

## Member administration

```javascript
members.list(params)
members.updateRole(id, role)
```

---

# 89. Complete login data flow

```text
LoginView template
      ↓ user submits form
handleSubmit()
      ↓
auth.login(form)
      ↓
apiFetch("/auth/login/", POST)
      ↓
Django authentication endpoint
      ↓
JSON tokens
      ↓
store.setTokens()
      ↓
localStorage
      ↓
auth.me()
      ↓
Django returns user and role
      ↓
store.setUser()
      ↓
Navbar and route guards update
      ↓
router.push()
```

---

# 90. Complete catalog data flow

```text
BookListView created()
      ↓
restore filters from URL
      ↓
load authors and genres
      ↓
fetchBooks()
      ↓
books.list(params)
      ↓
GET /api/v1/books/books/?...
      ↓
Django filters and paginates
      ↓
JSON { count, results }
      ↓
Vue saves results and count
      ↓
v-for creates book cards
```

---

# 91. Complete borrow data flow

```text
BookDetailView
      ↓ user clicks Borrow
handleBorrow()
      ↓
loans.borrow(book.id)
      ↓
POST /api/v1/loans/
      ↓
Django validates:
  - user role
  - available copy
  - duplicate active loan
  - reservation rules
      ↓
Django creates loan
      ↓
Django decreases inventory
      ↓
JSON response
      ↓
Vue shows success
      ↓
Vue reloads book
```

---

# 92. Complete return data flow

```text
MyLoansView
      ↓ user clicks Return
returnLoan(loan)
      ↓
loans.returnBook(loan.id)
      ↓
POST /api/v1/loans/<id>/return_book/
      ↓
Django marks loan returned
      ↓
Django increases inventory
      ↓
Django handles fine/reservation effects
      ↓
Vue reloads loans
```

---

# 93. Complete admin book-save flow

```text
AdminCatalogView
      ↓
Administrator fills form
      ↓
saveBook()
      ↓
buildBookPayload()
      ↓
No file → JSON
File    → FormData
      ↓
ID exists?
  yes → PATCH existing book
  no  → POST new book
      ↓
Django validates fields
      ↓
Success → flash message + reload list
Error   → field errors + error message
```

---

# 94. How to add a new frontend page

Suppose you want a page called `AboutView`.

## Step 1: create the view

```text
frontend/js/views/AboutView.js
```

```javascript
export default {
  name: "AboutView",

  template: `
    <div class="container">
      <h1>About</h1>
      <p>Library information.</p>
    </div>
  `,
};
```

## Step 2: import it in `router.js`

```javascript
import AboutView
  from "./views/AboutView.js";
```

## Step 3: add a route

```javascript
{
  path: "/about",
  name: "about",
  component: AboutView,
}
```

## Step 4: add navigation if needed

```html
<router-link
  class="nav-link"
  to="/about"
>
  About
</router-link>
```

The URL becomes:

```text
#/about
```

---

# 95. How to add a new API function

Suppose Django adds:

```text
GET /api/v1/books/recommended/
```

Add to `api.js`:

```javascript
export const books = {
  // existing functions

  recommended: () =>
    apiFetch(
      "/books/recommended/"
    ),
};
```

Use it in a view:

```javascript
import { books } from "../api.js";

async loadRecommended() {
  this.results =
    await books.recommended();
}
```

---

# 96. How to create a small reusable component

Suppose book cards are used in several pages.

Create:

```text
frontend/js/components/BookCard.js
```

```javascript
export default {
  name: "BookCard",

  props: ["book"],

  template: `
    <div class="card book-card p-3">
      <h2>{{ book.title }}</h2>
      <p>{{ book.author_name }}</p>
    </div>
  `,
};
```

Import into a view:

```javascript
import BookCard
  from "../components/BookCard.js";

export default {
  components: {
    BookCard,
  },

  template: `
    <BookCard
      v-for="book in results"
      :key="book.id"
      :book="book"
    />
  `,
};
```

---

# 97. `props`

Props pass data from a parent to a child.

Example:

```html
<BookCard :book="book" />
```

Child:

```javascript
props: ["book"]
```

Simple analogy:

```text
Parent hands a book object to the BookCard component.
```

Props should be treated as input. The child should normally not directly mutate the parent's object.

---

# 98. Lifecycle hooks

## `created()`

Runs after the component's state is created.

Good for API requests:

```javascript
async created() {
  await this.fetchLoans();
}
```

## `beforeUnmount()`

Runs just before Vue removes the component.

Book catalog uses it to cancel the debounce timer:

```javascript
beforeUnmount() {
  clearTimeout(this._debounce);
}
```

This avoids an old timer running after the user leaves the page.

---

# 99. `async` and `await`

An API request takes time.

```javascript
const data =
  await books.list(params);
```

`await` means:

> Pause this async function until the promise finishes.

The function must be marked:

```javascript
async fetchBooks() {
```

Without `await`, `data` would be a pending Promise instead of the actual response.

---

# 100. Array methods used in your frontend

## `.map()`

Transform each item.

```javascript
this.monthlyBorrowing.map(
  (month) => month.count
)
```

## `.filter()`

Keep matching items.

```javascript
results.filter(
  (notification) =>
    !notification.is_read
)
```

## `.find()`

Find one item.

```javascript
reviewList.find(
  (review) =>
    review.username === username
)
```

## `.findIndex()`

Find an item's position.

```javascript
results.findIndex(
  (item) => item.id === id
)
```

## `.reduce()`

Combine values into one result.

```javascript
fines.reduce(
  (total, fine) =>
    total + Number(fine.amount),
  0
)
```

## `.slice()`

Take part of an array.

```javascript
results.slice(0, 20)
```

## `.unshift()`

Add to the beginning.

```javascript
reviewList.unshift(created)
```

## `.splice()`

Replace/remove items reactively.

```javascript
reviewList.splice(
  index,
  1,
  updated
)
```

---

# 101. Destructuring used in the project

```javascript
const {
  method = "GET",
  body,
  auth = true,
} = opts;
```

This extracts values from an object.

Equivalent longer code:

```javascript
const method =
  opts.method || "GET";

const body =
  opts.body;

const auth =
  opts.auth === undefined
    ? true
    : opts.auth;
```

Another example:

```javascript
const [book, reviews] =
  await Promise.all([...]);
```

This extracts array positions.

---

# 102. Spread syntax

```javascript
const params = {
  ...this.filters,
  page: this.page,
};
```

`...this.filters` copies all filter properties.

If:

```javascript
this.filters = {
  search: "orwell",
  genre: "2",
}
```

result:

```javascript
params = {
  search: "orwell",
  genre: "2",
  page: 1,
}
```

---

# 103. Ternary operator

```javascript
store.isAdmin
  ? "All loans"
  : "My loans"
```

Meaning:

```text
If admin → "All loans"
Otherwise → "My loans"
```

It is a short `if/else` used to calculate a value.

---

# 104. Common frontend mistakes to avoid

## Mistake 1: forgetting `.js` in imports

Correct:

```javascript
import { store }
  from "./store.js";
```

In native browser ES modules, the extension matters.

---

## Mistake 2: using a backend URL as a Vue route

Vue route:

```text
#/books
```

Backend API:

```text
/api/v1/books/books/
```

They are different.

---

## Mistake 3: trusting frontend role checks for security

Hiding a button is not security.

Django permissions are required.

---

## Mistake 4: directly changing server data only in the frontend

Bad:

```javascript
loan.status = "RETURNED";
```

without calling the backend.

Good:

```javascript
await loans.returnBook(loan.id);
await this.fetchLoans();
```

---

## Mistake 5: forgetting loading reset

Use `finally`:

```javascript
finally {
  this.loading = false;
}
```

---

## Mistake 6: manually setting `Content-Type` for `FormData`

Do not do:

```javascript
headers["Content-Type"] =
  "multipart/form-data";
```

The browser must add the boundary.

Your API wrapper correctly avoids setting it.

---

## Mistake 7: filtering only one page by accident

If data is paginated, local `.filter()` sees only the current page.

For complete filtering, send parameters to Django.

---

## Mistake 8: sending too many search requests

Use debounce for text search.

---

## Mistake 9: not handling old requests

Fast-changing searches can produce out-of-order results.

Your catalog request-ID pattern handles this.

---

## Mistake 10: forgetting to clear errors

Before a new request:

```javascript
this.error = "";
```

Otherwise an old error may remain visible during a successful retry.

---

# 105. Browser Developer Tools

Open:

```text
F12
```

Important tabs:

## Console

Shows:

- JavaScript syntax errors
- `console.error()`
- `console.warn()`
- Failed module imports
- Undefined variables

Example:

```text
ReferenceError: key is not defined
```

## Network

Shows every API request.

Check:

- URL
- Method
- Status code
- Request body
- Response JSON
- Authorization header

## Application

Shows:

```text
Local Storage
```

Look for:

```text
library.auth
```

## Elements

Shows the generated HTML and CSS.

---

# 106. HTTP status codes you should understand

| Code | Meaning |
|---:|---|
| `200` | Request succeeded |
| `201` | New object created |
| `204` | Success with no response body |
| `400` | Invalid input/business validation |
| `401` | Not authenticated/token invalid |
| `403` | Authenticated but not allowed |
| `404` | Resource not found |
| `405` | HTTP method not allowed |
| `409` | Conflict |
| `402` | Payment required/declined in mock flow |
| `500` | Backend server error |

Examples:

```text
Wrong password → 401
Weak registration password → 400
Member opens admin API → 403
Missing book → 404
PATCH disabled loan endpoint → 405
```

---

# 107. Debugging a failed button

Suppose Borrow does nothing.

Follow this order:

```text
1. Open Console.
2. Look for JavaScript error.
3. Open Network.
4. Click Borrow again.
5. Find POST /api/v1/loans/.
6. Check status code.
7. Check response JSON.
8. Check request body.
9. Check Authorization header.
10. Check Django terminal logs.
```

Possible meanings:

```text
No request appears
→ frontend click/method/JavaScript problem

Request appears with 400
→ backend validation/business rule

Request appears with 401
→ authentication/token problem

Request appears with 403
→ permission problem

Request appears with 500
→ backend exception
```

---

# 108. How to explain the frontend in a presentation

Use this:

> The frontend is a Vue 3 single-page application served directly by Django. It uses Vue Router in hash mode for navigation, a small reactive store for JWT authentication, and a centralized API wrapper around `fetch()`. Each screen is a JavaScript Vue component with a template, local state, computed values, lifecycle hooks, and methods. The frontend sends requests to Django REST Framework, displays returned JSON, and changes its interface based on the user's role.

A simpler version:

> Vue shows the pages, the router changes pages, the store remembers the logged-in user, and `api.js` talks to Django.

---

# 109. Questions someone may ask you

## Why did you use Vue?

Answer:

> Vue makes the interface reactive. When data changes, Vue updates the relevant HTML automatically without reloading the whole page.

## Why no Node or npm?

Answer:

> This version uses Vue's browser global build from a CDN. It keeps setup simple and allows Django to serve the frontend directly without a build step.

## What is a single-page application?

Answer:

> The browser loads one base HTML page. Vue changes the visible view inside that page instead of requesting a new HTML document for every screen.

## What does Vue Router do?

Answer:

> It maps frontend paths such as `/books` and `/loans` to Vue view components.

## Why is there a `#`?

Answer:

> Hash routing lets Vue manage frontend paths while Django only needs to serve the root frontend page.

## What is the store?

Answer:

> It is shared reactive memory containing the JWT tokens and logged-in user.

## What does `api.js` do?

Answer:

> It centralizes HTTP requests, adds authentication headers, refreshes expired access tokens, serializes JSON, handles file uploads, and normalizes errors.

## Is hiding admin buttons secure?

Answer:

> No. It improves the interface, but Django permissions provide the real security.

## Why use pagination?

Answer:

> It avoids loading hundreds of records at once, improving speed and reducing data transfer.

## Why use debounce?

Answer:

> It waits for the user to pause typing so the frontend does not send an API request after every keystroke.

## Why reload after borrowing or returning?

Answer:

> The backend may change several related values, so reloading retrieves the authoritative state.

## What is `Promise.all()`?

Answer:

> It starts independent requests together and waits until all are finished, which is usually faster than running them one after another.

---

# 110. Five-minute frontend demonstration order

## 1. Show folder structure

Explain:

```text
app → router → view → api → Django
```

## 2. Show `index.html`

Point to:

```html
<div id="app"></div>
<script type="module" src="js/app.js"></script>
```

## 3. Show `app.js`

Explain:

```text
Navbar stays
router-view changes
```

## 4. Show `router.js`

Open:

```text
#/books
#/loans
#/admin
```

Explain route guards.

## 5. Show `store.js`

Explain:

```text
tokens + user + role
```

## 6. Show `api.js`

Explain:

```text
JWT header
automatic refresh
named API functions
```

## 7. Show `BookListView.js`

Explain:

```text
v-model
v-for
filters
debounce
pagination
```

## 8. Show `BookDetailView.js`

Click Borrow/Reserve and explain the API flow.

## 9. Show role changes

Login as member and admin. Point out different navbar items.

## 10. Open Developer Tools

Show one request in the Network tab.

---

# 111. Thirty-second memory sheet

```text
index.html
Loads Vue, Bootstrap, CSS, and app.js.

app.js
Creates Vue, installs router, mounts #app.

router.js
Maps URL paths to pages and protects routes.

store.js
Stores JWT tokens and current user globally.

api.js
Sends HTTP requests to Django and handles tokens/errors.

components/
Reusable UI pieces, currently mainly the navbar.

views/
Full pages such as books, loans, fines, and admin screens.

theme.css
Custom appearance on top of Bootstrap.
```

---

# 112. The full frontend formula

Memorize:

```text
Template
+ data
+ computed
+ methods
+ lifecycle
= Vue page
```

And:

```text
User action
→ Vue method
→ api.js
→ Django
→ JSON
→ update Vue data
→ Vue updates HTML
```

---

# 113. Symbols cheat sheet

| Syntax | Meaning |
|---|---|
| `{{ value }}` | Display JavaScript value |
| `v-if` | Show only if true |
| `v-else` | Otherwise show |
| `v-for` | Repeat for every item |
| `v-show` | Hide/show with CSS |
| `v-model` | Connect input and state |
| `@click` | Run method on click |
| `@submit.prevent` | Handle form without reload |
| `:class` | Dynamic class |
| `:disabled` | Dynamic disabled state |
| `:to` | Dynamic router destination |
| `:src` | Dynamic image URL |
| `?.` | Read safely if value exists |
| `??` | Use fallback for null/undefined |
| `...object` | Copy object properties |
| `async` | Function can wait for promises |
| `await` | Wait for promise result |
| `try/catch` | Handle success/failure |
| `finally` | Always run cleanup |
| `this` | Current Vue component |

---

# 114. File-by-file one-line summary

| File | One-line purpose |
|---|---|
| `index.html` | Loads all frontend libraries and the Vue application |
| `css/theme.css` | Defines the library-themed appearance |
| `js/config.js` | Stores the API base path |
| `js/app.js` | Creates and mounts the Vue application |
| `js/router.js` | Maps frontend URLs to pages and guards access |
| `js/store.js` | Stores global authentication state |
| `js/api.js` | Sends authenticated requests to Django |
| `components/AppNavbar.js` | Displays role-aware navigation |
| `views/LoginView.js` | Logs users in |
| `views/RegisterView.js` | Creates member accounts |
| `views/ForgotPasswordView.js` | Requests password-reset email |
| `views/ResetPasswordView.js` | Sets a new password using reset token |
| `views/BookListView.js` | Searches, filters, sorts, and paginates books |
| `views/BookDetailView.js` | Shows one book, borrowing, reservations, and reviews |
| `views/ProfileView.js` | Edits profile and password |
| `views/MyLoansView.js` | Lists and returns loans |
| `views/MyReservationsView.js` | Lists and cancels reservations |
| `views/MyFinesView.js` | Pays or waives fines and shows payment history |
| `views/NotificationsView.js` | Lists and marks notifications read |
| `views/AdminDashboardView.js` | Shows library statistics and reports |
| `views/AdminCatalogView.js` | Manages books and lookup resources |
| `views/AdminMembersView.js` | Searches users and changes roles |
| `views/NotFoundView.js` | Handles unknown frontend URLs |

---

# 115. Final mental model

Imagine a restaurant:

```text
User                  = customer
Vue view              = waiter
api.js                = order system
Django API            = kitchen manager
Database              = storage room
store.js              = customer's membership card
router.js             = person directing customers to tables
theme.css              = restaurant decoration
```

The waiter does not cook or manage storage.

The frontend does not own business rules or the database.

It gathers the user's request, sends it to Django, receives the result, and presents it clearly.

---

# 116. What to study first

Study in this order:

```text
1. index.html
2. app.js
3. router.js
4. store.js
5. api.js
6. LoginView.js
7. BookListView.js
8. BookDetailView.js
9. MyLoansView.js
10. AdminCatalogView.js
```

Do not begin by memorizing every line.

First understand these five questions for each page:

```text
1. What does the template show?
2. What values are stored in data()?
3. What computed values are calculated?
4. What runs in created()?
5. Which methods call which API functions?
```

Once you can answer those questions, you understand the page.

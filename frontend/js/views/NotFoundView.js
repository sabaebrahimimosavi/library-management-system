export default {
  name: "NotFoundView",
  template: /* html */ `
    <div class="container py-5 text-center">
      <p class="eyebrow">Misfiled</p>
      <h1 class="display-heading">This card isn't in the drawer.</h1>
      <router-link to="/books" class="btn btn-primary mt-3">Back to the catalog</router-link>
    </div>
  `,
};

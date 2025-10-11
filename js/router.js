const routes = {};
let currentRoute = "/";

function renderRoute(path) {
  const view = routes[path] ?? routes["*"];
  if (view) {
    view();
  }
}

function updateActiveLinks(path) {
  document
    .querySelectorAll(".nav__link")
    .forEach((link) => link.classList.toggle("active", link.dataset.route === path));
}

export function registerRoute(path, render) {
  routes[path] = render;
}

export function initRouter(defaultRoute) {
  function onHashChange() {
    const path = location.hash.replace(/^#/, "");
    currentRoute = path || defaultRoute;
    updateActiveLinks(currentRoute);
    renderRoute(currentRoute);
  }

  window.addEventListener("hashchange", onHashChange);
  onHashChange();
}

export function navigate(path) {
  if (currentRoute === path) return;
  location.hash = path;
}

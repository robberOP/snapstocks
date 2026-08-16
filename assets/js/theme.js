/* Theme toggle: light (default) / dark, persisted in localStorage.
   Site defaults to light — this only matters for the optional toggle. */
(function () {
  var KEY = "snapstocks-theme";
  function apply(theme) {
    if (theme === "dark" || theme === "light") {
      document.documentElement.setAttribute("data-theme", theme);
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  }
  var saved = localStorage.getItem(KEY);
  if (saved) apply(saved);

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-theme-toggle]");
    if (!btn) return;
    var current = document.documentElement.getAttribute("data-theme");
    var isDark = current === "dark" || (!current && window.matchMedia("(prefers-color-scheme: dark)").matches);
    var next = isDark ? "light" : "dark";
    apply(next);
    localStorage.setItem(KEY, next);
  });
})();

/* Mobile nav drawer toggle. Active-link highlighting is set per-page via
   aria-current="page" in the markup (no routing framework in this static site). */
(function () {
  document.addEventListener("click", function (e) {
    var toggle = e.target.closest("[data-nav-toggle]");
    if (toggle) {
      var drawer = document.querySelector("[data-nav-drawer]");
      if (drawer) drawer.classList.toggle("open");
      return;
    }
    var link = e.target.closest("[data-nav-drawer] a");
    if (link) {
      var drawer2 = document.querySelector("[data-nav-drawer]");
      if (drawer2) drawer2.classList.remove("open");
    }
  });
})();

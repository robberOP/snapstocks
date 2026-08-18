// Powers every ticker search box on the site — the header nav-search and
// the bigger search field on stock-analysis/index.html — from the single
// data/stocks.json index (see scripts/generate_stock_index.py). Selecting
// a result goes to that stock's fundamentals page by default; stocks that
// also have a deep-dive report show a pill that jumps straight there
// instead, since only a few stocks have one so far.
(function () {
  var inputs = document.querySelectorAll("[data-stock-search]");
  if (!inputs.length) return;

  var stocksPromise = fetch("/data/stocks.json")
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .catch(function (err) {
      console.error("stock-search: could not load /data/stocks.json", err);
      return [];
    });

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // Lower rank = better match: exact symbol, then symbol-prefix, then
  // name-prefix, then symbol/name substring.
  function rank(stock, query) {
    var symbol = stock.symbol.toLowerCase();
    var name = stock.name.toLowerCase();
    if (symbol === query) return 0;
    if (symbol.indexOf(query) === 0) return 1;
    if (name.indexOf(query) === 0) return 2;
    if (symbol.indexOf(query) !== -1) return 3;
    if (name.indexOf(query) !== -1) return 4;
    return -1;
  }

  function search(stocks, query, limit) {
    query = query.trim().toLowerCase();
    if (!query) return [];
    var scored = [];
    for (var i = 0; i < stocks.length; i++) {
      var r = rank(stocks[i], query);
      if (r !== -1) scored.push([r, stocks[i]]);
    }
    scored.sort(function (a, b) {
      return a[0] - b[0] || a[1].name.localeCompare(b[1].name);
    });
    var out = [];
    for (var j = 0; j < scored.length && j < limit; j++) out.push(scored[j][1]);
    return out;
  }

  inputs.forEach(function (input) {
    var wrap = input.closest(".nav-search, .search-field");
    if (!wrap) return;

    var panel = document.createElement("div");
    panel.className = "stock-search-results";
    panel.setAttribute("role", "listbox");
    wrap.appendChild(panel);

    var activeIndex = -1;
    var currentResults = [];

    function close() {
      panel.classList.remove("is-open");
      panel.innerHTML = "";
      activeIndex = -1;
      currentResults = [];
    }

    function go(url) {
      if (url) window.location.href = url;
    }

    function renderRows(results) {
      panel.innerHTML = results
        .map(function (s, i) {
          var sub = s.sector ? s.symbol + " · " + esc(s.sector) : s.symbol;
          var pill = s.deep_dive_url
            ? '<span class="pill pill-ai" data-deepdive-jump><span class="d"></span>Deep-dive</span>'
            : "";
          return (
            '<div class="row' + (i === 0 ? " is-active" : "") + '" role="option" data-index="' + i + '">' +
            '<div class="meta"><span class="name">' + esc(s.name) + '</span><span class="sub">' + sub + "</span></div>" +
            pill +
            "</div>"
          );
        })
        .join("");
    }

    function render(stocks) {
      var results = search(stocks, input.value, 8);
      currentResults = results;
      activeIndex = results.length ? 0 : -1;

      if (!input.value.trim()) {
        close();
        return;
      }
      if (!results.length) {
        panel.innerHTML = '<div class="empty">No matching stocks.</div>';
        panel.classList.add("is-open");
        return;
      }
      renderRows(results);
      panel.classList.add("is-open");
    }

    function setActive(next) {
      var rows = panel.querySelectorAll(".row");
      if (!rows.length) return;
      activeIndex = (next + rows.length) % rows.length;
      rows.forEach(function (row, idx) {
        row.classList.toggle("is-active", idx === activeIndex);
      });
      rows[activeIndex].scrollIntoView({ block: "nearest" });
    }

    input.addEventListener("input", function () {
      stocksPromise.then(render);
    });
    input.addEventListener("focus", function () {
      if (input.value.trim()) stocksPromise.then(render);
    });
    input.addEventListener("keydown", function (e) {
      if (!panel.classList.contains("is-open")) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActive(activeIndex + 1);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActive(activeIndex - 1);
      } else if (e.key === "Enter") {
        e.preventDefault();
        var s = currentResults[activeIndex];
        if (s) go(s.fundamentals_url);
      } else if (e.key === "Escape") {
        close();
        input.blur();
      }
    });

    // mousedown (not click) fires before the input's blur, so the panel is
    // still open and currentResults hasn't been cleared when we read it.
    panel.addEventListener("mousedown", function (e) {
      var row = e.target.closest(".row");
      if (!row) return;
      e.preventDefault();
      var s = currentResults[Number(row.getAttribute("data-index"))];
      if (!s) return;
      var jump = e.target.closest("[data-deepdive-jump]");
      go(jump ? s.deep_dive_url : s.fundamentals_url);
    });

    document.addEventListener("click", function (e) {
      if (!wrap.contains(e.target)) close();
    });
  });

  // Global "/" shortcut focuses the first visible search box — matches the
  // <kbd>/</kbd> hint already shown next to the header search field.
  document.addEventListener("keydown", function (e) {
    if (e.key !== "/" || e.metaKey || e.ctrlKey || e.altKey) return;
    var active = document.activeElement;
    if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.isContentEditable)) return;
    var visible = Array.prototype.filter.call(inputs, function (i) {
      return i.offsetParent !== null;
    })[0];
    if (!visible) return;
    e.preventDefault();
    visible.focus();
  });
})();

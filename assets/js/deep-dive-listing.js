// Renders the "Deep-dive reports" table on stock-analysis/index.html from
// data/deep_dive_reports.json — the manifest scripts/generate_deep_dive_shells.py
// rewrites every time a new report is added. Nothing here needs to change
// when a stock is added or removed; only the manifest does.
(function () {
  var tbody = document.getElementById("deep-dive-list");
  if (!tbody) return;

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  fetch("/data/deep_dive_reports.json")
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(function (reports) {
      if (!reports || !reports.length) {
        tbody.innerHTML = '<tr><td colspan="2"><span style="color:var(--text-muted);">No deep-dive reports yet — check back soon.</span></td></tr>';
        return;
      }
      tbody.innerHTML = reports
        .map(function (r) {
          return (
            "<tr>" +
            '<td class="name-cell"><b>' + esc(r.name) + "</b></td>" +
            '<td><a href="' + esc(r.shell_url) + '">Read report →</a></td>' +
            "</tr>"
          );
        })
        .join("");
    })
    .catch(function (err) {
      tbody.innerHTML =
        '<tr><td colspan="2"><div class="callout callout-flag"><span class="icon">!</span><div><b>Couldn’t load the report list.</b> ' +
        esc(err.message) +
        "</div></div></td></tr>";
      console.error(err);
    });
})();

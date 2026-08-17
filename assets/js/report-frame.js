// Auto-sizes an embedded deep-dive report iframe to its real content height
// so it reads as part of the page instead of a scrolling box, and swaps the
// loading state out once the frame has painted. Same-origin only — the
// report files this points at are always served from this same site.
(function () {
  document.querySelectorAll("[data-report-frame]").forEach(function (frame) {
    var wrap = frame.closest(".report-frame-wrap");

    function resize() {
      try {
        var doc = frame.contentDocument;
        if (!doc || !doc.documentElement) return;
        var h = Math.max(doc.documentElement.scrollHeight, doc.body ? doc.body.scrollHeight : 0);
        if (h > 0) frame.style.height = h + "px";
      } catch (e) {
        // cross-origin or not yet ready — leave the default height
      }
    }

    frame.addEventListener("load", function () {
      resize();
      if (wrap) wrap.classList.add("is-loaded");
      // fonts/images/chart scripts inside the report can still shift layout
      // after load fires — a couple of follow-up passes catch that.
      setTimeout(resize, 300);
      setTimeout(resize, 1200);
      try {
        var doc = frame.contentDocument;
        if (window.ResizeObserver && doc && doc.documentElement) {
          new ResizeObserver(resize).observe(doc.documentElement);
        }
      } catch (e) {}
    });
  });
})();

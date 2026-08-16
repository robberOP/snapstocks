/* SAMPLE DATA — replace with the live sector-momentum feed.
   Shape matches /snapstocks/data/sector_momentum.sample.json so the chart
   and table pages can be pointed at a real endpoint without changing
   render code. One 1W return + 1W volume ratio is hand-set per sector;
   the other four periods are derived with a small deterministic wobble
   purely so the period toggle has something plausible to show in the demo. */
(function (global) {
  var BASE = [
    { name: "Nifty Realty",             ret1w: 4.82,  vol1w: 1.28 },
    { name: "Nifty Metal",              ret1w: 3.65,  vol1w: 1.22 },
    { name: "Nifty PSU Bank",           ret1w: 2.90,  vol1w: 1.18 },
    { name: "Nifty Energy",             ret1w: 2.10,  vol1w: 1.05 },
    { name: "Nifty Auto",               ret1w: 1.35,  vol1w: 0.98 },
    { name: "Nifty Infrastructure",     ret1w: 0.85,  vol1w: 1.02 },
    { name: "Nifty Bank",               ret1w: 0.42,  vol1w: 0.95 },
    { name: "Nifty Financial Services", ret1w: 0.20,  vol1w: 0.92 },
    { name: "Nifty Oil & Gas",          ret1w: -0.35, vol1w: 0.88 },
    { name: "Nifty Consumer Durables",  ret1w: -0.60, vol1w: 0.90 },
    { name: "Nifty FMCG",               ret1w: -1.10, vol1w: 0.80 },
    { name: "Nifty Healthcare",         ret1w: -1.45, vol1w: 0.85 },
    { name: "Nifty Pharma",             ret1w: -1.95, vol1w: 0.78 },
    { name: "Nifty IT",                 ret1w: -2.80, vol1w: 0.72 },
    { name: "Nifty Media",              ret1w: -3.60, vol1w: 0.65 }
  ];

  var PERIODS = ["1d", "2d", "1w", "1m", "3m"];
  var PERIOD_SCALE = { "1d": 0.22, "2d": 0.4, "1w": 1, "1m": 1.9, "3m": 3.1 };

  function wobble(seed, i) {
    // deterministic pseudo-variation, no Math.random so the page is stable on reload
    return Math.sin(seed * 12.9898 + i * 78.233) * 0.35;
  }

  var SECTORS = BASE.map(function (s, i) {
    var ret = {}, vol = {};
    PERIODS.forEach(function (p) {
      var scale = PERIOD_SCALE[p];
      ret[p] = +(s.ret1w * scale + wobble(s.ret1w, i) * scale * 0.6).toFixed(2);
      vol[p] = +(0.85 + (s.vol1w - 0.85) * (scale / PERIOD_SCALE["1w"]) * 0.7 + 0.85 * (1 - scale / PERIOD_SCALE["1w"]) * 0.3).toFixed(2);
      if (vol[p] < 0.4) vol[p] = 0.4;
    });
    return { name: s.name, ret: ret, vol: vol };
  });

  global.SNAPSTOCKS_SECTOR_MOMENTUM = { periods: PERIODS, sectors: SECTORS };
})(window);

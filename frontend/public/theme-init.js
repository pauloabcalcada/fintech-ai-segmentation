// Set the theme class before first paint to avoid a flash of the wrong theme.
// Kept as an external file (not inline) so the page can enforce a strict
// Content-Security-Policy of script-src 'self' with no 'unsafe-inline'.
(function () {
  var t = localStorage.getItem("theme");
  document.documentElement.classList.add(t === "light" ? "light" : "dark");
})();

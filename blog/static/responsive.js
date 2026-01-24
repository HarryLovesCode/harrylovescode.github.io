// Nav toggle for small screens
(function () {
  const navToggle = document.getElementById("navToggle");
  const siteNav = document.getElementById("siteNav");
  if (!navToggle || !siteNav) return;

  function closeNav() {
    siteNav.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
    const hh = navToggle.querySelector(".icon-hamburger");
    const cc = navToggle.querySelector(".icon-close");
    if (hh) hh.style.display = "";
    if (cc) cc.style.display = "none";
  }
  function openNav() {
    siteNav.classList.add("open");
    navToggle.setAttribute("aria-expanded", "true");
    const hh = navToggle.querySelector(".icon-hamburger");
    const cc = navToggle.querySelector(".icon-close");
    if (hh) hh.style.display = "none";
    if (cc) cc.style.display = "";
  }

  navToggle.addEventListener("click", (e) => {
    const expanded = navToggle.getAttribute("aria-expanded") === "true";
    if (expanded) closeNav();
    else openNav();
  });

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (!siteNav.contains(e.target) && !navToggle.contains(e.target)) {
      closeNav();
    }
  });

  // Close when resizing to larger screens
  window.addEventListener("resize", () => {
    if (window.innerWidth > 640) closeNav();
  });

  // Close on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeNav();
  });
})();

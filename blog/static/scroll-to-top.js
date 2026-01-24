const scrollToTopBtn = document.getElementById("scrollToTopBtn");
const footer = document.querySelector(".site-footer");

function updateButtonPosition() {
  const footerRect = footer.getBoundingClientRect();
  const viewportHeight = window.innerHeight;
  const buttonHeight = scrollToTopBtn.offsetHeight;
  const padding = 2; // 2rem in pixels (16px * 2)

  // If footer is visible and would overlap the button, fade it out
  if (footerRect.top < viewportHeight - (buttonHeight + padding * 8)) {
    scrollToTopBtn.classList.add("hidden");
  } else {
    scrollToTopBtn.classList.remove("hidden");
  }
}

window.addEventListener("scroll", () => {
  if (window.pageYOffset > 300) {
    scrollToTopBtn.classList.add("visible");
  } else {
    scrollToTopBtn.classList.remove("visible");
  }
  updateButtonPosition();
});

window.addEventListener("resize", updateButtonPosition);

scrollToTopBtn.addEventListener("click", () => {
  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
});

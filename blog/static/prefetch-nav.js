// Link prefetching on hover for snappier navigation
const prefetchedLinks = new Set();

function prefetchLink(url) {
  if (prefetchedLinks.has(url)) return;
  prefetchedLinks.add(url);

  const link = document.createElement("link");
  link.rel = "prefetch";
  link.href = url;
  link.as = "document";
  document.head.appendChild(link);
}

// Add hover listeners to all internal links
document.addEventListener("mouseover", (e) => {
  const link = e.target.closest("a");
  if (!link) return;

  const href = link.getAttribute("href");
  if (!href) return;

  // Only prefetch internal links (same origin, HTML pages)
  try {
    const url = new URL(href, window.location.origin);
    if (
      url.origin === window.location.origin &&
      (href.endsWith(".html") || !href.includes("."))
    ) {
      prefetchLink(href);
    }
  } catch {
    // Invalid URL, skip
  }
});
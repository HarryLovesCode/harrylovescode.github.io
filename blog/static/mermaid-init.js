/* Extracted from template.html: mermaid initialization */
let mermaidInitialized = false;

function renderMermaid() {
  const mermaidDiagrams = document.querySelectorAll(".mermaid");
  if (mermaidDiagrams.length < 1) return;

  const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const theme = isDark ? "dark" : "default";

  if (!mermaidInitialized) {
    // Store original content before first render
    mermaidDiagrams.forEach((el) => {
      const original = el.textContent.trim();
      if (original && !original.startsWith("<")) {
        el.dataset.original = original;
      }
    });

    mermaid.initialize({ startOnLoad: false, theme });
    mermaid.run();
    mermaidInitialized = true;
  } else {
    // Update theme and re-render diagrams
    mermaid.initialize({ theme });

    document.querySelectorAll(".mermaid").forEach((el) => {
      const graphDefinition = el.dataset.original;
      if (graphDefinition) {
        el.removeAttribute("data-processed");
        el.textContent = graphDefinition;
      }
    });

    mermaid.run();
  }
}

// Render when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", renderMermaid);
} else {
  renderMermaid();
}

// Watch for theme changes
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", renderMermaid);

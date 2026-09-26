export const THEME_STORAGE_KEY = "nat-theme";
export type Theme = "dark" | "light";

export function applyTheme(theme: Theme | null) {
  const root = document.documentElement;
  if (theme) {
    root.setAttribute("data-theme", theme);
  } else {
    root.removeAttribute("data-theme");
  }
}

export function getStoredTheme(): Theme | null {
  const value = window.localStorage.getItem(THEME_STORAGE_KEY);
  return value === "dark" || value === "light" ? value : null;
}

export function setStoredTheme(theme: Theme | null) {
  if (theme) {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } else {
    window.localStorage.removeItem(THEME_STORAGE_KEY);
  }
}

// Inlined into <head> as a blocking script so the visitor's saved theme applies before
// first paint (no flash of the wrong theme). Kept as a string so it can run before any
// React/hydration code — do not import app modules into it.
export const noFlashThemeScript = `
(function () {
  try {
    var stored = window.localStorage.getItem("${THEME_STORAGE_KEY}");
    if (stored === "dark" || stored === "light") {
      document.documentElement.setAttribute("data-theme", stored);
    }
  } catch (e) {}
})();
`;

// Light / dark / system themes without a flash: an inline script in <head> (THEME_SCRIPT)
// sets data-theme before the first paint; the toggle then updates it and localStorage.

export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

const STORAGE_KEY = "repocompass-theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";

export const THEME_SCRIPT = `(function(){try{var p=localStorage.getItem("${STORAGE_KEY}")||"system";var d=p==="dark"||(p!=="light"&&matchMedia("${DARK_QUERY}").matches);var r=document.documentElement;r.setAttribute("data-theme",d?"dark":"light");r.style.colorScheme=d?"dark":"light"}catch(e){}})()`;

export function getThemePreference(): ThemePreference {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === "light" || value === "dark" ? value : "system";
  } catch {
    return "system";
  }
}

function resolve(preference: ThemePreference): ResolvedTheme {
  if (preference !== "system") return preference;
  return matchMedia(DARK_QUERY).matches ? "dark" : "light";
}

function apply(preference: ThemePreference) {
  const theme = resolve(preference);
  document.documentElement.setAttribute("data-theme", theme);
  document.documentElement.style.colorScheme = theme;
}

const listeners = new Set<() => void>();

export function setThemePreference(preference: ThemePreference) {
  try {
    localStorage.setItem(STORAGE_KEY, preference);
  } catch {
    // Private mode etc.: the theme still applies for this visit.
  }
  apply(preference);
  listeners.forEach((listener) => listener());
}

/** Subscribe to preference changes (this tab, other tabs, and OS changes while on "system"). */
export function subscribeToTheme(listener: () => void) {
  listeners.add(listener);
  const media = matchMedia(DARK_QUERY);
  const onSystemChange = () => {
    if (getThemePreference() === "system") apply("system");
    listener();
  };
  const onStorage = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY) {
      apply(getThemePreference());
      listener();
    }
  };
  media.addEventListener("change", onSystemChange);
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    media.removeEventListener("change", onSystemChange);
    window.removeEventListener("storage", onStorage);
  };
}

export function getResolvedTheme(): ResolvedTheme {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

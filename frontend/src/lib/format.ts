import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const formatNumber = (n: number) => new Intl.NumberFormat("en").format(n);

export function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} bytes`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function formatAgo(iso: string | null) {
  if (!iso) return "";
  const days = Math.round((new Date(iso).getTime() - Date.now()) / 86_400_000);
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  if (Math.abs(days) < 1) return "today";
  if (Math.abs(days) < 45) return rtf.format(days, "day");
  if (Math.abs(days) < 540) return rtf.format(Math.round(days / 30), "month");
  return rtf.format(Math.round(days / 365), "year");
}

export function formatElapsed(ms: number) {
  const seconds = Math.floor(ms / 1000);
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

/** Normalizes paths the AI writes (`./src/`, `src/*`, `` `src` ``) to how the tree stores them. */
export function cleanPath(path: string) {
  return path
    .trim()
    .replace(/^`|`$/g, "")
    .replace(/^\.\//, "")
    .replace(/\*+$/, "")
    .replace(/\/+$/, "");
}

// GitHub's own language colors, so they look familiar.
export const LANGUAGE_COLORS: Record<string, string> = {
  Python: "#3572A5", JavaScript: "#f1e05a", TypeScript: "#3178c6", Go: "#00ADD8", Rust: "#dea584",
  Java: "#b07219", Kotlin: "#A97BFF", Swift: "#F05138", "C#": "#178600", C: "#555555", "C++": "#f34b7d",
  Ruby: "#701516", PHP: "#4F5D95", Dart: "#00B4AB", HTML: "#e34c26", CSS: "#663399", SCSS: "#c6538c",
  Shell: "#89e051", Vue: "#41b883", Svelte: "#ff3e00", "Jupyter Notebook": "#DA5B0B", Dockerfile: "#384d54",
  Makefile: "#427819", Lua: "#000080", Elixir: "#6e4a7e", Scala: "#c22d40", R: "#198CE7", MDX: "#fcb32c",
};

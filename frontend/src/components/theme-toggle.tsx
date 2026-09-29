"use client";

import { Monitor, Moon, Sun } from "lucide-react";
import { useSyncExternalStore } from "react";

import { cn } from "@/lib/format";
import { getThemePreference, setThemePreference, subscribeToTheme, type ThemePreference } from "@/lib/theme";

const OPTIONS: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Light theme", icon: Sun },
  { value: "dark", label: "Dark theme", icon: Moon },
  { value: "system", label: "Match system theme", icon: Monitor },
];

export function ThemeToggle() {
  // The server can't know the saved choice, so it renders "system"; the client corrects it after hydration.
  const preference = useSyncExternalStore(subscribeToTheme, getThemePreference, () => "system" as const);

  return (
    <div role="group" aria-label="Theme" className="flex items-center gap-0.5 rounded-xl border border-line bg-surface p-0.5">
      {OPTIONS.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          type="button"
          aria-label={label}
          aria-pressed={preference === value}
          title={label}
          onClick={() => setThemePreference(value)}
          className={cn(
            "grid size-8 place-items-center rounded-lg text-muted transition-colors hover:text-fg",
            preference === value && "bg-accent-soft text-accent-text hover:text-accent-text",
          )}
        >
          <Icon className="size-4" aria-hidden />
        </button>
      ))}
    </div>
  );
}

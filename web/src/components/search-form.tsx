"use client";

import { LoaderCircle, Search, Sparkles } from "lucide-react";
import { useId, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/format";
import type { ProvidersResponse } from "@/lib/types";

export const NO_AI = "none";

interface SearchFormProps {
  url: string;
  onUrlChange: (url: string) => void;
  onSubmit: (url: string) => void;
  busy: boolean;
  compact?: boolean;
  providers: ProvidersResponse | null;
  provider: string;
  onProviderChange: (id: string) => void;
  model: string;
  onModelChange: (model: string) => void;
}

export function SearchForm({
  url, onUrlChange, onSubmit, busy, compact = false,
  providers, provider, onProviderChange, model, onModelChange,
}: SearchFormProps) {
  const id = useId();
  const current = providers?.providers.find((p) => p.id === provider);

  function submit(event: FormEvent) {
    event.preventDefault();
    const value = url.trim();
    if (value) onSubmit(value);
  }

  return (
    <form onSubmit={submit} className={cn("w-full", compact && "flex flex-col gap-2 lg:flex-row lg:items-center")}>
      <div
        className={cn(
          "flex items-center gap-2 rounded-2xl border border-line bg-surface p-1.5 pl-4 transition-shadow",
          "focus-within:border-accent focus-within:ring-4 focus-within:ring-accent/15",
          compact ? "flex-1 rounded-xl p-1 pl-3" : "shadow-sm",
        )}
      >
        <Search className={cn("shrink-0 text-muted", compact ? "size-4" : "size-5")} aria-hidden />
        <label htmlFor={`${id}-url`} className="sr-only">
          GitHub repository link
        </label>
        <input
          id={`${id}-url`}
          value={url}
          onChange={(e) => onUrlChange(e.target.value)}
          placeholder="https://github.com/owner/repo"
          inputMode="url"
          autoComplete="off"
          spellCheck={false}
          required
          className={cn(
            "min-w-0 flex-1 bg-transparent font-mono text-fg outline-none placeholder:text-muted/70",
            compact ? "h-8 text-sm" : "h-11 text-[15px]",
          )}
        />
        <Button type="submit" size={compact ? "sm" : "lg"} disabled={busy}>
          {busy && <LoaderCircle className="size-4 animate-spin" aria-hidden />}
          {busy ? "Analyzing" : compact ? "Analyze" : "Analyze repo"}
        </Button>
      </div>

      <div className={cn("flex flex-wrap items-center gap-2 text-sm", compact ? "" : "mt-3 px-1")}>
        <label htmlFor={`${id}-provider`} className="flex items-center gap-1.5 font-medium text-muted">
          <Sparkles className="size-4 text-accent" aria-hidden />
          {compact ? "Guide by" : "AI guide by"}
        </label>
        <select
          id={`${id}-provider`}
          value={provider}
          onChange={(e) => onProviderChange(e.target.value)}
          disabled={!providers}
          className="h-8 rounded-lg border border-line bg-surface px-2 text-sm text-fg outline-none hover:border-line-strong focus:border-accent"
        >
          <option value={NO_AI}>No AI (map only)</option>
          {providers?.providers.map((p) => (
            <option key={p.id} value={p.id} disabled={!p.ready}>
              {p.ready ? p.label : `${p.label} (not set up)`}
            </option>
          ))}
        </select>
        {current && (
          <>
            <label htmlFor={`${id}-model`} className="sr-only">
              Model
            </label>
            <input
              id={`${id}-model`}
              list={`${id}-models`}
              value={model}
              onChange={(e) => onModelChange(e.target.value)}
              placeholder={current.default_model}
              spellCheck={false}
              className="h-8 w-52 max-w-full rounded-lg border border-line bg-surface px-2 font-mono text-[13px] text-fg outline-none hover:border-line-strong focus:border-accent"
            />
            <datalist id={`${id}-models`}>
              {current.models.map((m) => (
                <option key={m} value={m} />
              ))}
            </datalist>
          </>
        )}
      </div>
    </form>
  );
}

/** One line explaining how to enable the providers that aren't set up yet. */
export function providerSetupNote(providers: ProvidersResponse | null) {
  if (!providers) return "";
  const needKeys = providers.providers.filter((p) => !p.ready && p.id !== "ollama").map((p) => p.label);
  const ollama = providers.providers.find((p) => p.id === "ollama");
  const notes: string[] = [];
  if (needKeys.length) {
    const names = needKeys.length > 1 ? `${needKeys.slice(0, -1).join(", ")} or ${needKeys.at(-1)}` : needKeys[0];
    notes.push(`To use ${names}, add an API key to the .env file and restart the API.`);
  }
  if (ollama && !ollama.ready) notes.push(ollama.note);
  return notes.join(" ");
}

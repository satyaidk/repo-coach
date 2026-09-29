"use client";

import { Check, Copy } from "lucide-react";
import { useEffect, useState } from "react";

export function CopyButton({ text }: { text: string }) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");

  useEffect(() => {
    if (state === "idle") return;
    const timer = setTimeout(() => setState("idle"), 1600);
    return () => clearTimeout(timer);
  }, [state]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setState("copied");
    } catch {
      setState("failed");
    }
  }

  const label = state === "copied" ? "Copied" : state === "failed" ? "Copy failed" : "Copy";
  return (
    <button
      type="button"
      onClick={copy}
      aria-label={`${label}: ${text}`}
      className="inline-flex h-7 shrink-0 items-center gap-1.5 rounded-lg border border-line px-2 text-xs font-semibold text-muted transition-colors hover:border-line-strong hover:text-fg"
    >
      {state === "copied" ? <Check className="size-3.5 text-accent-text" aria-hidden /> : <Copy className="size-3.5" aria-hidden />}
      {label}
    </button>
  );
}

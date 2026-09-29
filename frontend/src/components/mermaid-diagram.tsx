"use client";

import { useEffect, useId, useState, useSyncExternalStore } from "react";

import { getResolvedTheme, subscribeToTheme, type ResolvedTheme } from "@/lib/theme";

const THEME_VARIABLES: Record<ResolvedTheme, Record<string, string | boolean>> = {
  light: {
    background: "#ffffff",
    primaryColor: "#fcefe9",
    primaryTextColor: "#1c1917",
    primaryBorderColor: "#d97757",
    lineColor: "#a8a29e",
    secondaryColor: "#f5f4f2",
    tertiaryColor: "#ffffff",
  },
  dark: {
    darkMode: true,
    background: "#1b1a18",
    primaryColor: "#2b211d",
    primaryTextColor: "#f3f0ed",
    primaryBorderColor: "#d97757",
    lineColor: "#78716c",
    secondaryColor: "#232120",
    tertiaryColor: "#1b1a18",
  },
};

/** Models sometimes wrap diagrams in ``` fences or double-escape newlines. */
function tidy(code: string) {
  return code
    .replace(/^```(?:mermaid)?\s*/i, "")
    .replace(/```\s*$/, "")
    .replace(/\\n/g, "\n")
    .trim();
}

type Rendered = { source: string; theme: ResolvedTheme; svg: string | null };

export function MermaidDiagram({ code }: { code: string }) {
  const theme = useSyncExternalStore(subscribeToTheme, getResolvedTheme, () => "light" as const);
  const baseId = useId().replace(/[^a-zA-Z0-9]/g, "");
  const source = tidy(code);
  const [rendered, setRendered] = useState<Rendered | null>(null);

  useEffect(() => {
    let cancelled = false;
    const renderId = `diagram-${baseId}-${theme}`;
    (async () => {
      let svg: string | null = null;
      try {
        const { default: mermaid } = await import("mermaid");
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: "strict", // mermaid sanitizes labels, so the SVG is safe to insert
          theme: "base",
          fontFamily: "var(--font-manrope), system-ui, sans-serif",
          themeVariables: THEME_VARIABLES[theme],
        });
        if (await mermaid.parse(source, { suppressErrors: true })) {
          svg = (await mermaid.render(renderId, source)).svg;
        }
      } catch {
        document.getElementById(`d${renderId}`)?.remove(); // mermaid can leave an error node behind
      }
      if (!cancelled) setRendered({ source, theme, svg });
    })();
    return () => {
      cancelled = true;
    };
  }, [source, theme, baseId]);

  const current = rendered?.source === source ? rendered : null;

  if (!current) {
    return <div className="h-48 animate-pulse rounded-xl bg-surface-2" aria-label="Drawing diagram" />;
  }
  if (!current.svg) {
    return (
      <div className="rounded-xl border border-dashed border-line-strong p-4">
        <p className="text-sm text-muted">The model&apos;s diagram has a syntax error, so here&apos;s its source instead.</p>
        <pre className="mt-2 overflow-x-auto font-mono text-xs whitespace-pre-wrap">{source}</pre>
      </div>
    );
  }
  return (
    <div
      role="img"
      aria-label="Architecture diagram"
      className="diagram flex justify-center overflow-x-auto rounded-xl border border-line bg-surface p-4"
      dangerouslySetInnerHTML={{ __html: current.svg }}
    />
  );
}

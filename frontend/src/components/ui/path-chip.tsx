"use client";

import { FileText, Folder } from "lucide-react";

import { useRepoMap } from "@/components/repo-map-context";
import { cleanPath } from "@/lib/format";

/** A clickable file/folder path. Clicking opens it in the folder map; invented paths are flagged. */
export function PathChip({ path, exists = true }: { path: string; exists?: boolean }) {
  const { findNode, reveal } = useRepoMap();
  const clean = cleanPath(path);
  const node = exists ? findNode(clean) : null;

  if (!node) {
    return (
      <span
        title="The AI mentioned this path, but it isn't in the repository."
        className="inline-flex max-w-full items-center gap-1.5 rounded-md border border-dashed border-line-strong px-2 py-0.5 font-mono text-[13px] text-muted"
      >
        <span className="truncate line-through decoration-muted/60">{path}</span>
        <span className="shrink-0 font-sans text-[11px] font-semibold text-accent-text no-underline">not in repo</span>
      </span>
    );
  }

  const Icon = node.type === "dir" ? Folder : FileText;
  return (
    <button
      type="button"
      onClick={() => reveal(clean)}
      title="Show in folder map"
      className="inline-flex max-w-full items-center gap-1.5 rounded-md border border-line bg-surface-2 px-2 py-0.5 text-left font-mono text-[13px] text-fg transition-colors hover:border-accent hover:bg-accent-soft"
    >
      <Icon className="size-3.5 shrink-0 text-muted" aria-hidden />
      <span className="truncate">{clean || "/"}</span>
    </button>
  );
}

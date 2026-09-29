"use client";

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import { cleanPath } from "@/lib/format";
import type { Guide, Report, TreeNode } from "@/lib/types";

/** Everything we know about one path: shown as markers in the tree and in the detail panel. */
export interface PathNote {
  entry?: string;
  purpose?: string;
  key?: boolean;
  route?: number;
  routeTitle?: string;
}

interface RepoMapValue {
  report: Report;
  guide: Guide | null;
  notes: Map<string, PathNote>;
  selected: string | null;
  expanded: Set<string>;
  mapOpen: boolean;
  setMapOpen: (open: boolean) => void;
  findNode: (path: string) => TreeNode | null;
  toggle: (path: string) => void;
  select: (path: string) => void;
  reveal: (path: string) => void;
  githubUrl: (path: string, isDir: boolean) => string;
}

const RepoMapContext = createContext<RepoMapValue | null>(null);

export function useRepoMap() {
  const value = useContext(RepoMapContext);
  if (!value) throw new Error("useRepoMap must be used inside <RepoMapProvider>");
  return value;
}

function buildNotes(report: Report, guide: Guide | null) {
  const notes = new Map<string, PathNote>();
  const note = (path: string) => {
    const key = cleanPath(path);
    if (!notes.has(key)) notes.set(key, {});
    return notes.get(key)!;
  };
  for (const e of report.entry_points) note(e.path).entry = e.reason;
  if (guide) {
    for (const c of guide.architecture.components) if (c.exists) note(c.path).purpose ??= c.responsibility;
    for (const d of guide.directories) if (d.exists) note(d.path).purpose = d.purpose;
    for (const f of guide.key_files) if (f.exists) Object.assign(note(f.path), { purpose: f.purpose, key: true });
    guide.learning_path.forEach((step, i) => {
      for (const p of step.paths) {
        if (!p.exists) continue;
        const n = note(p.path);
        if (n.route == null) Object.assign(n, { route: i + 1, routeTitle: step.title });
      }
    });
  }
  return notes;
}

export function RepoMapProvider({
  report,
  guide,
  children,
}: {
  report: Report;
  guide: Guide | null;
  children: ReactNode;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());
  const [mapOpen, setMapOpen] = useState(true);

  const notes = useMemo(() => buildNotes(report, guide), [report, guide]);

  const findNode = useCallback(
    (path: string): TreeNode | null => {
      let node: TreeNode | undefined = report.tree;
      if (!path) return node;
      for (const part of path.split("/")) {
        node = node?.type === "dir" ? node.children.find((c) => c.name === part) : undefined;
        if (!node) return null;
      }
      return node;
    },
    [report],
  );

  const toggle = useCallback((path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }, []);

  const reveal = useCallback(
    (path: string) => {
      const node = findNode(path);
      if (!node) return;
      setExpanded((prev) => {
        const next = new Set(prev);
        const parts = path.split("/");
        for (let i = 1; i < parts.length; i++) next.add(parts.slice(0, i).join("/"));
        if (node.type === "dir") next.add(path);
        return next;
      });
      setSelected(path);
      setMapOpen(true);
      // Wait for React to render the newly expanded rows, then bring the row into view.
      requestAnimationFrame(() => {
        const row = document.querySelector<HTMLElement>(`[data-tree-path="${CSS.escape(path)}"]`);
        const smooth = !matchMedia("(prefers-reduced-motion: reduce)").matches;
        row?.scrollIntoView({ block: "center", behavior: smooth ? "smooth" : "auto" });
        row?.focus({ preventScroll: true });
      });
    },
    [findNode],
  );

  const githubUrl = useCallback(
    (path: string, isDir: boolean) => {
      const encoded = path.split("/").map(encodeURIComponent).join("/");
      return `${report.repo.url}/${isDir ? "tree" : "blob"}/${report.repo.commit_sha}/${encoded}`;
    },
    [report],
  );

  const value = useMemo(
    () => ({
      report, guide, notes, selected, expanded, mapOpen, setMapOpen,
      findNode, toggle, select: setSelected, reveal, githubUrl,
    }),
    [report, guide, notes, selected, expanded, mapOpen, findNode, toggle, reveal, githubUrl],
  );

  return <RepoMapContext.Provider value={value}>{children}</RepoMapContext.Provider>;
}

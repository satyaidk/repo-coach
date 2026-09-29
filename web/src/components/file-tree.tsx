"use client";

import { ChevronRight, ExternalLink, FileText, Folder, FolderOpen, FolderTree, Play, Star } from "lucide-react";
import { useState } from "react";

import { useRepoMap } from "@/components/repo-map-context";
import { RichText } from "@/components/ui/rich-text";
import { cn, formatNumber, formatSize } from "@/lib/format";
import type { DirNode, TreeNode } from "@/lib/types";

const CHILD_CAP = 300; // huge folders render in pages so the browser stays fast

export function FileTreePanel() {
  const { report, mapOpen, setMapOpen } = useRepoMap();

  return (
    <aside
      aria-label="Folder map"
      className="flex flex-col overflow-hidden rounded-2xl border border-line bg-surface lg:sticky lg:top-32 lg:max-h-[calc(100vh-9rem)]"
    >
      <button
        type="button"
        onClick={() => setMapOpen(!mapOpen)}
        aria-expanded={mapOpen}
        className="flex items-center gap-2 border-b border-line px-4 py-3 text-left lg:pointer-events-none"
      >
        <FolderTree className="size-4 text-accent" aria-hidden />
        <span className="font-bold">Folder map</span>
        <span className="text-sm text-muted">{formatNumber(report.stats.files)} files</span>
        <ChevronRight
          className={cn("ml-auto size-4 text-muted transition-transform lg:hidden", mapOpen && "rotate-90")}
          aria-hidden
        />
      </button>

      <div className={cn("flex min-h-0 flex-1 flex-col", !mapOpen && "hidden lg:flex")}>
        <Legend />
        <div data-tree-scroll className="max-h-[55vh] min-h-32 flex-1 overflow-auto px-2 pb-2 lg:max-h-none">
          <ul aria-label={`Files in ${report.repo.full_name}`}>
            <TreeRows node={report.tree} path="" depth={0} />
          </ul>
        </div>
        <FileDetail />
      </div>
    </aside>
  );
}

function Legend() {
  return (
    <p className="flex flex-wrap gap-x-4 gap-y-1 px-4 py-2.5 text-xs text-muted">
      <span className="inline-flex items-center gap-1.5">
        <Play className="size-3 fill-accent text-accent" aria-hidden /> starts here
      </span>
      <span className="inline-flex items-center gap-1.5">
        <RouteBadge n={1} /> on your route
      </span>
      <span className="inline-flex items-center gap-1.5">
        <Star className="size-3 fill-accent text-accent" aria-hidden /> key file
      </span>
    </p>
  );
}

function RouteBadge({ n }: { n: number }) {
  return (
    <span className="grid size-4 shrink-0 place-items-center rounded-full bg-accent-strong font-sans text-[10px] font-bold text-white">
      {n}
    </span>
  );
}

function TreeRows({ node, path, depth }: { node: DirNode; path: string; depth: number }) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? node.children : node.children.slice(0, CHILD_CAP);
  return (
    <>
      {visible.map((child) => (
        <TreeRow key={child.name} node={child} path={path ? `${path}/${child.name}` : child.name} depth={depth} />
      ))}
      {visible.length < node.children.length && (
        <li>
          <button
            type="button"
            onClick={() => setShowAll(true)}
            style={{ paddingLeft: 8 + depth * 14 }}
            className="py-1 text-left text-[13px] font-semibold text-accent-text hover:underline"
          >
            Show {formatNumber(node.children.length - visible.length)} more
          </button>
        </li>
      )}
    </>
  );
}

function TreeRow({ node, path, depth }: { node: TreeNode; path: string; depth: number }) {
  const { notes, selected, expanded, toggle, select } = useRepoMap();
  const isDir = node.type === "dir";
  const open = isDir && expanded.has(path);
  const note = notes.get(path);
  const isSelected = selected === path;
  const FolderIcon = open ? FolderOpen : Folder;

  return (
    <li>
      <button
        type="button"
        data-tree-path={path}
        aria-expanded={isDir ? open : undefined}
        aria-current={isSelected || undefined}
        onClick={() => {
          if (isDir) toggle(path);
          select(path);
        }}
        style={{ paddingLeft: 8 + depth * 14 }}
        className={cn(
          "flex w-full items-center gap-1.5 rounded-lg py-1 pr-2 text-left font-mono text-[13px] transition-colors",
          isSelected ? "bg-accent-soft text-accent-text" : "hover:bg-surface-2",
        )}
      >
        {isDir ? (
          <ChevronRight className={cn("size-3.5 shrink-0 text-muted transition-transform", open && "rotate-90")} aria-hidden />
        ) : (
          <span className="w-3.5 shrink-0" />
        )}
        {isDir ? (
          <FolderIcon className="size-4 shrink-0 text-accent" aria-hidden />
        ) : (
          <FileText className="size-4 shrink-0 text-muted" aria-hidden />
        )}
        <span className={cn("truncate", note?.key && "font-semibold")}>{node.name}</span>
        {note?.entry && <Play className="size-3 shrink-0 fill-accent text-accent" aria-label="starts here" />}
        {note?.route && <RouteBadge n={note.route} />}
        {note?.key && <Star className="size-3 shrink-0 fill-accent text-accent" aria-label="key file" />}
        {isDir && <span className="ml-auto pl-2 font-sans text-[11px] text-muted">{formatNumber(node.count)}</span>}
      </button>
      {open && (
        <ul>
          <TreeRows node={node} path={path} depth={depth + 1} />
        </ul>
      )}
    </li>
  );
}

function FileDetail() {
  const { selected, findNode, notes, guide, githubUrl } = useRepoMap();
  const node = selected ? findNode(selected) : null;

  if (!selected || !node) {
    return (
      <p className="border-t border-line px-4 py-3 text-sm text-muted">Select a file or folder to see what it does.</p>
    );
  }

  const isDir = node.type === "dir";
  const note = notes.get(selected);
  const hasNotes = note?.entry || note?.route || note?.purpose;

  return (
    <div className="max-h-[35vh] space-y-2 overflow-auto border-t border-line px-4 py-3 text-sm">
      <p className="font-mono text-[13px] font-semibold break-all">{isDir ? `${selected}/` : selected}</p>
      <p className="text-xs text-muted">
        {isDir ? `Folder with ${formatNumber(node.count)} files` : `File, ${formatSize(node.size)}`}
      </p>
      {note?.entry && (
        <p>
          <span className="font-semibold">Starts here. </span>
          <RichText text={note.entry} />
        </p>
      )}
      {note?.route && (
        <p>
          <span className="font-semibold">Stop {note.route} on your route: </span>
          {note.routeTitle}
        </p>
      )}
      {note?.purpose && (
        <p className="text-muted">
          <RichText text={note.purpose} />
        </p>
      )}
      {!hasNotes && guide && (
        <p className="text-muted">The guide doesn&apos;t describe this one. Open it and skim the top of the file.</p>
      )}
      <a
        href={githubUrl(selected, isDir)}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1 font-semibold text-accent-text hover:underline"
      >
        Open on GitHub <ExternalLink className="size-3.5" aria-hidden />
      </a>
    </div>
  );
}

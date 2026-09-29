"use client";

import { Archive, Clock, ExternalLink, Files, GitBranch, GitFork, Scale, Star, TriangleAlert } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { useRepoMap } from "@/components/repo-map-context";
import { formatAgo, formatNumber, LANGUAGE_COLORS } from "@/lib/format";

function Stat({ icon: Icon, children }: { icon: LucideIcon; children: ReactNode }) {
  return (
    <li className="inline-flex items-center gap-1.5">
      <Icon className="size-4 text-muted" aria-hidden />
      <span>{children}</span>
    </li>
  );
}

export function RepoHeader() {
  const { report } = useRepoMap();
  const { repo, stats, languages } = report;
  const license = repo.license && repo.license !== "NOASSERTION" ? repo.license : "";

  return (
    <header className="rounded-2xl border border-line bg-surface p-5 sm:p-7">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="text-2xl font-extrabold tracking-tight break-words sm:text-3xl">
            <span className="font-semibold text-muted">{repo.owner}/</span>
            {repo.name}
          </h1>
          {repo.description && <p className="mt-2 max-w-3xl leading-relaxed text-muted">{repo.description}</p>}
        </div>
        <a
          href={repo.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex h-9 shrink-0 items-center gap-2 self-start rounded-xl border border-line px-3.5 text-sm font-semibold transition-colors hover:border-line-strong hover:bg-surface-2"
        >
          View on GitHub <ExternalLink className="size-3.5" aria-hidden />
        </a>
      </div>

      <ul className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-sm">
        <Stat icon={Star}>
          <b>{formatNumber(repo.stars)}</b> stars
        </Stat>
        <Stat icon={GitFork}>
          <b>{formatNumber(repo.forks)}</b> forks
        </Stat>
        {license && (
          <Stat icon={Scale}>
            <b>{license}</b> license
          </Stat>
        )}
        <Stat icon={Files}>
          <b>{formatNumber(stats.files)}</b> files in <b>{formatNumber(stats.dirs)}</b> folders
        </Stat>
        {repo.pushed_at && (
          <Stat icon={Clock}>
            Updated <b>{formatAgo(repo.pushed_at)}</b>
          </Stat>
        )}
        <Stat icon={GitBranch}>
          <b>{repo.ref}</b> at <code className="font-mono text-xs">{repo.commit_sha.slice(0, 7)}</code>
        </Stat>
      </ul>

      {languages.length > 0 && (
        <ul className="mt-4 flex flex-wrap gap-x-4 gap-y-1.5 border-t border-line pt-4 text-sm" aria-label="Languages">
          {languages.slice(0, 8).map((lang) => (
            <li key={lang.name} className="inline-flex items-center gap-1.5">
              <span
                className="size-2.5 rounded-full"
                style={{ background: LANGUAGE_COLORS[lang.name] ?? "var(--muted)" }}
                aria-hidden
              />
              <span className="font-medium">{lang.name}</span>
              <span className="text-muted">{lang.percent < 0.1 ? "<0.1" : lang.percent}%</span>
            </li>
          ))}
        </ul>
      )}

      {repo.archived && (
        <p className="mt-4 flex items-start gap-2 rounded-xl bg-surface-2 p-3 text-sm">
          <Archive className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
          This repository is archived: it&apos;s read-only and won&apos;t accept contributions. It&apos;s still fine for learning.
        </p>
      )}
      {report.tree_truncated && (
        <p className="mt-4 flex items-start gap-2 rounded-xl bg-surface-2 p-3 text-sm">
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
          This repository is so big that GitHub only returned part of its file list, so the map is incomplete.
        </p>
      )}
    </header>
  );
}

"use client";

import { BookOpen, LoaderCircle, RotateCcw, Sparkles, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";

import { useRepoMap } from "@/components/repo-map-context";
import { Button } from "@/components/ui/button";
import { RichText } from "@/components/ui/rich-text";
import { SectionCard } from "@/components/ui/section-card";
import { cn, formatElapsed } from "@/lib/format";

export type GuideState =
  | { status: "skipped" }
  | { status: "pending"; model: string; startedAt: number }
  | { status: "error"; model: string; message: string }
  | { status: "done" };

const DIFFICULTY = {
  beginner: { label: "Beginner friendly", dot: "bg-emerald-500" },
  intermediate: { label: "Intermediate", dot: "bg-amber-500" },
  advanced: { label: "Advanced", dot: "bg-rose-500" },
};

export function OverviewSection() {
  const { report, guide } = useRepoMap();
  const summary = guide?.overview.summary || report.repo.description;
  const difficulty = guide?.overview.difficulty ? DIFFICULTY[guide.overview.difficulty] : null;

  return (
    <SectionCard id="overview" icon={BookOpen} title="What this project is">
      {summary ? (
        <p className="text-[17px] leading-relaxed">
          <RichText text={summary} />
        </p>
      ) : (
        <p className="text-muted">This repository has no description.</p>
      )}
      {guide?.overview.problem && (
        <p className="mt-3 leading-relaxed text-muted">
          <RichText text={guide.overview.problem} />
        </p>
      )}
      {difficulty && (
        <div className="mt-5 flex items-start gap-3 rounded-xl bg-surface-2 p-4">
          <span className={cn("mt-1.5 size-2.5 shrink-0 rounded-full", difficulty.dot)} aria-hidden />
          <p className="text-sm">
            <span className="font-bold">{difficulty.label} for newcomers. </span>
            <span className="text-muted">
              <RichText text={guide!.overview.difficulty_reason} />
            </span>
          </p>
        </div>
      )}
      {report.repo.topics.length > 0 && (
        <ul className="mt-5 flex flex-wrap gap-1.5" aria-label="Topics">
          {report.repo.topics.map((topic) => (
            <li key={topic} className="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-semibold text-accent-text">
              {topic}
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

function Elapsed({ since }: { since: number }) {
  const [now, setNow] = useState(since);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  return <span className="font-mono text-sm text-muted tabular-nums">{formatElapsed(Math.max(0, now - since))}</span>;
}

/** Shown above the sections while the AI guide is missing: writing, failed, or turned off. */
export function GuideStatus({ state, onRetry }: { state: GuideState; onRetry: () => void }) {
  if (state.status === "done") return null;

  if (state.status === "pending") {
    return (
      <div className="space-y-4">
        <div role="status" className="flex items-start gap-4 rounded-2xl border border-accent/40 bg-accent-soft p-5">
          <LoaderCircle className="mt-0.5 size-5 shrink-0 animate-spin text-accent" aria-hidden />
          <div className="min-w-0 flex-1">
            <p className="font-bold">Writing the guide with {state.model}</p>
            <p className="mt-1 text-sm text-muted">
              The reading route, architecture and folder explanations will appear here. Local models on a laptop can
              take several minutes. The map and facts are ready now.
            </p>
          </div>
          <Elapsed since={state.startedAt} />
        </div>
        <div className="space-y-3 rounded-2xl border border-line bg-surface p-6" aria-hidden>
          <div className="h-4 w-1/3 animate-pulse rounded bg-surface-2" />
          <div className="h-3 w-full animate-pulse rounded bg-surface-2" />
          <div className="h-3 w-5/6 animate-pulse rounded bg-surface-2" />
          <div className="h-3 w-2/3 animate-pulse rounded bg-surface-2" />
        </div>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div role="alert" className="flex flex-col gap-4 rounded-2xl border border-red-300 bg-red-50 p-5 sm:flex-row sm:items-start dark:border-red-900/70 dark:bg-red-950/30">
        <TriangleAlert className="size-5 shrink-0 text-red-600 dark:text-red-400" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="font-bold text-red-800 dark:text-red-200">{state.model} couldn&apos;t write the guide</p>
          <p className="mt-1 text-sm break-words text-red-800/80 dark:text-red-200/80">
            <RichText text={state.message} />
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={onRetry}>
          <RotateCcw className="size-3.5" aria-hidden /> Try again
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-4 rounded-2xl border border-dashed border-line-strong p-5">
      <Sparkles className="size-5 shrink-0 text-accent" aria-hidden />
      <p className="text-sm text-muted">
        <span className="font-bold text-fg">You mapped this repo without AI. </span>
        Pick a model under &ldquo;Guide by&rdquo; and analyze it again to get the reading route, architecture and folder
        explanations.
      </p>
    </div>
  );
}

"use client";

import { Flag, Route } from "lucide-react";

import { useRepoMap } from "@/components/repo-map-context";
import { PathChip } from "@/components/ui/path-chip";
import { RichText } from "@/components/ui/rich-text";
import { SectionCard } from "@/components/ui/section-card";

export function RouteSection() {
  const { guide } = useRepoMap();
  if (!guide?.learning_path.length) return null;

  return (
    <SectionCard
      id="route"
      icon={Route}
      title="Your route through the code"
      description="Read these in order. Each stop is numbered in the folder map too."
    >
      <ol className="relative">
        {/* The line joining the stops draws itself in once. */}
        <span aria-hidden className="absolute top-4 bottom-4 left-[15px] w-0.5 origin-top animate-draw-down bg-accent/50" />
        {guide.learning_path.map((step, i) => (
          <li key={i} className="relative flex gap-4 pb-6">
            <span className="z-10 grid size-8 shrink-0 place-items-center rounded-full bg-accent-strong text-sm font-bold text-white ring-4 ring-surface">
              {i + 1}
            </span>
            <div className="min-w-0 pt-1">
              <h3 className="font-bold">{step.title}</h3>
              {step.why && (
                <p className="mt-1 text-sm leading-relaxed text-muted">
                  <RichText text={step.why} />
                </p>
              )}
              {step.paths.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {step.paths.map((p) => (
                    <PathChip key={p.path} path={p.path} exists={p.exists} />
                  ))}
                </div>
              )}
            </div>
          </li>
        ))}
        <li className="relative flex gap-4">
          <span className="z-10 grid size-8 shrink-0 place-items-center rounded-full border-2 border-accent bg-surface text-accent ring-4 ring-surface">
            <Flag className="size-4" aria-hidden />
          </span>
          <div className="pt-1">
            <h3 className="font-bold">Pick a first contribution</h3>
            <a href="#contributing" className="mt-1 inline-block text-sm font-semibold text-accent-text hover:underline">
              See where to start contributing
            </a>
          </div>
        </li>
      </ol>
    </SectionCard>
  );
}

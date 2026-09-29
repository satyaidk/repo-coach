"use client";

import { Network, Workflow } from "lucide-react";

import { MermaidDiagram } from "@/components/mermaid-diagram";
import { useRepoMap } from "@/components/repo-map-context";
import { PathChip } from "@/components/ui/path-chip";
import { RichText } from "@/components/ui/rich-text";
import { SectionCard, SubHeading } from "@/components/ui/section-card";

function NumberedSteps({ steps }: { steps: string[] }) {
  return (
    <ol className="space-y-3">
      {steps.map((step, i) => (
        <li key={i} className="flex gap-3">
          <span className="grid size-6 shrink-0 place-items-center rounded-full bg-accent-soft text-xs font-bold text-accent-text">
            {i + 1}
          </span>
          <p className="pt-0.5 text-[15px] leading-relaxed">
            <RichText text={step} />
          </p>
        </li>
      ))}
    </ol>
  );
}

export function ArchitectureSection() {
  const { guide } = useRepoMap();
  if (!guide) return null;
  const { summary, mermaid, components, data_flow } = guide.architecture;
  if (!summary && !mermaid && !components.length && !data_flow.length) return null;

  return (
    <SectionCard id="architecture" icon={Network} title="How it's built">
      {summary && (
        <p className="leading-relaxed">
          <RichText text={summary} />
        </p>
      )}
      {mermaid && (
        <div className="mt-5">
          <MermaidDiagram code={mermaid} />
        </div>
      )}
      {components.length > 0 && (
        <>
          <SubHeading>Main parts</SubHeading>
          <ul className="grid gap-3 sm:grid-cols-2">
            {components.map((c, i) => (
              <li key={i} className="rounded-xl border border-line p-4">
                <p className="font-bold">{c.name}</p>
                {c.path && (
                  <div className="mt-1.5">
                    <PathChip path={c.path} exists={c.exists} />
                  </div>
                )}
                {c.responsibility && (
                  <p className="mt-2 text-sm leading-relaxed text-muted">
                    <RichText text={c.responsibility} />
                  </p>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
      {data_flow.length > 0 && (
        <>
          <SubHeading>How data moves through it</SubHeading>
          <NumberedSteps steps={data_flow} />
        </>
      )}
    </SectionCard>
  );
}

export function HowItWorksSection() {
  const { guide } = useRepoMap();
  if (!guide?.how_it_works.length) return null;
  return (
    <SectionCard id="how-it-works" icon={Workflow} title="How it works, step by step">
      <NumberedSteps steps={guide.how_it_works} />
    </SectionCard>
  );
}

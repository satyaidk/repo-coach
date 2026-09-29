"use client";

import { BookA, CircleCheck, CircleDashed, CircleDot, ExternalLink, GitPullRequest, Lightbulb } from "lucide-react";

import { useRepoMap } from "@/components/repo-map-context";
import { PathChip } from "@/components/ui/path-chip";
import { RichText } from "@/components/ui/rich-text";
import { SectionCard, SubHeading } from "@/components/ui/section-card";
import type { CommunityKey } from "@/lib/types";

const CHECKS: [CommunityKey, string][] = [
  ["readme", "README"],
  ["contributing", "Contributing guide"],
  ["code_of_conduct", "Code of conduct"],
  ["license", "License"],
  ["issue_templates", "Issue templates"],
  ["pr_template", "Pull request template"],
  ["tests", "Tests"],
  ["ci", "Automated checks (CI)"],
];

export function ContributingSection() {
  const { report, guide, githubUrl } = useRepoMap();
  const { community, good_first_issues, repo } = report;
  const contribution = guide?.contribution;
  const found = CHECKS.filter(([key]) => community[key]).length;

  return (
    <SectionCard
      id="contributing"
      icon={GitPullRequest}
      title="Contributing"
      description={`${found} of ${CHECKS.length} things that help newcomers are in place.`}
    >
      <ul className="grid gap-2 sm:grid-cols-2">
        {CHECKS.map(([key, label]) => {
          const path = community[key];
          return (
            <li key={key} className="flex items-center gap-2.5 text-sm">
              {path ? (
                <>
                  <CircleCheck className="size-4 shrink-0 text-accent" aria-label="Found" />
                  <a
                    href={githubUrl(path, false)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium hover:text-accent-text hover:underline"
                  >
                    {label}
                  </a>
                </>
              ) : (
                <>
                  <CircleDashed className="size-4 shrink-0 text-muted" aria-label="Not found" />
                  <span className="text-muted">{label} not found</span>
                </>
              )}
            </li>
          );
        })}
      </ul>

      {contribution?.setup_steps.length ? (
        <>
          <SubHeading>Get it running</SubHeading>
          <ol className="list-decimal space-y-1.5 pl-5 text-[15px] leading-relaxed marker:font-semibold marker:text-accent-text">
            {contribution.setup_steps.map((step, i) => (
              <li key={i} className="pl-1">
                <RichText text={step} />
              </li>
            ))}
          </ol>
        </>
      ) : null}

      {contribution?.starter_areas.length ? (
        <>
          <SubHeading>Good places to start</SubHeading>
          <ul className="space-y-3">
            {contribution.starter_areas.map((area) => (
              <li key={area.path}>
                <PathChip path={area.path} exists={area.exists} />
                {area.why && (
                  <p className="mt-1 text-sm leading-relaxed text-muted">
                    <RichText text={area.why} />
                  </p>
                )}
              </li>
            ))}
          </ul>
        </>
      ) : null}

      <SubHeading>Open issues for newcomers</SubHeading>
      {good_first_issues.length ? (
        <ul className="divide-y divide-line rounded-xl border border-line">
          {good_first_issues.map((issue) => (
            <li key={issue.number}>
              <a
                href={issue.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-start gap-3 px-4 py-3 transition-colors hover:bg-surface-2"
              >
                <CircleDot className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
                <span className="min-w-0 flex-1">
                  <span className="text-sm font-semibold">{issue.title}</span>
                  <span className="mt-1 flex flex-wrap gap-1.5">
                    <span className="text-xs text-muted">#{issue.number}</span>
                    {issue.labels.map((label) => (
                      <span key={label} className="rounded-full bg-accent-soft px-2 text-xs font-medium text-accent-text">
                        {label}
                      </span>
                    ))}
                  </span>
                </span>
                <ExternalLink className="size-3.5 shrink-0 text-muted" aria-hidden />
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted">
          No open issues are labeled &ldquo;good first issue&rdquo; or &ldquo;help wanted&rdquo; right now.{" "}
          <a href={`${repo.url}/issues`} target="_blank" rel="noopener noreferrer" className="font-semibold text-accent-text hover:underline">
            Browse all issues
          </a>
        </p>
      )}

      {contribution?.tips.length ? (
        <>
          <SubHeading>Tips for your first pull request</SubHeading>
          <ul className="space-y-2">
            {contribution.tips.map((tip, i) => (
              <li key={i} className="flex gap-2.5 text-[15px] leading-relaxed">
                <Lightbulb className="mt-1 size-4 shrink-0 text-accent" aria-hidden />
                <span>
                  <RichText text={tip} />
                </span>
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </SectionCard>
  );
}

export function GlossarySection() {
  const { guide } = useRepoMap();
  if (!guide?.glossary.length) return null;
  return (
    <SectionCard id="glossary" icon={BookA} title="Words to know">
      <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-[minmax(8rem,max-content)_1fr]">
        {guide.glossary.map((item) => (
          <div key={item.term} className="contents">
            <dt className="font-bold">{item.term}</dt>
            <dd className="text-[15px] leading-relaxed text-muted">
              <RichText text={item.meaning} />
            </dd>
          </div>
        ))}
      </dl>
    </SectionCard>
  );
}

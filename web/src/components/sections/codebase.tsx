"use client";

import { FolderTree, Layers, Play, Terminal } from "lucide-react";

import { useRepoMap } from "@/components/repo-map-context";
import { CopyButton } from "@/components/ui/copy-button";
import { PathChip } from "@/components/ui/path-chip";
import { RichText } from "@/components/ui/rich-text";
import { SectionCard, SubHeading } from "@/components/ui/section-card";

export function EntryPointsSection() {
  const { report } = useRepoMap();
  const { entry_points, run_commands } = report;

  return (
    <SectionCard
      id="entry-points"
      icon={Play}
      title="Where it starts"
      description="Found by looking for the files programs in this language usually start from."
    >
      {entry_points.length ? (
        <ul className="divide-y divide-line">
          {entry_points.map((e) => (
            <li key={e.path} className="flex flex-col gap-1.5 py-3 first:pt-0 sm:flex-row sm:items-center sm:gap-4">
              <div className="sm:w-2/5 sm:shrink-0">
                <PathChip path={e.path} />
              </div>
              <p className="text-sm text-muted">
                <RichText text={e.reason} />
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted">No obvious entry file. This may be a library, docs or config repository.</p>
      )}

      {run_commands.length > 0 && (
        <>
          <SubHeading>
            <span className="inline-flex items-center gap-2">
              <Terminal className="size-4 text-accent" aria-hidden /> Commands to run it
            </span>
          </SubHeading>
          <ul className="space-y-2">
            {run_commands.map((c) => (
              <li key={c.command} className="flex items-center gap-3 rounded-xl bg-surface-2 px-4 py-2.5">
                <div className="min-w-0 flex-1">
                  <code className="font-mono text-sm break-all">
                    <span className="mr-2 text-accent select-none" aria-hidden>
                      $
                    </span>
                    {c.command}
                  </code>
                  <p className="mt-0.5 truncate text-xs text-muted" title={c.note}>
                    {c.note ? `${c.note} ` : ""}(from {c.source})
                  </p>
                </div>
                <CopyButton text={c.command} />
              </li>
            ))}
          </ul>
        </>
      )}
    </SectionCard>
  );
}

const CATEGORY_ORDER = ["Language", "Framework", "Library", "Database & ORM", "Testing", "Build & Tooling", "DevOps & Infra"];

export function StackSection() {
  const { report } = useRepoMap();
  const groups = CATEGORY_ORDER.map((category) => ({
    category,
    items: report.stack.filter((s) => s.category === category),
  })).filter((g) => g.items.length);

  return (
    <SectionCard
      id="stack"
      icon={Layers}
      title="What it's built with"
      description="Read from the repository's config files, not guessed."
    >
      {groups.length ? (
        <dl className="grid gap-4 sm:grid-cols-[10rem_1fr] sm:gap-x-6">
          {groups.map(({ category, items }) => (
            <div key={category} className="contents">
              <dt className="pt-1 text-sm font-semibold text-muted">{category}</dt>
              <dd className="flex flex-wrap gap-1.5">
                {items.map((s) => (
                  <span
                    key={s.name}
                    title={`Found in ${s.source}`}
                    className="rounded-lg border border-line bg-surface-2 px-2.5 py-1 text-sm font-medium"
                  >
                    {s.name}
                  </span>
                ))}
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="text-sm text-muted">No known frameworks or tools were detected from config files.</p>
      )}

      {report.dependencies.map((d) => (
        <details key={d.source} className="group mt-5 rounded-xl border border-line">
          <summary className="cursor-pointer list-none px-4 py-3 text-sm font-semibold marker:hidden">
            <span className="text-accent-text group-open:hidden">Show</span>
            <span className="hidden text-accent-text group-open:inline">Hide</span> all {d.total} dependencies in{" "}
            <code className="font-mono text-[13px]">{d.source}</code>
          </summary>
          <p className="border-t border-line px-4 py-3 font-mono text-xs leading-6 break-words text-muted">
            {d.names.join("   ")}
          </p>
        </details>
      ))}
    </SectionCard>
  );
}

export function FoldersSection() {
  const { guide } = useRepoMap();
  if (!guide || (!guide.directories.length && !guide.key_files.length)) return null;

  const list = (items: { path: string; exists: boolean; purpose: string }[]) => (
    <ul className="divide-y divide-line">
      {items.map((item) => (
        <li key={item.path} className="flex flex-col gap-1.5 py-3 first:pt-0 sm:flex-row sm:items-start sm:gap-4">
          <div className="sm:w-2/5 sm:shrink-0">
            <PathChip path={item.path} exists={item.exists} />
          </div>
          {item.purpose && (
            <p className="text-sm leading-relaxed text-muted">
              <RichText text={item.purpose} />
            </p>
          )}
        </li>
      ))}
    </ul>
  );

  return (
    <SectionCard id="folders" icon={FolderTree} title="Folders and key files">
      {guide.directories.length > 0 && (
        <>
          <SubHeading>Folders</SubHeading>
          {list(guide.directories)}
        </>
      )}
      {guide.key_files.length > 0 && (
        <>
          <SubHeading>Files worth knowing</SubHeading>
          {list(guide.key_files)}
        </>
      )}
    </SectionCard>
  );
}

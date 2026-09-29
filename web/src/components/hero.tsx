import { FolderTree, GitPullRequest, Play, Route } from "lucide-react";
import type { ReactNode } from "react";

const FEATURES = [
  { icon: FolderTree, title: "Folder map", text: "Every file and folder, with the important ones marked." },
  { icon: Play, title: "Where it starts", text: "The entry-point files and the commands to install, run and test it." },
  { icon: Route, title: "A reading route", text: "Which files to read first, in order, numbered on the map." },
  { icon: GitPullRequest, title: "First contribution", text: "How newcomer-friendly it is, setup steps and starter issues." },
];

export const EXAMPLES = ["pallets/flask", "expressjs/express", "gin-gonic/gin"];

export function Hero({
  form,
  notice,
  onExample,
}: {
  form: ReactNode;
  notice: ReactNode;
  onExample: (repo: string) => void;
}) {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 pt-14 pb-20 sm:pt-24">
      <div className="mx-auto max-w-3xl text-center">
        <h1 className="text-4xl leading-[1.08] font-extrabold tracking-tight text-balance sm:text-6xl">
          Understand any GitHub repo before you dive in
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-pretty text-muted">
          Paste a repository link. You&apos;ll get its folder map, the files where it starts, the tech it uses, and a
          reading route from your first file to your first contribution.
        </p>
      </div>

      <div className="mx-auto mt-10 max-w-3xl">
        {form}
        {notice}
        <p className="mt-5 flex flex-wrap items-center justify-center gap-2 text-sm text-muted">
          Try one:
          {EXAMPLES.map((repo) => (
            <button
              key={repo}
              type="button"
              onClick={() => onExample(repo)}
              className="rounded-full border border-line bg-surface px-3 py-1 font-mono text-[13px] text-fg transition-colors hover:border-accent hover:text-accent-text"
            >
              {repo}
            </button>
          ))}
        </p>
      </div>

      <ul className="mt-20 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map(({ icon: Icon, title, text }) => (
          <li key={title} className="rounded-2xl border border-line bg-surface p-5">
            <span className="grid size-10 place-items-center rounded-xl bg-accent-soft text-accent-text">
              <Icon className="size-5" aria-hidden />
            </span>
            <h2 className="mt-4 font-bold">{title}</h2>
            <p className="mt-1 text-sm leading-relaxed text-muted">{text}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

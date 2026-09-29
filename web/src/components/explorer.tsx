"use client";

import { Info, RefreshCw, TriangleAlert } from "lucide-react";
import { useEffect, useEffectEvent, useRef, useState, type MouseEvent } from "react";

import { FileTreePanel } from "@/components/file-tree";
import { Hero } from "@/components/hero";
import { Logo } from "@/components/logo";
import { RepoHeader } from "@/components/repo-header";
import { RepoMapProvider } from "@/components/repo-map-context";
import { NO_AI, providerSetupNote, SearchForm } from "@/components/search-form";
import { SectionNav, type NavItem } from "@/components/section-nav";
import { ArchitectureSection, HowItWorksSection } from "@/components/sections/architecture";
import { EntryPointsSection, FoldersSection, StackSection } from "@/components/sections/codebase";
import { ContributingSection, GlossarySection } from "@/components/sections/contributing";
import { GuideStatus, OverviewSection, type GuideState } from "@/components/sections/overview";
import { RouteSection } from "@/components/sections/route";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { cn } from "@/lib/format";
import type { ExplainResult, Guide, ProvidersResponse, Report } from "@/lib/types";

const PROVIDER_KEY = "repocompass-provider";
const modelKey = (provider: string) => `repocompass-model:${provider}`;

const storage = {
  get(key: string) {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  set(key: string, value: string) {
    try {
      localStorage.setItem(key, value);
    } catch {
      // Private mode etc.: the choice just isn't remembered.
    }
  },
};

const toUrl = (repo: string) => (repo.includes("github.com") ? repo : `https://github.com/${repo}`);
const messageOf = (error: unknown) => (error instanceof Error ? error.message : String(error));

type Notice = { tone: "info" | "error"; text: string };

function navItems(guide: Guide | null): NavItem[] {
  const arch = guide?.architecture;
  return [
    { id: "overview", label: "Overview", show: true },
    { id: "route", label: "Reading route", show: !!guide?.learning_path.length },
    { id: "architecture", label: "Architecture", show: !!(arch && (arch.summary || arch.mermaid || arch.components.length)) },
    { id: "how-it-works", label: "How it works", show: !!guide?.how_it_works.length },
    { id: "entry-points", label: "Where it starts", show: true },
    { id: "stack", label: "Tech stack", show: true },
    { id: "folders", label: "Folders & files", show: !!(guide?.directories.length || guide?.key_files.length) },
    { id: "contributing", label: "Contributing", show: true },
    { id: "glossary", label: "Glossary", show: !!guide?.glossary.length },
  ]
    .filter((item) => item.show)
    .map(({ id, label }) => ({ id, label }));
}

function NoticeBanner({ notice }: { notice: Notice }) {
  const error = notice.tone === "error";
  const Icon = error ? TriangleAlert : Info;
  return (
    <p
      role={error ? "alert" : "status"}
      className={cn(
        "mt-4 flex items-start gap-2.5 rounded-xl border p-3.5 text-sm",
        error
          ? "border-red-300 bg-red-50 text-red-800 dark:border-red-900/70 dark:bg-red-950/30 dark:text-red-200"
          : "border-line bg-surface text-muted",
      )}
    >
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <span className="break-words">{notice.text}</span>
    </p>
  );
}

export function Explorer() {
  const [providers, setProviders] = useState<ProvidersResponse | null>(null);
  const [provider, setProvider] = useState(NO_AI);
  const [model, setModel] = useState("");
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [guideState, setGuideState] = useState<GuideState>({ status: "skipped" });
  const [guideResult, setGuideResult] = useState<ExplainResult | null>(null);

  // Each analysis gets an id, so a slow guide for an old repo can't land on a newer one.
  const runRef = useRef(0);
  const repoUrlRef = useRef("");

  async function writeGuide(target: string, providerId: string, modelName: string, refresh: boolean, runId: number) {
    const info = providers?.providers.find((p) => p.id === providerId);
    const label = modelName.trim() || info?.default_model || providerId;
    setGuideState({ status: "pending", model: label, startedAt: Date.now() });
    try {
      const result = await api.explain(target, providerId, modelName.trim() || null, refresh);
      if (runId !== runRef.current) return;
      setGuideResult(result);
      setGuideState({ status: "done" });
    } catch (error) {
      if (runId !== runRef.current) return;
      setGuideState({ status: "error", model: label, message: messageOf(error) });
    }
  }

  async function analyze(target: string, providerId = provider, modelName = model) {
    const runId = ++runRef.current;
    setBusy(true);
    setNotice(null);
    try {
      const data = await api.analyze(target);
      if (runId !== runRef.current) return;
      repoUrlRef.current = target;
      setReport(data);
      setGuideResult(null);
      setGuideState({ status: "skipped" });
      setBusy(false); // you can analyze another repo while the guide is being written
      window.history.replaceState(null, "", `?repo=${encodeURIComponent(data.repo.full_name)}`);
      document.title = `${data.repo.full_name} · RepoCompass`;
      window.scrollTo({ top: 0 });
      if (providerId !== NO_AI) await writeGuide(target, providerId, modelName, false, runId);
    } catch (error) {
      if (runId !== runRef.current) return;
      setBusy(false);
      setNotice({ tone: "error", text: messageOf(error) });
    }
  }

  function rewriteGuide() {
    if (provider === NO_AI) {
      setNotice({ tone: "info", text: "Pick an AI provider under “Guide by” first." });
      return;
    }
    writeGuide(repoUrlRef.current, provider, model, true, runRef.current);
  }

  function goHome(event: MouseEvent) {
    event.preventDefault();
    runRef.current++;
    setReport(null);
    setBusy(false);
    setNotice(null);
    window.history.replaceState(null, "", "/");
    document.title = "RepoCompass";
  }

  function changeProvider(id: string) {
    setProvider(id);
    setModel(id === NO_AI ? "" : (storage.get(modelKey(id)) ?? ""));
    storage.set(PROVIDER_KEY, id);
  }

  function changeModel(value: string) {
    setModel(value);
    storage.set(modelKey(provider), value.trim());
  }

  // Runs once providers are known: restore the saved choice, then open a shared ?repo= link.
  const onProvidersLoaded = useEffectEvent((data: ProvidersResponse | null) => {
    let chosen = NO_AI;
    let chosenModel = "";
    if (data) {
      setProviders(data);
      const saved = storage.get(PROVIDER_KEY);
      const ready = data.providers.filter((p) => p.ready);
      const pick = ready.find((p) => p.id === saved) ?? ready.find((p) => p.id === data.default) ?? ready[0];
      chosen = saved === NO_AI || !pick ? NO_AI : pick.id;
      chosenModel = chosen === NO_AI ? "" : (storage.get(modelKey(chosen)) ?? "");
      setProvider(chosen);
      setModel(chosenModel);
    }
    const shared = new URLSearchParams(window.location.search).get("repo");
    if (shared) {
      setUrl(toUrl(shared));
      analyze(toUrl(shared), chosen, chosenModel);
    }
  });

  useEffect(() => {
    let cancelled = false;
    api
      .providers()
      .then((data) => !cancelled && onProvidersLoaded(data))
      .catch((error) => {
        if (cancelled) return;
        setNotice({ tone: "error", text: messageOf(error) });
        onProvidersLoaded(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const guide = guideState.status === "done" ? (guideResult?.guide ?? null) : null;
  const setupNote = providerSetupNote(providers);

  const form = (
    <SearchForm
      url={url}
      onUrlChange={setUrl}
      onSubmit={(value) => analyze(value)}
      busy={busy}
      compact={!!report}
      providers={providers}
      provider={provider}
      onProviderChange={changeProvider}
      model={model}
      onModelChange={changeModel}
    />
  );

  return (
    <div className="flex min-h-screen flex-col">
      <header className="z-30 border-b border-line bg-bg/85 backdrop-blur-md lg:sticky lg:top-0">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3 lg:h-16 lg:flex-nowrap lg:py-0">
          <a href="/" onClick={goHome} aria-label="RepoCompass home" className="rounded-lg">
            <Logo />
          </a>
          {report && <div className="order-last w-full lg:order-none lg:w-auto lg:flex-1">{form}</div>}
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="flex-1">
        {!report ? (
          <Hero
            form={form}
            notice={
              <>
                {notice && <NoticeBanner notice={notice} />}
                {setupNote && <p className="mt-3 px-1 text-xs text-muted">{setupNote}</p>}
              </>
            }
            onExample={(repo) => {
              setUrl(toUrl(repo));
              analyze(toUrl(repo));
            }}
          />
        ) : (
          <RepoMapProvider key={`${report.repo.full_name}@${report.repo.commit_sha}`} report={report} guide={guide}>
            <div className="mx-auto max-w-7xl px-4 py-6">
              {notice && <NoticeBanner notice={notice} />}
              <div className="mt-2">
                <RepoHeader />
              </div>

              <div className="z-20 -mx-4 mt-4 border-b border-line bg-bg/85 px-4 py-2 backdrop-blur-md lg:sticky lg:top-16">
                <div className="flex items-center gap-3">
                  <div className="min-w-0 flex-1">
                    <SectionNav items={navItems(guide)} />
                  </div>
                  {guideState.status === "done" && guideResult && (
                    <div className="hidden shrink-0 items-center gap-2 text-xs text-muted md:flex">
                      <span>
                        Guide by <b className="font-semibold text-fg">{guideResult.model}</b>
                        {guideResult.cached && " (saved copy)"}
                      </span>
                      <Button variant="ghost" size="sm" onClick={rewriteGuide} title="Write a fresh guide with the selected model">
                        <RefreshCw className="size-3.5" aria-hidden /> Rewrite
                      </Button>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-5 grid items-start gap-5 lg:grid-cols-[320px_minmax(0,1fr)] xl:grid-cols-[360px_minmax(0,1fr)]">
                <FileTreePanel />
                <div className="min-w-0 space-y-5">
                  <GuideStatus state={guideState} onRetry={rewriteGuide} />
                  <OverviewSection />
                  <RouteSection />
                  <ArchitectureSection />
                  <HowItWorksSection />
                  <EntryPointsSection />
                  <StackSection />
                  <FoldersSection />
                  <ContributingSection />
                  <GlossarySection />
                </div>
              </div>
            </div>
          </RepoMapProvider>
        )}
      </main>

      <footer className="border-t border-line">
        <p className="mx-auto max-w-7xl px-4 py-6 text-xs leading-relaxed text-muted">
          The folder map, stack, entry points and commands are read straight from the repository&apos;s files. The
          written guide comes from an AI model and can be wrong; any path it mentions that doesn&apos;t exist is marked{" "}
          <span className="font-semibold text-accent-text">not in repo</span>.
        </p>
      </footer>
    </div>
  );
}

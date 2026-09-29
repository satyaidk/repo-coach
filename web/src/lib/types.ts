// Shapes of the JSON returned by the FastAPI backend (repocompass/).

export interface DirNode {
  name: string;
  type: "dir";
  count: number;
  children: TreeNode[];
}

export interface FileNode {
  name: string;
  type: "file";
  size: number;
}

export type TreeNode = DirNode | FileNode;

export type CommunityKey =
  | "readme"
  | "contributing"
  | "code_of_conduct"
  | "license"
  | "security"
  | "issue_templates"
  | "pr_template"
  | "tests"
  | "ci";

export interface Report {
  repo: {
    owner: string;
    name: string;
    full_name: string;
    description: string;
    url: string;
    homepage: string;
    stars: number;
    forks: number;
    open_issues: number;
    license: string;
    topics: string[];
    archived: boolean;
    default_branch: string;
    ref: string;
    commit_sha: string;
    pushed_at: string | null;
  };
  languages: { name: string; percent: number }[];
  stats: {
    files: number;
    dirs: number;
    size_bytes: number;
    max_depth: number;
    top_extensions: { ext: string; count: number }[];
  };
  tree: DirNode;
  tree_truncated: boolean;
  stack: { name: string; category: string; source: string }[];
  dependencies: { source: string; names: string[]; total: number }[];
  entry_points: { path: string; reason: string }[];
  run_commands: { command: string; source: string; note: string }[];
  community: Record<CommunityKey, string | null>;
  good_first_issues: { number: number; title: string; url: string; labels: string[]; comments: number }[];
}

export interface CheckedPath {
  path: string;
  exists: boolean;
}

export interface Guide {
  overview: {
    summary: string;
    problem: string;
    difficulty: "" | "beginner" | "intermediate" | "advanced";
    difficulty_reason: string;
  };
  architecture: {
    summary: string;
    components: (CheckedPath & { name: string; responsibility: string })[];
    data_flow: string[];
    mermaid: string;
  };
  how_it_works: string[];
  directories: (CheckedPath & { purpose: string })[];
  key_files: (CheckedPath & { purpose: string })[];
  learning_path: { title: string; why: string; paths: CheckedPath[] }[];
  contribution: {
    setup_steps: string[];
    starter_areas: (CheckedPath & { why: string })[];
    tips: string[];
  };
  glossary: { term: string; meaning: string }[];
}

export interface ExplainResult {
  provider: string;
  model: string;
  generated_at: string;
  cached: boolean;
  guide: Guide;
}

export interface ProviderInfo {
  id: string;
  label: string;
  ready: boolean;
  default_model: string;
  models: string[];
  note: string;
}

export interface ProvidersResponse {
  default: string;
  providers: ProviderInfo[];
}

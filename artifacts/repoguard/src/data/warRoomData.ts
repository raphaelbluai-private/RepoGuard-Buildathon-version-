export type RiskCategory =
  | "Secrets Exposure"
  | "Workflow Failure"
  | "Missing Environment Variable"
  | "Unsafe Shell Execution"
  | "Deployment Blocker"
  | "Dependency Risk"
  | "Permission Scope Risk";

export type Severity = "critical" | "high" | "medium" | "low";

export type RiskStatus = "open" | "fixing" | "resolved";

export type GateState = "pass" | "warning" | "fail";

export interface Risk {
  id: string;
  category: RiskCategory;
  severity: Severity;
  file: string;
  status: RiskStatus;
  shortExplanation: string;
  whatBroke: string;
  whyMatters: string;
  howToFix: string;
  fixPlan: string[];
}

export interface SafetyGate {
  id: string;
  label: string;
  state: GateState;
  detail?: string;
}

export interface AgentTraceStep {
  step: string;
  detail: string;
  t: string;
}

export const SCORE_BEFORE = 38;
export const SCORE_AFTER  = 96;

export const PROJECT_NAME = "repoguard-warroom-demo";

// Five deterministic seeded risks — one per category requested.
export const SEEDED_RISKS: Risk[] = [
  {
    id: "r1",
    category: "Secrets Exposure",
    severity: "critical",
    file: "src/api/openai-client.ts",
    status: "open",
    shortExplanation: "Hardcoded OpenAI API key committed to source",
    whatBroke:
      "An OpenAI API key (sk-…) was committed directly into source at line 12 of src/api/openai-client.ts. The string matches the OpenAI key regex used by gitleaks.",
    whyMatters:
      "Anyone with read access to the repo (including bots that scrape public repos within minutes of push) can exfiltrate the key and rack up charges or pivot into other systems that share the credential.",
    howToFix:
      "Move the key to a runtime secret, rotate the leaked credential at the provider, and add the file to your secret-scanner allowlist so the same pattern is caught pre-commit.",
    fixPlan: [
      "Generate a new key in dashboard.openai.com",
      "Add OPENAI_API_KEY to Replit Secrets",
      "Replace the literal value with process.env.OPENAI_API_KEY",
      "Revoke the leaked key at the provider",
      "Add a pre-commit hook that runs gitleaks on staged files",
    ],
  },
  {
    id: "r2",
    category: "Workflow Failure",
    severity: "high",
    file: ".github/workflows/deploy.yml",
    status: "open",
    shortExplanation: "Deploy workflow grants unscoped GH_TOKEN",
    whatBroke:
      "The deploy workflow runs with the default GITHUB_TOKEN at full repo:write scope and has no `permissions:` block.",
    whyMatters:
      "A compromised step (malicious dependency, supply-chain attack) can push to main, modify protected branches, or rewrite history because the token has more power than the job actually needs.",
    howToFix:
      "Add an explicit `permissions:` block at job level, granting only the minimum scope each step requires.",
    fixPlan: [
      "Add `permissions:` block at workflow root",
      "Set `contents: read` for build job",
      "Set `contents: write` only on the deploy job",
      "Remove unused secrets from the secrets list",
      "Re-run the workflow and confirm it still passes",
    ],
  },
  {
    id: "r3",
    category: "Missing Environment Variable",
    severity: "high",
    file: "backend/app.py",
    status: "open",
    shortExplanation: "DATABASE_URL referenced but undeclared",
    whatBroke:
      "backend/app.py reads os.environ['DATABASE_URL'] at startup, but the variable is not in .env.example or Replit Secrets for the deploy environment.",
    whyMatters:
      "Production will crash on the first request with a KeyError before any user-friendly error page can render. Users will see a 502 with no path to recovery.",
    howToFix:
      "Document DATABASE_URL in .env.example, set it in Replit Secrets for production, and add a startup check that exits with a clear message if it's missing.",
    fixPlan: [
      "Add DATABASE_URL=<placeholder> to .env.example",
      "Set DATABASE_URL in Replit Secrets for production",
      "Replace os.environ[...] with os.environ.get + fail-fast guard",
      "Update README under 'Required env vars'",
      "Re-run scan",
    ],
  },
  {
    id: "r4",
    category: "Unsafe Shell Execution",
    severity: "critical",
    file: "scripts/build.sh",
    status: "open",
    shortExplanation: "User input piped to shell via eval",
    whatBroke:
      "scripts/build.sh line 18 calls `eval` on $BUILD_TARGET which is sourced from a query parameter passed to the deploy webhook.",
    whyMatters:
      "Any caller of the webhook can execute arbitrary shell commands on the build host — a textbook command injection that escalates to full server compromise.",
    howToFix:
      "Replace eval with an allowlist lookup. Validate $BUILD_TARGET strictly. Never pass untrusted input to a shell.",
    fixPlan: [
      "Remove the eval call on line 18",
      "Define ALLOWED_TARGETS=(web mobile docs)",
      "Match input against the allowlist; reject otherwise",
      "Add a regression test that fails on `; rm -rf /`",
      "Re-run scan",
    ],
  },
  {
    id: "r5",
    category: "Deployment Blocker",
    severity: "high",
    file: ".replit",
    status: "open",
    shortExplanation: "[deployment] block missing — Publish will fail",
    whatBroke:
      ".replit has no [deployment] section, so the Publish flow has no build or run command to execute.",
    whyMatters:
      "Pressing Publish results in an immediate build error. The app cannot ship to production at all until this is corrected.",
    howToFix:
      "Add a [deployment] block with explicit build and run commands matching this project's package manager.",
    fixPlan: [
      "Open .replit",
      "Add [deployment] section",
      "Set build = ['pnpm', 'build']",
      "Set run = ['pnpm', 'start']",
      "Test build locally with `pnpm build`",
    ],
  },
];

// Pre-fix and post-fix gate snapshots
export const GATES_BEFORE: SafetyGate[] = [
  { id: "g1", label: "No exposed secrets",                    state: "fail",    detail: "1 critical secret detected" },
  { id: "g2", label: "Required env vars documented",          state: "warning", detail: "DATABASE_URL undeclared" },
  { id: "g3", label: "Workflow files validated",              state: "fail",    detail: "deploy.yml uses unscoped token" },
  { id: "g4", label: "No unauthorized shell execution",       state: "fail",    detail: "eval on user input in build.sh" },
  { id: "g5", label: "Build command verified",                state: "fail",    detail: "[deployment] block missing" },
  { id: "g6", label: "Preview route healthy",                 state: "pass",    detail: "200 OK on /" },
  { id: "g7", label: "Critical risks resolved",               state: "fail",    detail: "2 critical risks open" },
];

export const GATES_AFTER: SafetyGate[] = [
  { id: "g1", label: "No exposed secrets",                    state: "pass",    detail: "Key rotated · scanner clean" },
  { id: "g2", label: "Required env vars documented",          state: "pass",    detail: "All vars in .env.example" },
  { id: "g3", label: "Workflow files validated",              state: "pass",    detail: "Permissions block in place" },
  { id: "g4", label: "No unauthorized shell execution",       state: "pass",    detail: "Allowlist enforced" },
  { id: "g5", label: "Build command verified",                state: "pass",    detail: "[deployment] block valid" },
  { id: "g6", label: "Preview route healthy",                 state: "pass",    detail: "200 OK on /" },
  { id: "g7", label: "Critical risks resolved",               state: "pass",    detail: "0 critical risks open" },
];

export const AGENT_BUILD_TRACE: AgentTraceStep[] = [
  { step: "Prompt received",      detail: "War Room scan requested",                t: "00:00" },
  { step: "Repo scanned",         detail: "127 files analyzed across 3 sources",    t: "00:08" },
  { step: "Risks classified",     detail: "5 risks across 5 categories",            t: "00:11" },
  { step: "Fix plan generated",   detail: "Deterministic fix plans per risk",       t: "00:14" },
  { step: "Checklist validated",  detail: "7 safety gates evaluated",               t: "00:16" },
  { step: "Report generated",     detail: "Safe-to-Ship report ready",              t: "00:18" },
];

export const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "#FCA5A5",
  high:     "#FCD34D",
  medium:   "#93C5FD",
  low:      "#6EE7B7",
};

export const GATE_COLOR: Record<GateState, string> = {
  pass:    "#6EE7B7",
  warning: "#FCD34D",
  fail:    "#FCA5A5",
};

export const GATE_ICON: Record<GateState, string> = {
  pass:    "✓",
  warning: "!",
  fail:    "✕",
};

export const CATEGORY_ICON: Record<RiskCategory, string> = {
  "Secrets Exposure":              "🔑",
  "Workflow Failure":              "⚙",
  "Missing Environment Variable":  "✦",
  "Unsafe Shell Execution":        "⚠",
  "Deployment Blocker":            "🚫",
  "Dependency Risk":               "📦",
  "Permission Scope Risk":         "🛡",
};

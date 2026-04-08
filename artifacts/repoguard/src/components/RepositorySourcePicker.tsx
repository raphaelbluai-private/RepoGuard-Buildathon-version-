import { useMemo, useState } from "react";
import { ChevronDown, Search, Check, Shield, AlertTriangle, ShieldAlert } from "lucide-react";

const REPO_PLATFORMS = [
  {
    group: "Code Hosting Platforms",
    options: ["GitHub", "GitLab", "Bitbucket", "Gitea / Gogs", "Codeberg", "SourceForge"],
  },
  {
    group: "Enterprise & Cloud",
    options: ["Azure DevOps", "Google Cloud Source Repositories", "AWS CodeCommit", "OneDev", "SourceHut"],
  },
  {
    group: "DevOps Platforms",
    options: ["CloudBees Platform", "Azure Pipelines"],
  },
  {
    group: "CI/CD & Deployment",
    options: ["Harness", "Octopus Deploy", "Bitrise"],
  },
  {
    group: "Infrastructure as Code",
    options: ["AWS CloudFormation", "Red Hat Ansible Automation Platform"],
  },
  {
    group: "Code Review & Quality",
    options: ["CodeRabbit", "CodeAnt AI", "CodeScene", "Qodo"],
  },
  {
    group: "Security",
    options: ["Snyk"],
  },
  {
    group: "Cloud Dev Environments",
    options: ["Google Cloud Workstations", "AWS Cloud9", "Coder"],
  },
  {
    group: "AI Coding Assistants",
    options: ["Amazon Q Developer", "Gemini Code Assist", "Cursor", "Windsurf", "Claude", "Augment Code", "Launchpad"],
  },
];

const PRIMARY_REPO_PLATFORMS = [
  "GitHub",
  "GitLab",
  "Bitbucket",
  "Azure DevOps",
  "AWS CodeCommit",
  "Coder",
];

export type RepoItem = {
  id: string;
  name: string;
  status?: "secure" | "warning" | "breach";
};

type Props = {
  repos: RepoItem[];
  selectedPlatform: string | null;
  selectedRepo: RepoItem | null;
  onPlatformChange: (platform: string) => void;
  onRepoChange: (repo: RepoItem) => void;
  onScan: () => void;
};

function StatusIcon({ status }: { status?: RepoItem["status"] }) {
  if (status === "breach") return <ShieldAlert className="h-3.5 w-3.5 text-red-400" />;
  if (status === "warning") return <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />;
  return <Shield className="h-3.5 w-3.5 text-emerald-400" />;
}

export function RepositorySourcePicker({
  repos,
  selectedPlatform,
  selectedRepo,
  onPlatformChange,
  onRepoChange,
  onScan,
}: Props) {
  const [platformOpen, setPlatformOpen] = useState(false);
  const [platformQuery, setPlatformQuery] = useState("");
  const [repoQuery, setRepoQuery] = useState("");

  const filteredGroups = useMemo(() => {
    const q = platformQuery.trim().toLowerCase();
    if (!q) return REPO_PLATFORMS;
    return REPO_PLATFORMS
      .map((group) => ({
        ...group,
        options: group.options.filter((option) =>
          option.toLowerCase().includes(q)
        ),
      }))
      .filter((group) => group.options.length > 0);
  }, [platformQuery]);

  const filteredRepos = useMemo(() => {
    const q = repoQuery.trim().toLowerCase();
    if (!q) return repos;
    return repos.filter((repo) => repo.name.toLowerCase().includes(q));
  }, [repoQuery, repos]);

  return (
    <div className="w-full space-y-4">
      <div className="space-y-1">
        <label className="text-sm font-semibold tracking-wide text-[#F8F4ED]">
          Repository Source
        </label>
        <p className="text-xs text-white/60">
          Choose where the repository is housed, then select the repository to scan.
        </p>
      </div>

      <div className="rounded-2xl border border-white/10 bg-[#111111]/70 p-4 shadow-[0_12px_40px_rgba(0,0,0,0.18)]">
        {/* Quick-pick primary platforms */}
        <div className="mb-4 flex flex-wrap gap-2">
          {PRIMARY_REPO_PLATFORMS.map((platform) => {
            const active = selectedPlatform === platform;
            return (
              <button
                key={platform}
                type="button"
                onClick={() => {
                  onPlatformChange(platform);
                  setPlatformOpen(false);
                }}
                className={[
                  "rounded-full px-4 py-2 text-sm font-medium transition-all duration-150",
                  active
                    ? "bg-[#C49A47] text-[#111111] shadow-[0_8px_24px_rgba(196,154,71,0.25)]"
                    : "border border-white/10 bg-white/5 text-white hover:border-[#C49A47]/35 hover:bg-white/10",
                ].join(" ")}
              >
                {platform}
              </button>
            );
          })}

          <button
            type="button"
            onClick={() => setPlatformOpen((v) => !v)}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white transition-all duration-150 hover:border-[#C49A47]/35 hover:bg-white/10"
          >
            More Sources
            <ChevronDown className={`h-4 w-4 transition-transform duration-150 ${platformOpen ? "rotate-180" : ""}`} />
          </button>
        </div>

        {/* Expanded platform browser */}
        {platformOpen && (
          <div className="mb-4 rounded-2xl border border-[#C49A47]/20 bg-[#0F2C4F]/80 p-4 shadow-[0_12px_40px_rgba(0,0,0,0.18)]">
            <div className="relative mb-4">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/45" />
              <input
                value={platformQuery}
                onChange={(e) => setPlatformQuery(e.target.value)}
                placeholder="Search source platforms..."
                className="w-full rounded-xl border border-white/10 bg-[#111111]/70 py-3 pl-10 pr-4 text-sm text-white outline-none placeholder:text-white/35 focus:border-[#C49A47]/50"
              />
            </div>

            <div className="max-h-80 space-y-4 overflow-auto pr-1">
              {filteredGroups.length === 0 ? (
                <div className="px-2 py-6 text-sm text-white/50">No platforms found.</div>
              ) : (
                filteredGroups.map((group) => (
                  <div key={group.group} className="space-y-2">
                    <div className="text-[11px] uppercase tracking-[0.12em] text-[#C49A47]">
                      {group.group}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {group.options.map((option) => {
                        const active = selectedPlatform === option;
                        return (
                          <button
                            key={option}
                            type="button"
                            onClick={() => {
                              onPlatformChange(option);
                              setPlatformOpen(false);
                              setPlatformQuery("");
                            }}
                            className={[
                              "inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm transition-all duration-150",
                              active
                                ? "bg-[#C49A47] text-[#111111]"
                                : "border border-white/10 bg-white/5 text-white hover:border-[#C49A47]/35 hover:bg-white/10",
                            ].join(" ")}
                          >
                            {active && <Check className="h-3.5 w-3.5" />}
                            {option}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Repo picker — shown once a platform is selected */}
        {selectedPlatform && (
          <div className="space-y-3">
            <div className="text-sm font-medium text-[#F8F4ED]">
              Select repository from{" "}
              <span className="text-[#C49A47]">{selectedPlatform}</span>
            </div>

            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/45" />
              <input
                value={repoQuery}
                onChange={(e) => setRepoQuery(e.target.value)}
                placeholder="Search repositories..."
                className="w-full rounded-xl border border-white/10 bg-[#111111]/70 py-3 pl-10 pr-4 text-sm text-white outline-none placeholder:text-white/35 focus:border-[#C49A47]/50"
              />
            </div>

            <div className="max-h-72 overflow-auto rounded-2xl border border-white/10 bg-[#111111]/40 p-2">
              {filteredRepos.length === 0 ? (
                <div className="px-3 py-6 text-sm text-white/50">
                  No repositories found.
                </div>
              ) : (
                filteredRepos.map((repo) => {
                  const active = selectedRepo?.id === repo.id;
                  return (
                    <button
                      key={repo.id}
                      type="button"
                      onClick={() => onRepoChange(repo)}
                      className={[
                        "flex w-full items-center justify-between rounded-xl px-4 py-3 text-left transition-all duration-150",
                        active
                          ? "bg-[#C49A47]/15 ring-1 ring-[#C49A47]/40"
                          : "hover:bg-white/5",
                      ].join(" ")}
                    >
                      <div className="flex items-center gap-2.5">
                        <StatusIcon status={repo.status} />
                        <span className={`text-sm font-medium ${active ? "text-[#C49A47]" : "text-white"}`}>
                          {repo.name}
                        </span>
                      </div>
                      {active && <Check className="h-4 w-4 text-[#C49A47]" />}
                    </button>
                  );
                })
              )}
            </div>

            {selectedRepo && (
              <button
                type="button"
                onClick={onScan}
                className="w-full rounded-xl bg-[#C49A47] py-3 text-sm font-bold text-[#111111] shadow-[0_8px_24px_rgba(196,154,71,0.20)] transition-all duration-150 hover:brightness-110 active:scale-[0.98]"
              >
                Scan {selectedRepo.name}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

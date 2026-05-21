export type ExtensionSeverity = "critical" | "high" | "medium" | "low";
export type ExtensionGuardStatus = "LOW" | "REVIEW" | "HIGH" | "BLOCK";

export interface ExtensionInventoryItem {
  id: string;
  publisher: string;
  name: string;
  version: string | null;
  rawLine: string;
}

export interface ExtensionFinding {
  id: string;
  extensionId: string;
  publisher: string;
  name: string;
  version: string | null;
  severity: ExtensionSeverity;
  ruleId: string;
  whatBroke: string;
  whyMatters: string;
  howToFix: string;
  confidence: "high" | "medium" | "low";
  evidence: string;
}

export interface ExtensionGuardResult {
  ok: true;
  scanMode: "extension_inventory";
  scanTime: string;
  extensionsScanned: number;
  highRiskCount: number;
  unknownPublisherCount: number;
  toolingRiskScore: number;
  status: ExtensionGuardStatus;
  inventory: ExtensionInventoryItem[];
  findings: ExtensionFinding[];
  recommendations: string[];
}

const TRUSTED_PUBLISHERS = new Set(["ms-python", "ms-vscode", "ms-vscode-remote", "ms-azuretools", "ms-toolsai", "github", "dbaeumer", "esbenp", "redhat", "eamodio", "streetsidesoftware", "bradlc"]);
const GENERIC_PUBLISHERS = new Set(["dev", "developer", "tools", "extension", "extensions", "publisher", "admin", "security", "sync", "auth", "crypto", "remote"]);
const HIGH_RISK_KEYWORDS = ["credential", "wallet", "ssh", "auth", "key", "crypto", "sync", "remote", "proxy"];
const POPULAR_IDS = ["ms-python.python", "dbaeumer.vscode-eslint", "esbenp.prettier-vscode", "github.copilot", "github.copilot-chat", "ms-azuretools.vscode-docker", "ms-toolsai.jupyter", "ms-python.vscode-pylance", "ms-vscode-remote.remote-ssh", "ms-vscode-remote.remote-containers"];
const POPULAR_TERMS = ["python", "eslint", "prettier", "copilot", "docker", "jupyter", "pylance", "remote-ssh"];

function normalizeLine(rawLine: string): string {
  return rawLine.trim().replace(/^code\s+--install-extension\s+/i, "").trim();
}

export function parseExtensionInventory(input: string): ExtensionInventoryItem[] {
  const seen = new Set<string>();
  return input.split(/\r?\n/).map(normalizeLine).filter(line => line && !line.startsWith("#")).filter(line => {
    const key = line.toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  }).map(line => {
    const [idPart, versionPart] = line.split("@");
    const id = (idPart || "").trim().toLowerCase();
    const [publisher = "", ...nameParts] = id.split(".");
    return { id, publisher: publisher.trim(), name: nameParts.join(".").trim(), version: versionPart ? versionPart.trim() : null, rawLine: line };
  });
}

function mkFinding(item: ExtensionInventoryItem, index: number, severity: ExtensionSeverity, ruleId: string, whatBroke: string, whyMatters: string, howToFix: string, confidence: "high" | "medium" | "low", evidence: string): ExtensionFinding {
  return { id: `ext-${index}-${ruleId.toLowerCase()}`, extensionId: item.id || item.rawLine, publisher: item.publisher || "unknown", name: item.name || "unknown", version: item.version, severity, ruleId, whatBroke, whyMatters, howToFix, confidence, evidence };
}

function nearPopularName(name: string): string | null {
  const clean = name.replace(/[-_.]/g, "");
  for (const term of POPULAR_TERMS) {
    const normalizedTerm = term.replace(/[-_.]/g, "");
    if (clean.includes(normalizedTerm)) return term;
    if (Math.abs(clean.length - normalizedTerm.length) <= 2) {
      let misses = 0;
      for (let i = 0; i < Math.max(clean.length, normalizedTerm.length); i++) if (clean[i] !== normalizedTerm[i]) misses++;
      if (misses <= 2) return term;
    }
  }
  return null;
}

export function scanExtensions(input: string): ExtensionGuardResult {
  const inventory = parseExtensionInventory(input);
  const findings: ExtensionFinding[] = [];
  const nameToPublishers = new Map<string, Set<string>>();
  inventory.forEach(item => {
    if (!item.name) return;
    const bucket = nameToPublishers.get(item.name) ?? new Set<string>();
    bucket.add(item.publisher || "unknown");
    nameToPublishers.set(item.name, bucket);
  });

  inventory.forEach((item, index) => {
    const id = item.id.toLowerCase();
    const publisher = item.publisher.toLowerCase();
    const name = item.name.toLowerCase();
    if (!publisher || !name || !id.includes(".")) findings.push(mkFinding(item, index, "high", "EXT_MISSING_PUBLISHER", "Extension line is missing publisher.extension structure.", "Missing publisher identity makes provenance review unreliable.", "Verify the exact extension id from the official marketplace before use.", "high", `rawLine=${item.rawLine}`));
    if (!item.version) findings.push(mkFinding(item, index, "low", "EXT_VERSION_MISSING", "Extension version is missing from the inventory.", "Without a version, the report cannot separate stable builds from newly updated builds.", "Run code --list-extensions --show-versions and rescan.", "high", `extension=${item.id || item.rawLine}`));
    if (publisher && !TRUSTED_PUBLISHERS.has(publisher)) {
      const generic = GENERIC_PUBLISHERS.has(publisher);
      findings.push(mkFinding(item, index, generic ? "high" : "medium", generic ? "EXT_GENERIC_PUBLISHER" : "EXT_UNKNOWN_PUBLISHER", generic ? "Extension publisher uses a generic high-risk name." : "Extension publisher is outside RepoGuard's local trusted baseline.", "Unknown or generic publishers increase developer-tooling supply-chain risk.", "Verify publisher reputation, install count, source repository, and recent update history before use.", generic ? "high" : "medium", `publisher=${item.publisher}`));
    }
    const keyword = HIGH_RISK_KEYWORDS.find(k => id.includes(k));
    if (keyword) findings.push(mkFinding(item, index, ["credential", "wallet", "ssh", "auth", "key"].includes(keyword) ? "high" : "medium", "EXT_HIGH_RISK_KEYWORD", `Extension id contains high-risk keyword ${keyword}.`, "Extensions related to credentials, wallets, SSH, auth, sync, remote access, or proxies have elevated exposure potential.", "Review permissions and remove the extension from sensitive workspaces unless verified.", "medium", `extensionId=${item.id}`));
    const publishersForName = nameToPublishers.get(item.name);
    if (publishersForName && publishersForName.size > 1) findings.push(mkFinding(item, index, "high", "EXT_DUPLICATE_NAME_DIFFERENT_PUBLISHER", "Same extension name appears under multiple publishers.", "Duplicate extension names can indicate lookalike tooling.", "Keep only the verified official publisher and remove duplicates.", "high", `name=${item.name}; publishers=${Array.from(publishersForName).join(",")}`));
    const popularTerm = nearPopularName(name);
    if (popularTerm && !POPULAR_IDS.includes(id)) findings.push(mkFinding(item, index, "medium", "EXT_MIMICS_POPULAR_EXTENSION", `Extension name resembles popular tool ${popularTerm} but is not in the trusted id list.`, "Lookalike naming is a common supply-chain deception pattern.", "Compare the id and publisher against the official marketplace listing before enabling it.", "medium", `extensionId=${item.id}; similarTerm=${popularTerm}`));
  });

  const critical = findings.filter(f => f.severity === "critical").length;
  const high = findings.filter(f => f.severity === "high").length;
  const medium = findings.filter(f => f.severity === "medium").length;
  const low = findings.filter(f => f.severity === "low").length;
  const unknownPublisherCount = findings.filter(f => f.ruleId === "EXT_UNKNOWN_PUBLISHER" || f.ruleId === "EXT_GENERIC_PUBLISHER").length;
  const toolingRiskScore = Math.min(100, critical * 35 + high * 22 + medium * 10 + low * 3);
  const status: ExtensionGuardStatus = toolingRiskScore >= 80 || critical > 0 ? "BLOCK" : toolingRiskScore >= 56 || high > 1 ? "HIGH" : toolingRiskScore >= 26 || high > 0 || medium > 0 ? "REVIEW" : "LOW";
  return { ok: true, scanMode: "extension_inventory", scanTime: new Date().toISOString(), extensionsScanned: inventory.length, highRiskCount: critical + high, unknownPublisherCount, toolingRiskScore, status, inventory, findings, recommendations: findings.length === 0 ? ["No deterministic ExtensionGuard risks found in pasted inventory."] : ["Disable or remove high-risk extensions until publisher reputation is verified.", "Re-run code --list-extensions --show-versions after cleanup.", "Review recent commits and run the RepoGuard live repo scanner again after tooling cleanup."] };
}

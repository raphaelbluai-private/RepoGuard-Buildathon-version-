import React, { useState, useEffect } from "react";
import {
  SEEDED_RISKS,
  GATES_BEFORE,
  GATES_AFTER,
  AGENT_BUILD_TRACE,
  SCORE_BEFORE,
  SCORE_AFTER,
  PROJECT_NAME,
  SEVERITY_COLOR,
  GATE_COLOR,
  GATE_ICON,
  CATEGORY_ICON,
  RISK_STATUS_LABEL,
  RISK_STATUS_COLOR,
  coerceRiskStatus,
  type Risk,
  type RiskStatus,
  type SafetyGate,
  type ScanResult,
  type ScanResponse,
} from "../data/warRoomData";

interface WarRoomProps {
  theme: string;
}

type ScanMode =
  | { kind: "idle" }
  | { kind: "scanning"; repo: string }
  | { kind: "real"; data: ScanResult }
  | { kind: "sample" }
  | { kind: "error"; error: string; message: string };

const WAR_ROOM_STORAGE_KEY = "repoguard.warRoom.v2";

type PersistedWarRoomState = {
  scanMode: ScanMode;
  fixesApplied: boolean;
  selectedRiskId: string | null;
  statusOverrides: Record<string, RiskStatus>;
  repoInput: string;
};

function loadPersistedState(): PersistedWarRoomState | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(WAR_ROOM_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return null;

    // Only restore terminal scan modes ("sample" or "real"). The transient
    // "scanning" and "error" states are not worth replaying after a refresh.
    let scanMode: ScanMode = { kind: "idle" };
    const sm = parsed.scanMode;
    if (sm && typeof sm === "object" && typeof sm.kind === "string") {
      if (sm.kind === "sample") {
        scanMode = { kind: "sample" };
      } else if (sm.kind === "real" && sm.data && typeof sm.data === "object") {
        scanMode = { kind: "real", data: sm.data as ScanResult };
      }
    }

    return {
      scanMode,
      fixesApplied: Boolean(parsed.fixesApplied),
      selectedRiskId:
        typeof parsed.selectedRiskId === "string" ? parsed.selectedRiskId : null,
      statusOverrides:
        parsed.statusOverrides && typeof parsed.statusOverrides === "object"
          ? (parsed.statusOverrides as Record<string, RiskStatus>)
          : {},
      repoInput: typeof parsed.repoInput === "string" ? parsed.repoInput : "",
    };
  } catch {
    return null;
  }
}

export default function WarRoom({ theme }: WarRoomProps) {
  const dark = theme !== "light";
  const persisted = loadPersistedState();
  const [scanMode, setScanMode] = useState<ScanMode>(
    persisted?.scanMode ?? { kind: "idle" },
  );
  const [fixesApplied, setFixesApplied] = useState(persisted?.fixesApplied ?? false);
  const [selectedRiskId, setSelectedRiskId] = useState<string | null>(
    persisted?.selectedRiskId ?? null,
  );
  const [reportOpen, setReportOpen] = useState(false);
  const [rawOpen, setRawOpen] = useState(false);
  const [repoInput, setRepoInput] = useState(persisted?.repoInput ?? "");
  // User-driven status overrides per finding id. Backend always emits "open";
  // visitors can mark items Needs Review / Resolved Manually / Accepted Risk.
  const [statusOverrides, setStatusOverrides] = useState<Record<string, RiskStatus>>(
    persisted?.statusOverrides ?? {},
  );

  // Persist War Room state across page refreshes so the last scan, fix-applied
  // status, selected risk, and triage overrides survive a reload. Transient
  // states ("scanning", "error") are filtered out on load.
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(
        WAR_ROOM_STORAGE_KEY,
        JSON.stringify({
          scanMode,
          fixesApplied,
          selectedRiskId,
          statusOverrides,
          repoInput,
        }),
      );
    } catch {
      // ignore storage errors (quota, private mode, etc.)
    }
  }, [scanMode, fixesApplied, selectedRiskId, statusOverrides, repoInput]);

  function setRiskStatus(id: string, s: RiskStatus) {
    setStatusOverrides(prev => ({ ...prev, [id]: s }));
  }
  function effectiveStatus(r: Risk): RiskStatus {
    return statusOverrides[r.id] ?? coerceRiskStatus(r.status);
  }

  const hasScan = scanMode.kind === "real" || scanMode.kind === "sample";
  const isReal  = scanMode.kind === "real";
  const isSample = scanMode.kind === "sample";

  // ── Source of truth: real scan, sample, or empty ────────────────────────
  const realScan = scanMode.kind === "real" ? scanMode.data : null;

  const risks: Risk[] =
    isReal && realScan ? realScan.findings :
    isSample           ? SEEDED_RISKS :
                         [];

  const baseGates: SafetyGate[] =
    isReal && realScan ? realScan.gates :
    isSample           ? GATES_BEFORE :
                         [];

  // After fixes: real scans flip every gate to pass; sample uses GATES_AFTER.
  const gates: SafetyGate[] =
    !hasScan       ? [] :
    !fixesApplied  ? baseGates :
    isReal         ? baseGates.map(g => ({ ...g, state: "pass" as const, detail: "Resolved post-fix" })) :
                     GATES_AFTER;

  const scoreBefore =
    isReal && realScan ? realScan.score :
    isSample           ? SCORE_BEFORE :
                         0;

  const scoreAfter =
    isReal && realScan ? realScan.scoreProjected :
    isSample           ? SCORE_AFTER :
                         0;

  const scoreCurrent = !hasScan ? 100 : (fixesApplied ? scoreAfter : scoreBefore);
  const scoreDelta = Math.max(0, scoreAfter - scoreBefore);

  const projectName =
    isReal && realScan ? realScan.repo.fullName :
    isSample           ? PROJECT_NAME :
                         "—";

  const repoUrl = isReal && realScan ? realScan.repo.url : null;
  const filesScanned = isReal && realScan ? realScan.filesScanned : [];

  const realStatus =
    isReal && realScan ? realScan.status :
    isSample           ? (fixesApplied ? "SAFE_TO_SHIP" : "SHIP_BLOCKED") :
                         "SAFE_TO_SHIP";

  const statusLabel =
    !hasScan                                  ? "—" :
    fixesApplied                              ? "READY TO SHIP" :
    realStatus === "SAFE_TO_SHIP"             ? "SAFE TO SHIP" :
    realStatus === "NEEDS_REVIEW"             ? "NEEDS REVIEW" :
                                                "SHIP BLOCKED";

  const statusColor =
    !hasScan                                  ? "#FCA5A5" :
    fixesApplied || realStatus === "SAFE_TO_SHIP" ? "#6EE7B7" :
    realStatus === "NEEDS_REVIEW"             ? "#FCD34D" :
                                                "#FCA5A5";

  const criticalCount = risks.filter(r => r.severity === "critical").length;
  const highCount     = risks.filter(r => r.severity === "high").length;
  const mediumCount   = risks.filter(r => r.severity === "medium").length;
  const lowCount      = risks.filter(r => r.severity === "low").length;

  const safeToShip = hasScan && (fixesApplied || realStatus === "SAFE_TO_SHIP");
  const topBlocker = risks.find(r => r.severity === "critical")
                  ?? risks.find(r => r.severity === "high")
                  ?? risks[0];

  // ── Scan handlers ───────────────────────────────────────────────────────
  async function handleRealScan(input: string) {
    const trimmed = input.trim();
    if (!trimmed) return;
    setScanMode({ kind: "scanning", repo: trimmed });
    setFixesApplied(false);
    setSelectedRiskId(null);

    // Defensive watchdog: if the fetch never resolves (proxy hang, sleep,
    // dropped connection) the UI must not be stuck in "scanning" forever.
    // After 25s we abort the request, which forces the catch block to flip
    // scanMode to "error" so the Scan Public Repo button re-enables.
    const ac = new AbortController();
    const watchdog = window.setTimeout(() => ac.abort(), 25000);

    try {
      const r = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo: trimmed }),
        signal: ac.signal,
      });

      // Parse JSON defensively — server may return HTML on a proxy hiccup.
      let body: any = null;
      try { body = await r.json(); } catch { body = null; }

      // FastAPI rate-limit / generic HTTPException shape is {detail: ...}.
      // Map it to our deterministic error shape so the UI can render a
      // friendly message instead of going blank.
      if (!r.ok) {
        if (r.status === 429) {
          const detail = body && typeof body === "object" ? body.detail : null;
          const msg = (detail && typeof detail === "object" && typeof detail.message === "string")
            ? detail.message
            : "Too many scans from this network. Wait a moment and try again, or use the sample scan.";
          setScanMode({ kind: "error", error: "RATE_LIMIT", message: msg });
          return;
        }
        setScanMode({
          kind: "error",
          error: "SERVER_ERROR",
          message: `Scanner returned HTTP ${r.status}. Try again or use the sample scan.`,
        });
        return;
      }

      // Validate payload shape before trusting it.
      if (!body || typeof body !== "object" || typeof body.ok !== "boolean") {
        setScanMode({
          kind: "error",
          error: "BAD_RESPONSE",
          message: "Scanner returned an unexpected response. Try again or use the sample scan.",
        });
        return;
      }

      if (body.ok) {
        // Minimal shape validation for the success branch.
        const looksValid =
          body.repo && typeof body.repo === "object" &&
          Array.isArray(body.findings) &&
          Array.isArray(body.gates) &&
          typeof body.score === "number";
        if (!looksValid) {
          setScanMode({
            kind: "error",
            error: "BAD_RESPONSE",
            message: "Scanner returned an incomplete report. Try again or use the sample scan.",
          });
          return;
        }
        setScanMode({ kind: "real", data: body as ScanResponse & { ok: true } });
      } else {
        setScanMode({
          kind: "error",
          error: typeof body.error === "string" ? body.error : "SCAN_FAILED",
          message: typeof body.message === "string" ? body.message : "The scan could not be completed.",
        });
      }
    } catch (e: any) {
      const aborted = e?.name === "AbortError";
      setScanMode({
        kind: "error",
        error: aborted ? "TIMEOUT" : "NETWORK_ERROR",
        message: aborted
          ? "Scan took longer than 25s and was cancelled. Try again or use the sample scan."
          : "Could not reach the scanner. Check your network or try the sample scan.",
      });
    } finally {
      window.clearTimeout(watchdog);
    }
  }

  function handleSampleScan() {
    setScanMode({ kind: "sample" });
    setFixesApplied(false);
    setSelectedRiskId(null);
  }

  function handleResetAll() {
    setScanMode({ kind: "idle" });
    setFixesApplied(false);
    setSelectedRiskId(null);
    setRepoInput("");
    setStatusOverrides({});
    setReportOpen(false);
    setRawOpen(false);
    if (typeof window !== "undefined") {
      try {
        window.localStorage.removeItem(WAR_ROOM_STORAGE_KEY);
      } catch {
        // ignore
      }
    }
  }

  // Deep-link support: ?repo=owner/repo (or full URL) auto-runs a real scan
  // on mount. Lets judges/users share a stable "scan this repo" URL.
  // Module-level guard prevents StrictMode dev double-mount from firing twice.
  useEffect(() => {
    if (typeof window === "undefined") return;
    if ((window as any).__warroomDeepLinkFired) return;
    (window as any).__warroomDeepLinkFired = true;
    try {
      const params = new URLSearchParams(window.location.search);
      const r = params.get("repo");
      if (r && r.trim()) {
        setRepoInput(r.trim());
        setTimeout(() => { void handleRealScan(r.trim()); }, 0);
      } else if (params.get("sample") === "1") {
        handleSampleScan();
      }
    } catch { /* ignore malformed URLs */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cardBg     = dark ? "rgba(17,17,17,0.74)" : "rgba(255,255,255,0.92)";
  const cardBorder = dark ? "1px solid rgba(196,154,71,0.18)" : "1px solid rgba(28,44,69,0.10)";
  const subText    = dark ? "rgba(255,255,255,0.58)" : "rgba(28,44,69,0.58)";
  const text       = dark ? "#FFFFFF" : "#1C2C45";
  const subtle     = dark ? "rgba(255,255,255,0.42)" : "rgba(28,44,69,0.42)";
  const divider    = dark ? "rgba(255,255,255,0.07)" : "rgba(28,44,69,0.07)";

  const lastScan = hasScan ? "Just now" : "—";

  const selectedRisk = selectedRiskId ? risks.find(r => r.id === selectedRiskId) : null;

  const Card: React.FC<{ children: React.ReactNode; padding?: string; style?: React.CSSProperties }> = ({ children, padding = "16px 18px", style }) => (
    <div className="relative overflow-hidden wr-card-body" style={{
      background: cardBg, border: cardBorder, borderRadius: 16, padding,
      // minWidth: 0 prevents this card from being forced wider than its
      // parent grid track by long inline content (file paths, URLs, etc.).
      minWidth: 0,
      backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)",
      boxShadow: dark ? "0 4px 20px rgba(0,0,0,0.30)" : "0 4px 20px rgba(28,44,69,0.06)",
      ...style,
    }}>{children}</div>
  );

  const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div style={{ fontSize: 11, color: "#C49A47", fontWeight: 800, letterSpacing: "0.10em",
      textTransform: "uppercase", marginBottom: 10 }}>{children}</div>
  );

  return (
    <div style={{ animation: "wrFadeIn 360ms ease both" }}>
      <style>{`
        @keyframes wrFadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes wrPopIn {
          from { opacity: 0; transform: scale(0.95); }
          to   { opacity: 1; transform: scale(1); }
        }
        @keyframes wrScoreCount {
          from { opacity: 0.3; transform: scale(0.92); }
          to   { opacity: 1;   transform: scale(1); }
        }
        /* minmax(0, 1fr) lets grid items SHRINK below their intrinsic
           min content width; without it, long text inside a tile forces
           the column wider than the viewport on mobile. */
        .wr-grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
        .wr-grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
        @media (max-width: 700px) {
          .wr-grid-3 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .wr-grid-2 { grid-template-columns: minmax(0, 1fr); }
        }
        /* Phones: collapse the dashboard tiles to a single column so the
           long "Top Blocker" / "Risk Mix" copy can wrap instead of overflowing. */
        @media (max-width: 460px) {
          .wr-grid-3 { grid-template-columns: minmax(0, 1fr); }
        }
        .wr-cta {
          background: linear-gradient(135deg, #C49A47 0%, #a87d2e 100%);
          color: #111; border: none; border-radius: 12px;
          padding: 11px 22px; font-weight: 800; font-size: 14px;
          cursor: pointer; font-family: inherit; letter-spacing: 0.01em;
          box-shadow: 0 4px 18px rgba(196,154,71,0.32);
          transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
        }
        .wr-cta:hover { transform: scale(1.02); box-shadow: 0 6px 22px rgba(196,154,71,0.45); filter: brightness(1.06); }
        .wr-cta:active { transform: scale(0.98); }
        .wr-cta:disabled { opacity: 0.4; cursor: not-allowed; transform: none; filter: none; }
        .wr-ghost-btn {
          background: ${dark ? "rgba(255,255,255,0.06)" : "rgba(28,44,69,0.06)"};
          border: 1px solid ${dark ? "rgba(255,255,255,0.10)" : "rgba(28,44,69,0.10)"};
          color: ${text}; border-radius: 10px;
          padding: 10px 16px; font-weight: 600; font-size: 13px;
          cursor: pointer; font-family: inherit;
          transition: background 120ms ease;
        }
        .wr-ghost-btn:hover { background: ${dark ? "rgba(255,255,255,0.10)" : "rgba(28,44,69,0.10)"}; }
        .wr-risk-card {
          cursor: pointer;
          transition: transform 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
        }
        .wr-risk-card:hover { transform: translateY(-2px); }

        /* Mobile sizing — tighten paddings, scale headline, allow long
           file paths / inline code to break instead of forcing overflow. */
        .wr-hero { padding: 26px 24px 24px; }
        .wr-hero-headline { font-size: 26px; }
        @media (max-width: 600px) {
          .wr-hero { padding: 18px 16px 16px; }
          .wr-hero-headline { font-size: 22px; }
        }
        @media (max-width: 400px) {
          .wr-hero { padding: 16px 14px 14px; }
          .wr-hero-headline { font-size: 20px; }
        }
        /* Force any inline code / long path / URL to wrap on phones. */
        @media (max-width: 600px) {
          .wr-card-body code,
          .wr-card-body a {
            word-break: break-all;
            overflow-wrap: anywhere;
          }
        }
      `}</style>

      {/* ── Hero header ──────────────────────────────────────────────────── */}
      <div className="wr-hero" style={{
        marginBottom: 14, borderRadius: 18,
        background: dark
          ? "linear-gradient(135deg, rgba(196,154,71,0.12) 0%, rgba(28,44,69,0.55) 100%)"
          : "linear-gradient(135deg, rgba(196,154,71,0.18) 0%, rgba(255,255,255,0.85) 100%)",
        border: "1px solid rgba(196,154,71,0.32)",
        boxShadow: dark ? "0 6px 28px rgba(0,0,0,0.30)" : "0 6px 28px rgba(28,44,69,0.06)",
      }}>
        <div style={{
          fontSize: 11, color: "#C49A47", fontWeight: 800, letterSpacing: "0.14em",
          textTransform: "uppercase", marginBottom: 8,
        }}>
          RepoGuard War Room
        </div>
        <div className="wr-hero-headline" style={{
          fontWeight: 800, color: text, lineHeight: 1.15,
          letterSpacing: "-0.01em", marginBottom: 8,
        }}>
          Agent-Built Safety Layer for AI Apps
        </div>
        <div style={{ fontSize: 15, color: subText, lineHeight: 1.55, maxWidth: 660 }}>
          Scan your project before you ship. Paste any public GitHub repo, and RepoGuard
          runs deterministic checks for secrets, env vars, workflows, deploy config, and
          unsafe patterns — no login, no GitHub token, no AI in the loop.
        </div>
      </div>

      {/* ── 0. Repo Input ───────────────────────────────────────────────── */}
      <Card padding="22px 22px 20px" style={{ marginBottom: 14 }}>
        <SectionLabel>Scan a Public GitHub Repo</SectionLabel>
        <div style={{ color: subText, fontSize: 13.5, lineHeight: 1.55, marginBottom: 12,
          maxWidth: 640 }}>
          Enter a public repository as <code style={{ fontFamily: "monospace", color: text }}>owner/repo</code>{" "}
          or a full GitHub URL. No login. No GitHub token. RepoGuard reads the repo's public files
          and runs deterministic checks for secrets, env vars, workflows, deploy config, and unsafe patterns.
        </div>
        <form onSubmit={(e) => { e.preventDefault(); handleRealScan(repoInput); }}
          style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input
            type="text"
            value={repoInput}
            onChange={(e) => setRepoInput(e.target.value)}
            placeholder="vercel/next.js  or  https://github.com/owner/repo"
            disabled={scanMode.kind === "scanning"}
            style={{
              flex: "1 1 280px", minWidth: 200,
              padding: "11px 14px", borderRadius: 12,
              background: dark ? "rgba(255,255,255,0.05)" : "rgba(28,44,69,0.04)",
              border: `1px solid ${dark ? "rgba(255,255,255,0.12)" : "rgba(28,44,69,0.14)"}`,
              color: text, fontFamily: "inherit", fontSize: 14, outline: "none",
            }}
          />
          <button type="submit" className="wr-cta"
            disabled={scanMode.kind === "scanning" || !repoInput.trim()}>
            {scanMode.kind === "scanning" ? "Scanning…" : "Scan Public Repo"}
          </button>
          <button type="button" className="wr-ghost-btn" onClick={handleSampleScan}
            disabled={scanMode.kind === "scanning"}
            title="Load deterministic seeded findings — no GitHub call">
            Try Sample Scan
          </button>
          {hasScan && (
            <button type="button" className="wr-ghost-btn" onClick={handleResetAll}
              >
              ↻ Reset
            </button>
          )}
        </form>

        {scanMode.kind === "scanning" && (
          <div style={{ marginTop: 12, padding: "10px 14px", borderRadius: 10,
            background: "rgba(196,154,71,0.10)", border: "1px solid rgba(196,154,71,0.30)",
            color: text, fontSize: 13 }}>
            <span style={{ color: "#C49A47", fontWeight: 800 }}>● </span>
            Fetching <span style={{ fontFamily: "monospace" }}>{scanMode.repo}</span> from GitHub
            and running 12 deterministic checks…
          </div>
        )}

        {scanMode.kind === "error" && (
          <div style={{ marginTop: 12, padding: "12px 14px", borderRadius: 10,
            background: "rgba(252,165,165,0.10)", border: "1px solid rgba(252,165,165,0.40)",
            color: text, fontSize: 13.5 }}>
            <div style={{ fontWeight: 800, color: "#FCA5A5", marginBottom: 4 }}>
              Scan failed · {scanMode.error}
            </div>
            <div style={{ color: subText, marginBottom: 10 }}>{scanMode.message}</div>
            <button className="wr-ghost-btn" onClick={handleSampleScan}>
              Use sample scan instead →
            </button>
          </div>
        )}

        {isSample && (
          <div style={{ marginTop: 12, padding: "10px 14px", borderRadius: 10,
            background: "rgba(252,211,77,0.08)", border: "1px solid rgba(252,211,77,0.40)",
            fontSize: 13 }}>
            <div style={{ color: "#FCD34D", fontWeight: 800, marginBottom: 3 }}>
              SAMPLE SCAN — example data only
            </div>
            <div style={{ color: subText, fontSize: 12.5, lineHeight: 1.5 }}>
              This is seeded example data and not a live repo scan. Enter a public GitHub repo above to run a real scan against actual repository contents.
            </div>
          </div>
        )}

        {isReal && realScan && (
          <div style={{ marginTop: 12, padding: "12px 14px", borderRadius: 10,
            background: "rgba(110,231,183,0.08)", border: "1px solid rgba(110,231,183,0.40)",
            fontSize: 12.5, lineHeight: 1.6 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6, flexWrap: "wrap" }}>
              <span style={{ color: "#6EE7B7", fontWeight: 800, fontSize: 11,
                letterSpacing: "0.10em", textTransform: "uppercase" }}>● LIVE SCAN</span>
              <a href={realScan.repo.url ?? "#"} target="_blank" rel="noopener noreferrer"
                style={{ color: "#C49A47", fontFamily: "monospace", textDecoration: "none", fontSize: 13 }}>
                {realScan.repo.fullName}
              </a>
              {realScan.repo.language && (
                <span style={{ color: subText }}>· {realScan.repo.language}</span>
              )}
            </div>
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap", color: subText, fontSize: 12 }}>
              <span>Branch: <code style={{ color: text, fontFamily: "monospace" }}>{realScan.repo.defaultBranch}</code></span>
              <span>Files scanned: <b style={{ color: text }}>{filesScanned.length}</b></span>
              <span>Rules: <b style={{ color: text }}>{realScan.rulesExecuted ?? 12}</b></span>
              <span>Scanned: <b style={{ color: text }}>{new Date(realScan.scanTime).toLocaleTimeString()}</b></span>
              {(realScan.filesUnavailable ?? 0) > 0 && (
                <span style={{ color: "#FCD34D" }}>{realScan.filesUnavailable} not found / skipped</span>
              )}
            </div>
            {filesScanned.length > 0 && (
              <div style={{ marginTop: 6, color: subtle, fontFamily: "monospace", fontSize: 11,
                wordBreak: "break-all", overflowWrap: "anywhere" }}>
                {filesScanned.slice(0, 6).join("  ·  ")}{filesScanned.length > 6 ? `  +${filesScanned.length - 6} more` : ""}
              </div>
            )}
          </div>
        )}
      </Card>

      {/* ── Raw Scan Data toggle (live scans only) ──────────────────────── */}
      {isReal && realScan && (
        <div style={{ marginBottom: 14 }}>
          <button className="wr-ghost-btn" onClick={() => setRawOpen(v => !v)}
            style={{ width: "100%", textAlign: "left", fontSize: 12.5 }}>
            {rawOpen ? "▲ Hide Raw Scan Data" : "▼ View Raw Scan Data"}
            <span style={{ marginLeft: 8, color: subText, fontWeight: 400 }}>
              — sanitized JSON for judge verification
            </span>
          </button>
          {rawOpen && (
            <div style={{ marginTop: 6, padding: "14px 16px", borderRadius: 12,
              background: dark ? "rgba(0,0,0,0.40)" : "rgba(28,44,69,0.05)",
              border: cardBorder, maxHeight: 420, overflowY: "auto" }}>
              <pre style={{ margin: 0, fontSize: 11, color: text, fontFamily: "monospace",
                whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
                {JSON.stringify({
                  scanMode: "live",
                  repo: realScan.repo,
                  scanTime: realScan.scanTime,
                  score: realScan.score,
                  scoreProjected: realScan.scoreProjected,
                  status: realScan.status,
                  rulesExecuted: realScan.rulesExecuted,
                  filesScanned: realScan.filesScanned,
                  filesUnavailable: realScan.filesUnavailable,
                  findings: realScan.findings.map(f => ({
                    id: f.id, category: f.category, severity: f.severity, file: f.file,
                    shortExplanation: f.shortExplanation,
                    ruleId: f.ruleId, evidenceType: f.evidenceType,
                    evidenceFile: f.evidenceFile, evidenceSnippet: f.evidenceSnippet,
                    evidenceLine: f.evidenceLine, confidence: f.confidence, source: f.source,
                  })),
                  gates: realScan.gates,
                }, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* ── 1. Command Dashboard ─────────────────────────────────────────── */}
      <Card padding="22px 22px 20px" style={{ marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
          gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
          <div>
            <SectionLabel>War Room Command</SectionLabel>
            <div style={{ fontSize: "clamp(20px, 3.5vw, 26px)", fontWeight: 800, color: text,
              lineHeight: 1.15 }}>
              Safety command layer for {projectName}
            </div>
            <div style={{ color: subText, marginTop: 6, fontSize: 13.5, lineHeight: 1.55, maxWidth: 560 }}>
              One view of every risk an AI-built app must clear before it ships.
            </div>
          </div>
          {fixesApplied && (
            <div style={{ display: "flex", gap: 8, flexShrink: 0, flexWrap: "wrap" }}>
              <button
                className="wr-ghost-btn"
                onClick={() => { setFixesApplied(false); setSelectedRiskId(null); }}
                title="Revert fixes to show the unsafe state again"
              >
                ↻ Reset Fixes
              </button>
            </div>
          )}
        </div>

        <div className="wr-grid-3">
          <Tile label="Repo Integrity" value={hasScan ? `${scoreCurrent}%` : "—"}
            accent="#C49A47" theme={theme} />
          <Tile label="Safe-to-Ship" value={statusLabel}
            accent={statusColor} theme={theme} />
          <Tile label="Critical Risks" value={!hasScan ? "—" : String(criticalCount)}
            accent={criticalCount > 0 ? "#FCA5A5" : "#6EE7B7"} theme={theme} />
          <Tile label="Risk Mix" value={!hasScan ? "—" :
              `${highCount} high · ${mediumCount} med · ${lowCount} low`}
            accent={text} theme={theme} small />
          <Tile label="Last Scan" value={lastScan} accent={text} theme={theme} small />
          <Tile label="Top Blocker"
            value={!hasScan ? "—" : (topBlocker?.shortExplanation ?? "None")}
            accent={topBlocker?.severity ? SEVERITY_COLOR[topBlocker.severity] : "#6EE7B7"}
            theme={theme} small />
        </div>
      </Card>

      {/* ── 2. Before / After Integrity ─────────────────────────────────── */}
      <Card padding="22px 22px 24px" style={{ marginBottom: 14 }}>
        <SectionLabel>Integrity Score · Before vs After Fix Plan</SectionLabel>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 24,
          flexWrap: "wrap", padding: "10px 0 6px" }}>
          <ScoreBlock label="Current" value={hasScan ? scoreBefore : 0}
            color={scoreBefore >= 85 ? "#6EE7B7" : scoreBefore >= 60 ? "#FCD34D" : "#FCA5A5"}
            theme={theme} />
          <div style={{ fontSize: 28, color: subtle, fontWeight: 700 }}>→</div>
          <ScoreBlock label="After Fix Plan" value={hasScan ? scoreAfter : 0} color="#6EE7B7" theme={theme} />
          <div style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
            padding: "10px 16px", borderRadius: 12,
            background: "rgba(196,154,71,0.10)", border: "1px solid rgba(196,154,71,0.30)",
          }}>
            <div style={{ fontSize: 10, color: "#C49A47", fontWeight: 700, letterSpacing: "0.08em" }}>
              SCORE Δ
            </div>
            <div style={{ fontSize: 26, fontWeight: 800, color: "#C49A47" }}>
              {hasScan ? `+${scoreDelta}` : "—"}
            </div>
          </div>
        </div>
      </Card>

      {/* ── 3. Risk Detection Panel ─────────────────────────────────────── */}
      <Card padding="20px 20px 22px" style={{ marginBottom: 14 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
          marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
          <SectionLabel>Risk Detection</SectionLabel>
          <span style={{ fontSize: 11, color: subText, fontWeight: 600 }}>
            {risks.length} {risks.length === 1 ? "risk" : "risks"} detected
          </span>
        </div>

        {!hasScan ? (
          <EmptyState
            theme={theme}
            title="No scan loaded"
            body="Enter a public GitHub repo above and click Scan Public Repo, or use Try Sample Scan to load deterministic seeded findings."
          />
        ) : risks.length === 0 ? (
          <EmptyState
            theme={theme}
            title="Scanner found no findings"
            body="No risks were detected for this repo against the current ruleset. Integrity 100%."
          />
        ) : (
          <div className="wr-grid-2">
            {risks.map(r => (
              <RiskCardView
                key={r.id}
                risk={r}
                fixed={fixesApplied}
                selected={selectedRiskId === r.id}
                onClick={() => setSelectedRiskId(id => id === r.id ? null : r.id)}
                statusOverride={statusOverrides[r.id]}
                theme={theme}
              />
            ))}
          </div>
        )}

        {/* 4 + 6: What broke / Why / How to fix + Fix Plan */}
        {selectedRisk && (
          <div style={{
            marginTop: 14, padding: "16px 18px", borderRadius: 14,
            background: dark ? "rgba(196,154,71,0.06)" : "rgba(196,154,71,0.10)",
            border: "1px solid rgba(196,154,71,0.30)",
            animation: "wrPopIn 240ms ease both",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start",
              marginBottom: 10, gap: 8, flexWrap: "wrap" }}>
              <div style={{ fontSize: 14, fontWeight: 800, color: "#C49A47", letterSpacing: "0.04em",
                minWidth: 0, flex: "1 1 200px", wordBreak: "break-word", overflowWrap: "anywhere" }}>
                {selectedRisk.category} · {selectedRisk.file}
              </div>
              <button className="wr-ghost-btn" onClick={() => setSelectedRiskId(null)}
                style={{ padding: "5px 10px", fontSize: 12, flexShrink: 0 }}>✕ Close</button>
            </div>

            <DetailRow label="What broke"     body={selectedRisk.whatBroke}  theme={theme} />
            <DetailRow label="Why it matters" body={selectedRisk.whyMatters} theme={theme} />
            <DetailRow label="How to fix"     body={selectedRisk.howToFix}   theme={theme} />

            {(selectedRisk.ruleId != null || selectedRisk.evidenceSnippet != null) && (
              <div style={{ marginTop: 12, paddingTop: 12, borderTop: `1px solid ${divider}` }}>
                <div style={{ fontSize: 11, color: "#C49A47", fontWeight: 800,
                  letterSpacing: "0.10em", textTransform: "uppercase", marginBottom: 8 }}>
                  Evidence
                </div>
                <div style={{ display: "grid", gap: 5 }}>
                  {selectedRisk.ruleId && <EvidenceRow label="Rule ID" value={selectedRisk.ruleId} theme={theme} />}
                  {selectedRisk.source && <EvidenceRow label="Source" value={selectedRisk.source} theme={theme} />}
                  {selectedRisk.evidenceFile && <EvidenceRow label="File" value={selectedRisk.evidenceFile} theme={theme} />}
                  {selectedRisk.evidenceLine != null && <EvidenceRow label="Line" value={String(selectedRisk.evidenceLine)} theme={theme} />}
                  {selectedRisk.evidenceSnippet && <EvidenceRow label="Snippet" value={selectedRisk.evidenceSnippet} theme={theme} />}
                  {selectedRisk.confidence && <EvidenceRow label="Confidence" value={selectedRisk.confidence} theme={theme} />}
                </div>
              </div>
            )}

            {/* Status selector — visitors can mark their own triage decisions. */}
            <div style={{
              marginTop: 12, paddingTop: 12,
              borderTop: `1px solid ${divider}`,
              display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap",
            }}>
              <span style={{
                fontSize: 11, color: "#C49A47", fontWeight: 800, letterSpacing: "0.10em",
                textTransform: "uppercase",
              }}>
                Mark status
              </span>
              {(["open", "needs_review", "resolved_manually", "accepted_risk"] as RiskStatus[]).map(s => {
                const active = effectiveStatus(selectedRisk) === s;
                const c = RISK_STATUS_COLOR[s];
                return (
                  <button
                    key={s}
                    onClick={() => setRiskStatus(selectedRisk.id, s)}
                    style={{
                      padding: "6px 12px", borderRadius: 999, fontSize: 12, fontWeight: 700,
                      cursor: "pointer", fontFamily: "inherit",
                      background: active ? `${c}26` : (dark ? "rgba(255,255,255,0.04)" : "rgba(28,44,69,0.04)"),
                      border: active ? `1px solid ${c}88` : `1px solid ${dark ? "rgba(255,255,255,0.10)" : "rgba(28,44,69,0.10)"}`,
                      color: active ? c : (dark ? "rgba(255,255,255,0.65)" : "rgba(28,44,69,0.65)"),
                    }}
                  >
                    {RISK_STATUS_LABEL[s]}
                  </button>
                );
              })}
            </div>

            <div style={{ marginTop: 14, paddingTop: 14, borderTop: `1px solid ${divider}` }}>
              {!fixesApplied ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 8 }}>
                  <button className="wr-cta" onClick={() => setFixesApplied(true)}>
                    ✦ Generate Fix Plan
                  </button>
                  <div style={{ fontSize: 12, color: subText, lineHeight: 1.5 }}>
                    Generates the deterministic fix plan for this risk and updates the
                    Safe-to-Ship Checklist + Integrity Score.
                  </div>
                </div>
              ) : (
                <div style={{ animation: "wrPopIn 240ms ease both" }}>
                  <div style={{
                    display: "flex", alignItems: "center", gap: 8, marginBottom: 10,
                    fontSize: 11, color: "#C49A47", fontWeight: 800, letterSpacing: "0.10em",
                    textTransform: "uppercase",
                  }}>
                    <span style={{
                      display: "inline-flex", alignItems: "center", justifyContent: "center",
                      width: 18, height: 18, borderRadius: "50%",
                      background: "rgba(110,231,183,0.20)", border: "1px solid rgba(110,231,183,0.55)",
                      color: "#6EE7B7", fontSize: 11, fontWeight: 800,
                    }}>✓</span>
                    Deterministic Fix Plan · Applied
                  </div>
                  <ol style={{ margin: 0, paddingLeft: 20, color: text, fontSize: 13.5, lineHeight: 1.7 }}>
                    {selectedRisk.fixPlan.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </div>
        )}
      </Card>

      {/* ── 5. Safe-to-Ship Checklist ───────────────────────────────────── */}
      <Card padding="20px 20px 22px" style={{ marginBottom: 14 }}>
        <SectionLabel>Safe-to-Ship Checklist</SectionLabel>

        {!hasScan ? (
          <EmptyState theme={theme} title="No checklist evaluated"
            body="Run a real or sample scan to evaluate the safety gates." />
        ) : (
          <div style={{ display: "grid", gap: 8 }}>
            {gates.map(g => <GateRow key={g.id} gate={g} theme={theme} />)}
          </div>
        )}
      </Card>

      {/* ── 9. Agent Build Trace ────────────────────────────────────────── */}
      <Card padding="20px 20px 22px" style={{ marginBottom: 14 }}>
        <SectionLabel>Agent Build Trace</SectionLabel>
        <div style={{ display: "grid", gap: 0 }}>
          {AGENT_BUILD_TRACE.map((step, i) => {
            // Pre-fix: agent has scanned + classified + planned + validated checklist (steps 1-5).
            // Post-fix: agent has also generated the final report (step 6).
            // Pre-scan: nothing reached.
            const milestoneIndex = !hasScan ? -1 : (fixesApplied ? 5 : 4);
            const reached = i <= milestoneIndex;
            return (
              <TraceStepRow key={i} step={step} reached={reached} isLast={i === AGENT_BUILD_TRACE.length - 1}
                theme={theme} />
            );
          })}
        </div>
      </Card>

      {/* ── 10. Progress Evidence ───────────────────────────────────────── */}
      <Card padding="20px 20px 22px" style={{ marginBottom: 14 }}>
        <SectionLabel>Buildathon Progress</SectionLabel>
        <div style={{ display: "grid", gap: 8, fontSize: 13.5, color: text, lineHeight: 1.6 }}>
          <EvidenceRow label="Built during" value="Replit 10-Year Buildathon" theme={theme} />
          <EvidenceRow label="Before" value="Basic repo / security scanner — binary findings, no fix plans" theme={theme} />
          <EvidenceRow label="After"  value="Public War Room safety command layer with real GitHub scan + deterministic fix plans" theme={theme} />
          <EvidenceRow label="Workflow" value="Iterative Replit Agent build · prompt → scan → fix → ship" theme={theme} />
          <EvidenceRow label="Public usable" value="Anyone can scan a public repo + open a Safe-to-Ship report — no login, no token" theme={theme} />
        </div>
      </Card>

      {/* ── 7. Generate Report ──────────────────────────────────────────── */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>
        <button className="wr-cta" onClick={() => setReportOpen(true)} disabled={!hasScan}>
          Open Safe-to-Ship Report
        </button>
      </div>

      {reportOpen && (
        <SafeToShipReport
          onClose={() => setReportOpen(false)}
          theme={theme}
          projectName={projectName}
          repoUrl={repoUrl ?? null}
          scanTimeISO={isReal && realScan ? realScan.scanTime : new Date().toISOString()}
          filesScanned={filesScanned}
          risks={risks}
          gates={gates}
          scoreBefore={scoreBefore}
          scoreAfter={fixesApplied ? scoreAfter : scoreCurrent}
          fixesApplied={fixesApplied}
          statusLabel={statusLabel}
          statusColor={statusColor}
          isSample={isSample}
          rulesExecuted={isReal && realScan ? realScan.rulesExecuted : undefined}
        />
      )}
    </div>
  );
}

// ─── Sub-components ────────────────────────────────────────────────────────────

function Tile({ label, value, accent, theme, small }: {
  label: string; value: string; accent: string; theme: string; small?: boolean;
}) {
  const dark = theme !== "light";
  return (
    <div style={{
      padding: "12px 14px", borderRadius: 12,
      // minWidth: 0 lets this tile shrink inside a CSS grid track without
      // being forced wider by its own content (the "Top Blocker" copy).
      minWidth: 0,
      background: dark ? "rgba(255,255,255,0.04)" : "rgba(28,44,69,0.05)",
      border: dark ? "1px solid rgba(255,255,255,0.07)" : "1px solid rgba(28,44,69,0.08)",
    }}>
      <div style={{ fontSize: 10, color: dark ? "rgba(255,255,255,0.45)" : "rgba(28,44,69,0.50)",
        fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>
        {label}
      </div>
      <div style={{
        fontSize: small ? 13 : 18, fontWeight: 800, color: accent,
        lineHeight: 1.25, overflow: "hidden", textOverflow: "ellipsis",
        // Allow wrapping even on "small" tiles so phrases like
        // "3 high · 0 med · 0 low" don't punch out of the tile.
        wordBreak: "break-word", overflowWrap: "anywhere",
      }}>
        {value}
      </div>
    </div>
  );
}

function ScoreBlock({ label, value, color, theme }: {
  label: string; value: number; color: string; theme: string;
}) {
  const dark = theme !== "light";
  return (
    <div style={{ textAlign: "center", animation: "wrScoreCount 360ms ease both" }}>
      <div style={{ fontSize: 10, color: dark ? "rgba(255,255,255,0.45)" : "rgba(28,44,69,0.50)",
        fontWeight: 700, letterSpacing: "0.10em", textTransform: "uppercase", marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 48, fontWeight: 800, color, letterSpacing: "-0.02em",
        textShadow: `0 0 20px ${color}33` }}>
        {value}<span style={{ fontSize: 22 }}>%</span>
      </div>
    </div>
  );
}

function RiskCardView({ risk, fixed, selected, onClick, statusOverride, theme }: {
  risk: Risk; fixed: boolean; selected: boolean; onClick: () => void;
  statusOverride?: RiskStatus; theme: string;
}) {
  const dark = theme !== "light";
  const baseStatus: RiskStatus = statusOverride ?? coerceRiskStatus(risk.status);
  const status: RiskStatus = fixed ? "resolved_manually" : baseStatus;
  const sevColor = SEVERITY_COLOR[risk.severity];
  const statusColor = RISK_STATUS_COLOR[status];
  const statusLabel = RISK_STATUS_LABEL[status];

  return (
    <div className="wr-risk-card" onClick={onClick} style={{
      padding: "14px 16px", borderRadius: 14,
      background: dark ? "rgba(255,255,255,0.04)" : "rgba(28,44,69,0.05)",
      border: selected
        ? `1px solid ${sevColor}88`
        : dark ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(28,44,69,0.10)",
      boxShadow: selected ? `0 6px 20px ${sevColor}22` : "none",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start",
        gap: 10, marginBottom: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
          <span style={{ fontSize: 16, lineHeight: 1, flexShrink: 0 }}>
            {CATEGORY_ICON[risk.category]}
          </span>
          <span style={{ fontSize: 13, fontWeight: 800, color: dark ? "#FFFFFF" : "#1C2C45",
            overflow: "hidden", textOverflow: "ellipsis" }}>
            {risk.category}
          </span>
        </div>
        <span style={{
          padding: "3px 8px", borderRadius: 999,
          fontSize: 10, fontWeight: 800, letterSpacing: "0.06em",
          background: `${sevColor}20`, color: sevColor,
          border: `1px solid ${sevColor}55`, textTransform: "uppercase",
          flexShrink: 0,
        }}>
          {risk.severity}
        </span>
      </div>

      <div style={{ fontSize: 12, color: dark ? "rgba(255,255,255,0.55)" : "rgba(28,44,69,0.55)",
        fontFamily: "monospace", marginBottom: 6, overflow: "hidden", textOverflow: "ellipsis",
        whiteSpace: "nowrap" }}>
        {risk.file}
      </div>

      <div style={{ fontSize: 12.5, color: dark ? "rgba(255,255,255,0.78)" : "rgba(28,44,69,0.78)",
        lineHeight: 1.5, marginBottom: 10 }}>
        {risk.shortExplanation}
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          padding: "3px 8px", borderRadius: 999,
          background: `${statusColor}18`, border: `1px solid ${statusColor}44`,
          color: statusColor, fontSize: 11, fontWeight: 700,
        }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: statusColor }} />
          {statusLabel}
        </span>
        <span style={{ fontSize: 11, color: dark ? "rgba(255,255,255,0.40)" : "rgba(28,44,69,0.50)" }}>
          {selected ? "click to close" : "click for fix plan →"}
        </span>
      </div>
    </div>
  );
}

function DetailRow({ label, body, theme }: { label: string; body: string; theme: string }) {
  const dark = theme !== "light";
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontSize: 11, color: dark ? "rgba(255,255,255,0.50)" : "rgba(28,44,69,0.55)",
        fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 13.5, lineHeight: 1.6,
        color: dark ? "rgba(255,255,255,0.85)" : "rgba(28,44,69,0.85)" }}>
        {body}
      </div>
    </div>
  );
}

function GateRow({ gate, theme }: { gate: SafetyGate; theme: string }) {
  const dark = theme !== "light";
  const c = GATE_COLOR[gate.state];
  const ic = GATE_ICON[gate.state];
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 12,
      padding: "10px 14px", borderRadius: 12,
      background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
      border: `1px solid ${c}44`,
    }}>
      <span style={{
        flexShrink: 0, width: 26, height: 26, borderRadius: "50%",
        background: `${c}22`, border: `1px solid ${c}66`,
        color: c, fontWeight: 800, fontSize: 14,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>{ic}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13.5, fontWeight: 700, color: dark ? "#FFFFFF" : "#1C2C45" }}>
          {gate.label}
        </div>
        {gate.detail && (
          <div style={{ fontSize: 11, color: dark ? "rgba(255,255,255,0.50)" : "rgba(28,44,69,0.50)",
            marginTop: 2 }}>
            {gate.detail}
          </div>
        )}
      </div>
      <span style={{
        padding: "3px 9px", borderRadius: 999,
        background: `${c}18`, border: `1px solid ${c}55`,
        color: c, fontSize: 11, fontWeight: 800, letterSpacing: "0.06em",
        textTransform: "uppercase", flexShrink: 0,
      }}>
        {gate.state}
      </span>
    </div>
  );
}

function TraceStepRow({ step, reached, isLast, theme }: {
  step: { step: string; detail: string; t: string }; reached: boolean; isLast: boolean; theme: string;
}) {
  const dark = theme !== "light";
  const dotColor = reached ? "#6EE7B7" : (dark ? "rgba(255,255,255,0.20)" : "rgba(28,44,69,0.25)");
  return (
    <div style={{ display: "flex", gap: 12, paddingBottom: isLast ? 0 : 12 }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 }}>
        <div style={{
          width: 12, height: 12, borderRadius: "50%",
          background: dotColor, boxShadow: reached ? `0 0 8px ${dotColor}88` : "none",
        }} />
        {!isLast && <div style={{
          flex: 1, width: 1, marginTop: 4,
          background: dark ? "rgba(255,255,255,0.10)" : "rgba(28,44,69,0.12)",
        }} />}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
          <span style={{ fontSize: 13.5, fontWeight: 700, color: dark ? "#FFFFFF" : "#1C2C45" }}>
            {step.step}
          </span>
          <span style={{ fontSize: 11, color: dark ? "rgba(255,255,255,0.40)" : "rgba(28,44,69,0.45)",
            fontFamily: "monospace" }}>{step.t}</span>
        </div>
        <div style={{ fontSize: 12, color: dark ? "rgba(255,255,255,0.55)" : "rgba(28,44,69,0.60)",
          marginTop: 2 }}>
          {step.detail}
        </div>
      </div>
    </div>
  );
}

function EvidenceRow({ label, value, theme }: { label: string; value: string; theme: string }) {
  const dark = theme !== "light";
  return (
    <div style={{ display: "flex", gap: 12, alignItems: "baseline" }}>
      <span style={{
        flexShrink: 0, minWidth: 96, fontSize: 11, color: "#C49A47", fontWeight: 700,
        letterSpacing: "0.06em", textTransform: "uppercase",
      }}>{label}</span>
      <span style={{ color: dark ? "rgba(255,255,255,0.85)" : "rgba(28,44,69,0.85)" }}>{value}</span>
    </div>
  );
}

function EmptyState({ title, body, theme }: { title: string; body: string; theme: string }) {
  const dark = theme !== "light";
  return (
    <div style={{ padding: "20px 12px", textAlign: "center" }}>
      <div style={{ fontSize: 14, fontWeight: 700, color: dark ? "rgba(255,255,255,0.78)" : "#1C2C45",
        marginBottom: 4 }}>
        {title}
      </div>
      <div style={{ fontSize: 12.5, color: dark ? "rgba(255,255,255,0.50)" : "rgba(28,44,69,0.55)",
        lineHeight: 1.5 }}>
        {body}
      </div>
    </div>
  );
}

// ─── Safe-to-Ship Report Modal ────────────────────────────────────────────────

function SafeToShipReport({
  onClose, theme, projectName, repoUrl, scanTimeISO, filesScanned,
  risks, gates, scoreBefore, scoreAfter, fixesApplied,
  statusLabel, statusColor, isSample, rulesExecuted,
}: {
  onClose: () => void;
  theme: string;
  projectName: string;
  repoUrl: string | null;
  scanTimeISO: string;
  filesScanned: string[];
  risks: Risk[];
  gates: SafetyGate[];
  scoreBefore: number;
  scoreAfter: number;
  fixesApplied: boolean;
  statusLabel: string;
  statusColor: string;
  isSample: boolean;
  rulesExecuted?: number;
}) {
  const dark = theme !== "light";
  const cardBg = dark ? "rgba(18,24,36,0.98)" : "#FFFFFF";
  const text   = dark ? "#FFFFFF" : "#1C2C45";
  const sub    = dark ? "rgba(255,255,255,0.55)" : "rgba(28,44,69,0.60)";
  const border = dark ? "1px solid rgba(196,154,71,0.25)" : "1px solid rgba(28,44,69,0.12)";
  const divider = dark ? "rgba(255,255,255,0.07)" : "rgba(28,44,69,0.08)";

  const criticalBlockers = risks.filter(r => r.severity === "critical");
  const scanTime = new Date(scanTimeISO).toLocaleString();
  const slug = projectName.replace(/[^A-Za-z0-9._-]+/g, "_") || "scan";

  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");

  function buildSummary(): string {
    const scanMode = isSample ? "SAMPLE (seeded example data)" : "LIVE (public GitHub API)";
    const lines: string[] = [
      `RepoGuard — Safe-to-Ship Report${isSample ? " · SAMPLE DATA" : " · LIVE SCAN"}`,
      `Project:       ${projectName}${repoUrl ? `  (${repoUrl})` : ""}`,
      `Scan mode:     ${scanMode}`,
      `Scan time:     ${scanTime}`,
      `Status:        ${statusLabel}`,
      `Integrity:     ${scoreBefore}% → ${scoreAfter}%${fixesApplied ? "  [post-fix]" : ""}`,
      `Files scanned: ${filesScanned.length || "—"}`,
      rulesExecuted != null ? `Rules executed: ${rulesExecuted}` : "",
      ``,
      `Findings (${risks.length}):`,
    ].filter(l => l !== undefined);
    if (risks.length === 0) lines.push("  (none)");
    risks.forEach(r => {
      lines.push(`  [${r.severity.toUpperCase()}] ${r.category} · ${r.file}`);
      lines.push(`      ${r.shortExplanation}`);
    });
    lines.push("");
    lines.push("Checklist:");
    gates.forEach(g => {
      lines.push(`  ${g.state.toUpperCase().padEnd(8)} ${g.label}${g.detail ? `  — ${g.detail}` : ""}`);
    });
    return lines.join("\n");
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(buildSummary());
      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 2000);
    } catch {
      setCopyState("failed");
      window.setTimeout(() => setCopyState("idle"), 2000);
    }
  }

  function downloadBlob(content: string, mime: string, filename: string) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function handleDownloadJSON() {
    const payload = {
      project: projectName,
      repoUrl,
      scanTime: scanTimeISO,
      scanMode: isSample ? "sample" : "live",
      sample: isSample,
      rulesExecuted: rulesExecuted ?? null,
      score: { before: scoreBefore, after: scoreAfter, postFix: fixesApplied },
      status: statusLabel,
      filesScanned,
      findings: risks,
      checklist: gates,
    };
    downloadBlob(JSON.stringify(payload, null, 2), "application/json",
      `repoguard-${slug}.json`);
  }

  function csvEscape(s: unknown): string {
    const v = String(s ?? "");
    return /[",\n\r]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
  }

  function handleDownloadCSV() {
    const header = ["severity", "category", "file", "title", "what_broke", "why_matters", "how_to_fix"];
    const rows = risks.map(r => [
      r.severity, r.category, r.file, r.shortExplanation,
      r.whatBroke, r.whyMatters, r.howToFix,
    ].map(csvEscape).join(","));
    const csv = [header.join(","), ...rows].join("\n");
    downloadBlob(csv, "text/csv;charset=utf-8;", `repoguard-${slug}.csv`);
  }

  function buildMarkdown(): string {
    const lines: string[] = [];
    lines.push(`# RepoGuard — Safe-to-Ship Report${isSample ? " (Sample)" : ""}`);
    lines.push("");
    lines.push(`**Project:** ${projectName}`);
    if (repoUrl) lines.push(`**Repository:** <${repoUrl}>`);
    lines.push(`**Scan time:** ${scanTime}`);
    lines.push(`**Status:** ${statusLabel}`);
    lines.push(`**Integrity score:** ${scoreBefore}% → ${scoreAfter}%${fixesApplied ? "  _(post-fix)_" : ""}`);
    if (filesScanned.length > 0) lines.push(`**Files scanned:** ${filesScanned.length}`);
    lines.push("");

    lines.push(`## Critical Blockers`);
    if (criticalBlockers.length === 0 || fixesApplied) {
      lines.push("_None — no critical risks remaining._");
    } else {
      criticalBlockers.forEach(r => {
        lines.push(`- **${r.category}** — \`${r.file}\` — ${r.shortExplanation}`);
      });
    }
    lines.push("");

    lines.push(`## Risk Summary (${risks.length})`);
    if (risks.length === 0) {
      lines.push("_No findings._");
    } else {
      lines.push("");
      lines.push("| Severity | Category | File | Finding |");
      lines.push("| --- | --- | --- | --- |");
      risks.forEach(r => {
        const sev = fixesApplied ? "RESOLVED" : r.severity.toUpperCase();
        const file = r.file.replace(/\|/g, "\\|");
        const finding = r.shortExplanation.replace(/\|/g, "\\|");
        lines.push(`| ${sev} | ${r.category} | \`${file}\` | ${finding} |`);
      });
    }
    lines.push("");

    lines.push(`## Recommended Fixes`);
    if (risks.length === 0) {
      lines.push("_No fixes required._");
    } else {
      risks.forEach(r => {
        lines.push("");
        lines.push(`### ${r.category} — \`${r.file}\``);
        lines.push(`- **What broke:** ${r.whatBroke}`);
        lines.push(`- **Why it matters:** ${r.whyMatters}`);
        lines.push(`- **How to fix:** ${r.howToFix}`);
        if (r.fixPlan.length > 0) {
          lines.push(`- **Fix plan:**`);
          r.fixPlan.forEach((s, i) => lines.push(`  ${i + 1}. ${s}`));
        }
      });
    }
    lines.push("");

    lines.push(`## Checklist Result`);
    if (gates.length === 0) {
      lines.push("_No checks ran._");
    } else {
      gates.forEach(g => {
        const mark = g.state === "pass" ? "✅" : g.state === "warning" ? "⚠️" : "❌";
        const detail = g.detail ? ` — ${g.detail}` : "";
        lines.push(`- ${mark} **${g.label}** (${g.state.toUpperCase()})${detail}`);
      });
    }
    lines.push("");

    lines.push(`## Accuracy / Evidence`);
    lines.push(`- **Scan mode:** ${isSample ? "Sample — seeded example data" : "Live — public GitHub Contents API"}`);
    lines.push(`- **Files scanned:** ${filesScanned.length || "—"}`);
    if (rulesExecuted != null) lines.push(`- **Rules executed:** ${rulesExecuted}`);
    if (!isSample) {
      risks.filter(r => r.ruleId).forEach(r => {
        lines.push(`- ${r.category} (\`${r.file}\`): rule \`${r.ruleId}\`` +
          (r.confidence ? ` · confidence: ${r.confidence}` : "") +
          (r.evidenceSnippet ? ` · evidence: ${r.evidenceSnippet}` : ""));
      });
    }
    lines.push("");

    lines.push("---");
    lines.push(`_Generated by RepoGuard${isSample ? " · SAMPLE DATA — not a real repository scan" : " · LIVE SCAN from public GitHub API"}._`);
    return lines.join("\n");
  }

  function handleDownloadMarkdown() {
    downloadBlob(buildMarkdown(), "text/markdown;charset=utf-8;",
      `repoguard-${slug}.md`);
  }

  const SectionTitle: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div style={{ fontSize: 11, color: "#C49A47", fontWeight: 800, letterSpacing: "0.10em",
      textTransform: "uppercase", marginBottom: 10, marginTop: 18 }}>{children}</div>
  );

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.65)",
      display: "grid", placeItems: "center", zIndex: 1100, padding: 16,
      overflowY: "auto", animation: "wrFadeIn 220ms ease both",
    }}>
      <div onClick={e => e.stopPropagation()} className="wr-report-modal" style={{
        width: "100%", maxWidth: 720, background: cardBg, color: text,
        borderRadius: 18,
        border, boxShadow: "0 28px 80px rgba(0,0,0,0.45)",
        margin: "auto", maxHeight: "92vh", overflowY: "auto",
        // minWidth: 0 lets long file paths wrap inside the modal instead
        // of pushing the modal wider than its column.
        minWidth: 0,
      }}>
        <style>{`
          .wr-report-modal { padding: 24px 24px 28px; }
          @media (max-width: 600px) {
            .wr-report-modal { padding: 18px 16px 22px; border-radius: 14px; }
          }
          /* Risk Summary / Checklist rows: on phones, stack the file path
             beneath the category so the row never has to be wider than the
             modal. The severity badge keeps its place on the right. */
          .wr-modal-row {
            display: grid;
            grid-template-columns: auto minmax(0, 1fr) auto;
            gap: 10px; align-items: center;
          }
          @media (max-width: 540px) {
            .wr-modal-row {
              grid-template-columns: minmax(0, 1fr) auto;
              row-gap: 4px;
            }
            .wr-modal-row > .wr-modal-row-mid {
              grid-column: 1 / -1;
              white-space: normal !important;
              word-break: break-all;
            }
          }
        `}</style>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
          marginBottom: 6, gap: 12, flexWrap: "wrap" }}>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ fontSize: 11, color: "#C49A47", fontWeight: 800, letterSpacing: "0.10em",
              textTransform: "uppercase" }}>
              Safe-to-Ship Report{isSample && " · Sample"}
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, marginTop: 2,
              overflow: "hidden", textOverflow: "ellipsis" }}>
              {projectName}
            </div>
            {repoUrl && (
              <a href={repoUrl} target="_blank" rel="noopener noreferrer" style={{
                fontSize: 11.5, color: "#C49A47", fontFamily: "monospace",
                textDecoration: "none", wordBreak: "break-all",
              }}>{repoUrl}</a>
            )}
          </div>
          <button onClick={onClose} style={{
            border: "none", background: dark ? "rgba(255,255,255,0.08)" : "rgba(28,44,69,0.07)",
            color: text, fontSize: 18, cursor: "pointer", borderRadius: 10,
            width: 36, height: 36, display: "flex", alignItems: "center", justifyContent: "center",
          }}>✕</button>
        </div>

        <div style={{ display: "flex", gap: 16, marginTop: 12, flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: 12, color: sub }}>Scan time: <b style={{ color: text }}>{scanTime}</b></span>
          <span style={{ fontSize: 12, color: sub }}>Integrity: <b style={{ color: "#C49A47" }}>{scoreBefore}% → {scoreAfter}%</b></span>
          {filesScanned.length > 0 && (
            <span style={{ fontSize: 12, color: sub }}>Files: <b style={{ color: text }}>{filesScanned.length}</b></span>
          )}
          <span style={{
            padding: "4px 10px", borderRadius: 999, fontSize: 11, fontWeight: 800,
            letterSpacing: "0.08em", background: `${statusColor}20`,
            border: `1px solid ${statusColor}66`, color: statusColor,
          }}>{statusLabel}</span>
        </div>

        {/* Scan mode banner */}
        <div style={{ marginTop: 10, padding: "8px 12px", borderRadius: 8,
          background: isSample ? "rgba(252,211,77,0.08)" : "rgba(110,231,183,0.08)",
          border: `1px solid ${isSample ? "rgba(252,211,77,0.30)" : "rgba(110,231,183,0.30)"}`,
          fontSize: 12, fontWeight: 700,
          color: isSample ? "#FCD34D" : "#6EE7B7" }}>
          {isSample
            ? "SAMPLE REPORT — not a live repository scan. Findings below are seeded example data."
            : "LIVE REPORT — generated from public GitHub repository contents via unauthenticated GitHub API."}
        </div>

        {/* Accuracy / Evidence section */}
        <SectionTitle>Accuracy / Evidence</SectionTitle>
        <div style={{ display: "grid", gap: 4, fontSize: 12.5 }}>
          <div><b style={{ color: text }}>Scan mode:</b>{" "}
            <span style={{ color: sub }}>{isSample ? "Sample — seeded example data (not a live repository scan)" : "Live — public GitHub Contents API (no auth)"}</span>
          </div>
          {projectName && <div><b style={{ color: text }}>Repository:</b>{" "}
            <span style={{ color: sub }}>{projectName}</span>
          </div>}
          <div><b style={{ color: text }}>Scan time:</b>{" "}
            <span style={{ color: sub }}>{scanTime}</span>
          </div>
          <div><b style={{ color: text }}>Files scanned:</b>{" "}
            <span style={{ color: sub }}>{filesScanned.length > 0 ? filesScanned.length : "—"}</span>
          </div>
          {rulesExecuted != null && <div><b style={{ color: text }}>Rules executed:</b>{" "}
            <span style={{ color: sub }}>{rulesExecuted} distinct check categories</span>
          </div>}
          {!isSample && risks.length > 0 && risks.some(r => r.ruleId) && (
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 11, color: "#C49A47", fontWeight: 700, textTransform: "uppercase",
                letterSpacing: "0.08em", marginBottom: 6 }}>Finding evidence</div>
              <div style={{ display: "grid", gap: 4 }}>
                {risks.filter(r => r.ruleId).map(r => (
                  <div key={r.id} style={{ padding: "6px 10px", borderRadius: 8,
                    background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
                    border: `1px solid ${dark ? "rgba(255,255,255,0.07)" : "rgba(28,44,69,0.08)"}`,
                    fontSize: 11.5 }}>
                    <div style={{ fontWeight: 700, color: text, marginBottom: 2 }}>
                      {r.category} · <span style={{ fontFamily: "monospace", color: sub }}>{r.file}</span>
                    </div>
                    <div style={{ color: sub }}>
                      {r.ruleId && <span>Rule: <code style={{ fontFamily: "monospace" }}>{r.ruleId}</code></span>}
                      {r.evidenceType && <span> · {r.evidenceType}</span>}
                      {r.confidence && <span> · confidence: <b>{r.confidence}</b></span>}
                    </div>
                    {r.evidenceSnippet && (
                      <div style={{ fontFamily: "monospace", color: sub, marginTop: 2, fontSize: 11,
                        wordBreak: "break-all" }}>{r.evidenceSnippet}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Critical blockers */}
        <SectionTitle>Critical Blockers</SectionTitle>
        {criticalBlockers.length === 0 || fixesApplied ? (
          <div style={{ fontSize: 13.5, color: sub }}>None — no critical risks remaining.</div>
        ) : (
          <ul style={{ margin: 0, paddingLeft: 20, color: text, fontSize: 13.5, lineHeight: 1.7,
            wordBreak: "break-word", overflowWrap: "anywhere" }}>
            {criticalBlockers.map(r => (
              <li key={r.id}>
                <b>{r.category}</b> · <span style={{ fontFamily: "monospace", color: sub,
                  wordBreak: "break-all", overflowWrap: "anywhere" }}>{r.file}</span> — {r.shortExplanation}
              </li>
            ))}
          </ul>
        )}

        {/* Risk summary */}
        <SectionTitle>Risk Summary</SectionTitle>
        <div style={{ display: "grid", gap: 6 }}>
          {risks.map(r => {
            const sev = SEVERITY_COLOR[r.severity];
            const resolved = fixesApplied;
            return (
              <div key={r.id} className="wr-modal-row" style={{
                padding: "8px 12px", borderRadius: 10,
                background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
                borderLeft: `3px solid ${resolved ? "#6EE7B7" : sev}`,
              }}>
                <span style={{ fontSize: 13, fontWeight: 700 }}>{r.category}</span>
                <span className="wr-modal-row-mid" style={{ fontSize: 12, color: sub, fontFamily: "monospace",
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }}>
                  {r.file}
                </span>
                <span style={{
                  padding: "2px 7px", borderRadius: 999, fontSize: 10, fontWeight: 800,
                  letterSpacing: "0.06em", background: resolved ? "rgba(110,231,183,0.18)" : `${sev}20`,
                  border: `1px solid ${resolved ? "rgba(110,231,183,0.50)" : `${sev}55`}`,
                  color: resolved ? "#6EE7B7" : sev, textTransform: "uppercase",
                }}>
                  {resolved ? "RESOLVED" : r.severity}
                </span>
              </div>
            );
          })}
        </div>

        {/* Recommended fixes */}
        <SectionTitle>Recommended Fixes</SectionTitle>
        <div style={{ display: "grid", gap: 10 }}>
          {risks.map(r => (
            <div key={r.id} style={{ paddingTop: 8, borderTop: `1px solid ${divider}`, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 700,
                wordBreak: "break-word", overflowWrap: "anywhere" }}>
                {r.category} — <span style={{ fontFamily: "monospace", color: sub, fontWeight: 500,
                  wordBreak: "break-all", overflowWrap: "anywhere" }}>{r.file}</span>
              </div>
              <ol style={{ margin: "6px 0 0", paddingLeft: 20, color: sub, fontSize: 12.5, lineHeight: 1.6,
                wordBreak: "break-word", overflowWrap: "anywhere" }}>
                {r.fixPlan.map((s, i) => <li key={i}>{s}</li>)}
              </ol>
            </div>
          ))}
        </div>

        {/* Checklist results */}
        <SectionTitle>Checklist Result</SectionTitle>
        <div style={{ display: "grid", gap: 6 }}>
          {gates.map(g => {
            const c = GATE_COLOR[g.state];
            return (
              <div key={g.id} className="wr-modal-row" style={{
                padding: "7px 12px", borderRadius: 10,
                background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
              }}>
                <span style={{
                  width: 22, height: 22, borderRadius: "50%",
                  background: `${c}22`, border: `1px solid ${c}66`,
                  color: c, fontWeight: 800, fontSize: 12,
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>{GATE_ICON[g.state]}</span>
                <span className="wr-modal-row-mid" style={{ fontSize: 13, minWidth: 0,
                  overflowWrap: "anywhere" }}>{g.label}</span>
                <span style={{ fontSize: 11, fontWeight: 800, color: c, letterSpacing: "0.06em",
                  textTransform: "uppercase" }}>{g.state}</span>
              </div>
            );
          })}
        </div>

        {/* Footer actions — exports + close */}
        <div style={{ marginTop: 22, display: "flex", justifyContent: "space-between",
          gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button onClick={handleDownloadMarkdown} style={{
              background: "linear-gradient(135deg, #C49A47 0%, #a87d2e 100%)",
              color: "#111", border: "none", borderRadius: 10,
              padding: "10px 16px", fontWeight: 800, fontSize: 13,
              cursor: "pointer", fontFamily: "inherit",
              boxShadow: "0 4px 14px rgba(196,154,71,0.32)",
            }} title="Download a Markdown snapshot of this report">
              ⬇ Download Report
            </button>
            <button onClick={handleCopy} style={ghostBtnStyle(dark, text)}>
              {copyState === "copied" ? "✓ Copied" : copyState === "failed" ? "✕ Copy failed" : "📋 Copy Summary"}
            </button>
            <button onClick={handleDownloadJSON} style={ghostBtnStyle(dark, text)}>
              ⬇ JSON
            </button>
            <button onClick={handleDownloadCSV} style={ghostBtnStyle(dark, text)}>
              ⬇ CSV
            </button>
          </div>
          <button onClick={onClose} style={{
            background: dark ? "rgba(255,255,255,0.08)" : "rgba(28,44,69,0.07)",
            color: text, border: "none", borderRadius: 12,
            padding: "12px 22px", fontWeight: 700, fontSize: 14, cursor: "pointer",
            fontFamily: "inherit",
          }}>Close</button>
        </div>
      </div>
    </div>
  );
}

function ghostBtnStyle(dark: boolean, text: string): React.CSSProperties {
  return {
    background: dark ? "rgba(255,255,255,0.06)" : "rgba(28,44,69,0.06)",
    border: `1px solid ${dark ? "rgba(255,255,255,0.10)" : "rgba(28,44,69,0.12)"}`,
    color: text, borderRadius: 10,
    padding: "10px 14px", fontWeight: 700, fontSize: 12.5,
    cursor: "pointer", fontFamily: "inherit",
  };
}

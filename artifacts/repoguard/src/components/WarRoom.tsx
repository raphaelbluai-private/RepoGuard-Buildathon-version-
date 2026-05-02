import React, { useState } from "react";
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
  type Risk,
  type SafetyGate,
} from "../data/warRoomData";

interface WarRoomProps {
  theme: string;
}

export default function WarRoom({ theme }: WarRoomProps) {
  const dark = theme !== "light";
  const [demoRun, setDemoRun] = useState(false);
  const [fixesApplied, setFixesApplied] = useState(false);
  const [selectedRiskId, setSelectedRiskId] = useState<string | null>(null);
  const [reportOpen, setReportOpen] = useState(false);

  const risks: Risk[] = demoRun ? SEEDED_RISKS : [];
  const gates: SafetyGate[] = !demoRun ? [] : (fixesApplied ? GATES_AFTER : GATES_BEFORE);

  const criticalCount = risks.filter(r => r.severity === "critical").length;
  const scoreCurrent = !demoRun ? 100 : (fixesApplied ? SCORE_AFTER : SCORE_BEFORE);
  const scoreDelta = SCORE_AFTER - SCORE_BEFORE;

  const safeToShip = demoRun && fixesApplied;
  const topBlocker = risks.find(r => r.severity === "critical") ?? risks[0];

  const cardBg     = dark ? "rgba(17,17,17,0.74)" : "rgba(255,255,255,0.92)";
  const cardBorder = dark ? "1px solid rgba(196,154,71,0.18)" : "1px solid rgba(28,44,69,0.10)";
  const subText    = dark ? "rgba(255,255,255,0.58)" : "rgba(28,44,69,0.58)";
  const text       = dark ? "#FFFFFF" : "#1C2C45";
  const subtle     = dark ? "rgba(255,255,255,0.42)" : "rgba(28,44,69,0.42)";
  const divider    = dark ? "rgba(255,255,255,0.07)" : "rgba(28,44,69,0.07)";

  const lastScan = demoRun ? "Just now" : "—";
  const agentSummary = !demoRun
    ? "Idle"
    : fixesApplied
      ? "Generated 5 deterministic fix plans · gates re-validated"
      : "Classified 5 risks across 5 categories";

  const selectedRisk = selectedRiskId ? risks.find(r => r.id === selectedRiskId) : null;

  const Card: React.FC<{ children: React.ReactNode; padding?: string; style?: React.CSSProperties }> = ({ children, padding = "16px 18px", style }) => (
    <div className="relative overflow-hidden" style={{
      background: cardBg, border: cardBorder, borderRadius: 16, padding,
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
        .wr-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .wr-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        @media (max-width: 700px) {
          .wr-grid-3 { grid-template-columns: 1fr 1fr; }
          .wr-grid-2 { grid-template-columns: 1fr; }
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
      `}</style>

      {/* ── 1. Command Dashboard ─────────────────────────────────────────── */}
      <Card padding="22px 22px 20px" style={{ marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
          gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
          <div>
            <SectionLabel>War Room Command</SectionLabel>
            <div style={{ fontSize: "clamp(20px, 3.5vw, 26px)", fontWeight: 800, color: text,
              lineHeight: 1.15 }}>
              Safety command layer for {PROJECT_NAME}
            </div>
            <div style={{ color: subText, marginTop: 6, fontSize: 13.5, lineHeight: 1.55, maxWidth: 560 }}>
              One view of every risk an AI-built app must clear before it ships.
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, flexShrink: 0, flexWrap: "wrap" }}>
            <button
              className="wr-cta"
              onClick={() => { setDemoRun(true); setFixesApplied(false); setSelectedRiskId(null); }}
            >
              {demoRun ? "Re-run Demo Scan" : "Run Demo Scan"}
            </button>
            {fixesApplied && (
              <button
                className="wr-ghost-btn"
                onClick={() => { setFixesApplied(false); setSelectedRiskId(null); }}
                title="Revert fixes to show the unsafe state again"
              >
                ↻ Reset Fixes
              </button>
            )}
          </div>
        </div>

        <div className="wr-grid-3">
          <Tile label="Repo Integrity" value={`${scoreCurrent}%`} accent="#C49A47" theme={theme} />
          <Tile label="Safe-to-Ship" value={!demoRun ? "—" : safeToShip ? "READY" : "BLOCKED"}
            accent={!demoRun ? subtle : safeToShip ? "#6EE7B7" : "#FCA5A5"} theme={theme} />
          <Tile label="Critical Risks" value={!demoRun ? "—" : String(criticalCount)}
            accent={criticalCount > 0 ? "#FCA5A5" : "#6EE7B7"} theme={theme} />
          <Tile label="Last Scan" value={lastScan} accent={text} theme={theme} small />
          <Tile label="Agent Activity" value={agentSummary} accent={text} theme={theme} small />
          <Tile label="Top Blocker"
            value={!demoRun ? "—" : (topBlocker?.shortExplanation ?? "None")}
            accent={topBlocker?.severity ? SEVERITY_COLOR[topBlocker.severity] : "#6EE7B7"}
            theme={theme} small />
        </div>
      </Card>

      {/* ── 2. Before / After Integrity ─────────────────────────────────── */}
      <Card padding="22px 22px 24px" style={{ marginBottom: 14 }}>
        <SectionLabel>Integrity Score · Before vs After Fix Plan</SectionLabel>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 24,
          flexWrap: "wrap", padding: "10px 0 6px" }}>
          <ScoreBlock label="Before Scan" value={demoRun ? SCORE_BEFORE : 0} color="#FCA5A5" theme={theme} />
          <div style={{ fontSize: 28, color: subtle, fontWeight: 700 }}>→</div>
          <ScoreBlock label="After Fix Plan" value={demoRun ? SCORE_AFTER : 0} color="#6EE7B7" theme={theme} />
          <div style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
            padding: "10px 16px", borderRadius: 12,
            background: "rgba(196,154,71,0.10)", border: "1px solid rgba(196,154,71,0.30)",
          }}>
            <div style={{ fontSize: 10, color: "#C49A47", fontWeight: 700, letterSpacing: "0.08em" }}>
              SCORE Δ
            </div>
            <div style={{ fontSize: 26, fontWeight: 800, color: "#C49A47" }}>
              {demoRun ? `+${scoreDelta}` : "—"}
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

        {!demoRun ? (
          <EmptyState
            theme={theme}
            title="No scan loaded"
            body='Click "Run Demo Scan" to load deterministic seeded findings (no GitHub OAuth required).'
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
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
              marginBottom: 10, gap: 8, flexWrap: "wrap" }}>
              <div style={{ fontSize: 14, fontWeight: 800, color: "#C49A47", letterSpacing: "0.04em" }}>
                {selectedRisk.category} · {selectedRisk.file}
              </div>
              <button className="wr-ghost-btn" onClick={() => setSelectedRiskId(null)}
                style={{ padding: "5px 10px", fontSize: 12 }}>✕ Close</button>
            </div>

            <DetailRow label="What broke"     body={selectedRisk.whatBroke}  theme={theme} />
            <DetailRow label="Why it matters" body={selectedRisk.whyMatters} theme={theme} />
            <DetailRow label="How to fix"     body={selectedRisk.howToFix}   theme={theme} />

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

        {!demoRun ? (
          <EmptyState theme={theme} title="No checklist evaluated" body="Run a demo scan to evaluate the 7 safety gates." />
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
            const milestoneIndex = !demoRun ? -1 : (fixesApplied ? 5 : 4);
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
        <SectionLabel>Buildathon Evidence</SectionLabel>
        <div style={{ display: "grid", gap: 8, fontSize: 13.5, color: text, lineHeight: 1.6 }}>
          <EvidenceRow label="Built during" value="Replit 10-Year Buildathon" theme={theme} />
          <EvidenceRow label="Before"       value="Basic repo scan · binary findings, no fix plans" theme={theme} />
          <EvidenceRow label="After"        value="War Room safety command layer with deterministic fix plans" theme={theme} />
          <EvidenceRow label="Workflow"     value="Agent-assisted iterative build · prompt → scan → fix → ship" theme={theme} />
          <EvidenceRow label="Demo path"    value="Safe-to-Ship readiness — works without external OAuth" theme={theme} />
        </div>
      </Card>

      {/* ── 7. Generate Report ──────────────────────────────────────────── */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>
        <button className="wr-cta" onClick={() => setReportOpen(true)} disabled={!demoRun}>
          Open Safe-to-Ship Report
        </button>
      </div>

      {reportOpen && (
        <SafeToShipReport
          onClose={() => setReportOpen(false)}
          theme={theme}
          risks={risks}
          gates={gates}
          scoreBefore={SCORE_BEFORE}
          scoreAfter={fixesApplied ? SCORE_AFTER : scoreCurrent}
          fixesApplied={fixesApplied}
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
      background: dark ? "rgba(255,255,255,0.04)" : "rgba(28,44,69,0.05)",
      border: dark ? "1px solid rgba(255,255,255,0.07)" : "1px solid rgba(28,44,69,0.08)",
    }}>
      <div style={{ fontSize: 10, color: dark ? "rgba(255,255,255,0.45)" : "rgba(28,44,69,0.50)",
        fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: small ? 13 : 18, fontWeight: 800, color: accent,
        lineHeight: 1.25, overflow: "hidden", textOverflow: "ellipsis",
        ...(small ? { whiteSpace: "nowrap" as const } : {}) }}>
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

function RiskCardView({ risk, fixed, selected, onClick, theme }: {
  risk: Risk; fixed: boolean; selected: boolean; onClick: () => void; theme: string;
}) {
  const dark = theme !== "light";
  const status = fixed ? "resolved" : risk.status;
  const sevColor = SEVERITY_COLOR[risk.severity];
  const statusColor = status === "resolved" ? "#6EE7B7" : status === "fixing" ? "#FCD34D" : sevColor;
  const statusLabel = status === "resolved" ? "Resolved" : status === "fixing" ? "Fixing" : "Open";

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

function SafeToShipReport({ onClose, theme, risks, gates, scoreBefore, scoreAfter, fixesApplied }: {
  onClose: () => void;
  theme: string;
  risks: Risk[];
  gates: SafetyGate[];
  scoreBefore: number;
  scoreAfter: number;
  fixesApplied: boolean;
}) {
  const dark = theme !== "light";
  const cardBg = dark ? "rgba(18,24,36,0.98)" : "#FFFFFF";
  const text   = dark ? "#FFFFFF" : "#1C2C45";
  const sub    = dark ? "rgba(255,255,255,0.55)" : "rgba(28,44,69,0.60)";
  const border = dark ? "1px solid rgba(196,154,71,0.25)" : "1px solid rgba(28,44,69,0.12)";
  const divider = dark ? "rgba(255,255,255,0.07)" : "rgba(28,44,69,0.08)";

  const status = fixesApplied ? "READY TO SHIP" : "BLOCKED";
  const statusColor = fixesApplied ? "#6EE7B7" : "#FCA5A5";
  const criticalBlockers = risks.filter(r => r.severity === "critical");
  const scanTime = new Date().toLocaleString();

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
      <div onClick={e => e.stopPropagation()} style={{
        width: "100%", maxWidth: 720, background: cardBg, color: text,
        borderRadius: 18, padding: "24px 24px 28px",
        border, boxShadow: "0 28px 80px rgba(0,0,0,0.45)",
        margin: "auto", maxHeight: "92vh", overflowY: "auto",
      }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
          marginBottom: 6, gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 11, color: "#C49A47", fontWeight: 800, letterSpacing: "0.10em",
              textTransform: "uppercase" }}>
              Safe-to-Ship Report
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, marginTop: 2 }}>
              {PROJECT_NAME}
            </div>
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
          <span style={{
            padding: "4px 10px", borderRadius: 999, fontSize: 11, fontWeight: 800,
            letterSpacing: "0.08em", background: `${statusColor}20`,
            border: `1px solid ${statusColor}66`, color: statusColor,
          }}>{status}</span>
        </div>

        {/* Critical blockers */}
        <SectionTitle>Critical Blockers</SectionTitle>
        {criticalBlockers.length === 0 || fixesApplied ? (
          <div style={{ fontSize: 13.5, color: sub }}>None — no critical risks remaining.</div>
        ) : (
          <ul style={{ margin: 0, paddingLeft: 20, color: text, fontSize: 13.5, lineHeight: 1.7 }}>
            {criticalBlockers.map(r => (
              <li key={r.id}>
                <b>{r.category}</b> · <span style={{ fontFamily: "monospace", color: sub }}>{r.file}</span> — {r.shortExplanation}
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
              <div key={r.id} style={{
                display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 10, alignItems: "center",
                padding: "8px 12px", borderRadius: 10,
                background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
                borderLeft: `3px solid ${resolved ? "#6EE7B7" : sev}`,
              }}>
                <span style={{ fontSize: 13, fontWeight: 700 }}>{r.category}</span>
                <span style={{ fontSize: 12, color: sub, fontFamily: "monospace",
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
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
            <div key={r.id} style={{ paddingTop: 8, borderTop: `1px solid ${divider}` }}>
              <div style={{ fontSize: 13, fontWeight: 700 }}>
                {r.category} — <span style={{ fontFamily: "monospace", color: sub, fontWeight: 500 }}>{r.file}</span>
              </div>
              <ol style={{ margin: "6px 0 0", paddingLeft: 20, color: sub, fontSize: 12.5, lineHeight: 1.6 }}>
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
              <div key={g.id} style={{
                display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 10, alignItems: "center",
                padding: "7px 12px", borderRadius: 10,
                background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
              }}>
                <span style={{
                  width: 22, height: 22, borderRadius: "50%",
                  background: `${c}22`, border: `1px solid ${c}66`,
                  color: c, fontWeight: 800, fontSize: 12,
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>{GATE_ICON[g.state]}</span>
                <span style={{ fontSize: 13 }}>{g.label}</span>
                <span style={{ fontSize: 11, fontWeight: 800, color: c, letterSpacing: "0.06em",
                  textTransform: "uppercase" }}>{g.state}</span>
              </div>
            );
          })}
        </div>

        {/* Footer actions */}
        <div style={{ marginTop: 22, display: "flex", justifyContent: "flex-end", gap: 8 }}>
          <button onClick={onClose} style={{
            background: "#C49A47", color: "#111", border: "none", borderRadius: 12,
            padding: "12px 22px", fontWeight: 800, fontSize: 14, cursor: "pointer",
            fontFamily: "inherit",
          }}>Close Report</button>
        </div>
      </div>
    </div>
  );
}

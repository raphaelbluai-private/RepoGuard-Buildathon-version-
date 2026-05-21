import React, { useMemo, useState } from "react";
import { scanExtensions, type ExtensionGuardResult } from "../lib/extensionGuard";

type Props = {
  theme: string;
  onResultChange?: (result: ExtensionGuardResult | null) => void;
};

const SAMPLE = `ms-python.python@2026.1.0
dbaeumer.vscode-eslint@3.0.16
esbenp.prettier-vscode@11.0.0
github.copilot@1.301.0
security.auth-helper@0.1.4
remote.proxy-sync@2.0.0
prettier.prettier-vscode@1.0.0`;

const colorBySeverity: Record<string, string> = {
  critical: "#FCA5A5",
  high: "#FCA5A5",
  medium: "#FCD34D",
  low: "#93C5FD",
};

const colorByStatus: Record<string, string> = {
  LOW: "#6EE7B7",
  REVIEW: "#FCD34D",
  HIGH: "#FCA5A5",
  BLOCK: "#FCA5A5",
};

export default function ExtensionGuardPanel({ theme, onResultChange }: Props) {
  const dark = theme !== "light";
  const [input, setInput] = useState("");
  const [result, setResult] = useState<ExtensionGuardResult | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const text = dark ? "#FFFFFF" : "#1C2C45";
  const muted = dark ? "rgba(255,255,255,0.62)" : "rgba(28,44,69,0.62)";
  const cardBg = dark ? "rgba(17,17,17,0.74)" : "rgba(255,255,255,0.92)";
  const border = dark ? "1px solid rgba(196,154,71,0.18)" : "1px solid rgba(28,44,69,0.10)";

  const selected = useMemo(
    () => result?.findings.find((finding) => finding.id === selectedId) ?? result?.findings[0] ?? null,
    [result, selectedId],
  );

  function runScan(nextInput = input) {
    const next = scanExtensions(nextInput);
    setResult(next);
    setSelectedId(next.findings[0]?.id ?? null);
    onResultChange?.(next);
  }

  function loadSample() {
    setInput(SAMPLE);
    runScan(SAMPLE);
  }

  function reset() {
    setInput("");
    setResult(null);
    setSelectedId(null);
    onResultChange?.(null);
  }

  return (
    <div style={{ animation: "fadeSlide 280ms ease" }}>
      <section style={{
        borderRadius: 18,
        border: "1px solid rgba(196,154,71,0.32)",
        background: dark ? "linear-gradient(135deg, rgba(196,154,71,0.12), rgba(28,44,69,0.55))" : "linear-gradient(135deg, rgba(196,154,71,0.18), rgba(255,255,255,0.85))",
        padding: 22,
        marginBottom: 14,
      }}>
        <div style={{ color: "#C49A47", fontWeight: 900, letterSpacing: "0.14em", textTransform: "uppercase", fontSize: 11, marginBottom: 8 }}>ExtensionGuard</div>
        <h1 style={{ color: text, fontWeight: 900, fontSize: 26, lineHeight: 1.1, margin: 0 }}>Developer Tooling Supply Chain Risk</h1>
        <p style={{ color: muted, fontSize: 14, lineHeight: 1.55, maxWidth: 780, marginTop: 8 }}>
          Paste VS Code extension inventory from code --list-extensions --show-versions. RepoGuard parses publisher, name, version, and runs deterministic local checks without external calls or workstation access.
        </p>
      </section>

      <section style={{ background: cardBg, border, borderRadius: 16, padding: 18, marginBottom: 14 }}>
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={"ms-python.python@2026.1.0\ndbaeumer.vscode-eslint@3.0.16\nesbenp.prettier-vscode@11.0.0"}
          spellCheck={false}
          autoCapitalize="none"
          autoCorrect="off"
          style={{
            width: "100%",
            minHeight: 150,
            borderRadius: 12,
            padding: 14,
            background: dark ? "rgba(255,255,255,0.05)" : "rgba(28,44,69,0.04)",
            border: dark ? "1px solid rgba(255,255,255,0.12)" : "1px solid rgba(28,44,69,0.14)",
            color: text,
            fontFamily: "monospace",
            fontSize: 13,
            lineHeight: 1.5,
            boxSizing: "border-box",
          }}
        />
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 12 }}>
          <button className="wr-cta" onClick={() => runScan()} disabled={!input.trim()}>Scan Tooling Risk</button>
          <button className="wr-ghost-btn" onClick={loadSample}>Load Sample Inventory</button>
          <button className="wr-ghost-btn" onClick={reset}>Reset ExtensionGuard</button>
        </div>
      </section>

      <div className="wr-grid-3" style={{ marginBottom: 14 }}>
        <div style={{ background: cardBg, border, borderRadius: 16, padding: 16 }}>
          <div style={{ color: muted, fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em" }}>Extensions Scanned</div>
          <div style={{ color: "#C49A47", fontSize: 28, fontWeight: 900, marginTop: 8 }}>{result?.extensionsScanned ?? "—"}</div>
        </div>
        <div style={{ background: cardBg, border, borderRadius: 16, padding: 16 }}>
          <div style={{ color: muted, fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em" }}>Tooling Risk Score</div>
          <div style={{ color: result ? colorByStatus[result.status] : "#C49A47", fontSize: 28, fontWeight: 900, marginTop: 8 }}>{result ? `${result.toolingRiskScore}%` : "—"}</div>
        </div>
        <div style={{ background: cardBg, border, borderRadius: 16, padding: 16 }}>
          <div style={{ color: muted, fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em" }}>Status</div>
          <div style={{ color: result ? colorByStatus[result.status] : "#C49A47", fontSize: 24, fontWeight: 900, marginTop: 10 }}>{result?.status ?? "NOT RUN"}</div>
        </div>
      </div>

      {result && (
        <div className="wr-grid-2">
          <section style={{ background: cardBg, border, borderRadius: 16, padding: 18 }}>
            <div style={{ color: "#C49A47", fontWeight: 900, letterSpacing: "0.10em", textTransform: "uppercase", fontSize: 11, marginBottom: 10 }}>Extension Findings</div>
            {result.findings.length === 0 ? (
              <div style={{ color: "#6EE7B7", fontWeight: 800 }}>No deterministic ExtensionGuard risks found.</div>
            ) : result.findings.map((finding) => (
              <button key={finding.id} onClick={() => setSelectedId(finding.id)} style={{
                display: "block",
                width: "100%",
                textAlign: "left",
                border: `1px solid ${(colorBySeverity[finding.severity] ?? "#FCD34D")}44`,
                background: selectedId === finding.id ? "rgba(196,154,71,0.12)" : "transparent",
                color: text,
                borderRadius: 12,
                padding: 12,
                marginBottom: 8,
                cursor: "pointer",
              }}>
                <div style={{ fontWeight: 800 }}>{finding.extensionId}</div>
                <div style={{ color: muted, fontSize: 12, marginTop: 3 }}>{finding.ruleId} · {finding.severity}</div>
              </button>
            ))}
          </section>
          <section style={{ background: cardBg, border, borderRadius: 16, padding: 18 }}>
            <div style={{ color: "#C49A47", fontWeight: 900, letterSpacing: "0.10em", textTransform: "uppercase", fontSize: 11, marginBottom: 10 }}>Evidence + Fix Plan</div>
            {selected ? (
              <div style={{ border: `1px solid ${(colorBySeverity[selected.severity] ?? "#FCD34D")}44`, borderRadius: 14, padding: 14 }}>
                <div style={{ color: text, fontWeight: 900 }}>{selected.extensionId}</div>
                <p style={{ color: text, fontSize: 13, lineHeight: 1.5 }}>{selected.whatBroke}</p>
                <p style={{ color: muted, fontSize: 12.5, lineHeight: 1.5 }}>{selected.whyMatters}</p>
                <p style={{ color: "#6EE7B7", fontSize: 12.5, lineHeight: 1.5 }}>{selected.howToFix}</p>
                <div style={{ color: muted, fontFamily: "monospace", fontSize: 11, overflowWrap: "anywhere" }}>Evidence: {selected.evidence} · Confidence: {selected.confidence}</div>
              </div>
            ) : <div style={{ color: muted }}>No finding selected.</div>}
            <div style={{ color: muted, fontSize: 12, lineHeight: 1.5, marginTop: 12 }}>
              <b style={{ color: text }}>Recommended actions:</b>
              <ul style={{ paddingLeft: 18 }}>{result.recommendations.map((item, index) => <li key={index}>{item}</li>)}</ul>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

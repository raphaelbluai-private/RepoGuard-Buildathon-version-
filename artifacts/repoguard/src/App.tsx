import React, { useEffect, useMemo, useRef, useState } from "react";
import { RepositorySourcePicker, type RepoItem } from "./components/RepositorySourcePicker";
import { useIsMobile } from "./hooks/use-mobile";
import WarRoomFeed from "./components/WarRoomFeed";
import RepoGuardCore, { type RGStatus } from "./components/RepoGuardCore";

const pages = ["Command", "Breach", "Correction", "Resolution"];

// ─── Shared AudioContext ─────────────────────────────────────────────────────
let _ctx: AudioContext | null = null;

function getCtx(): AudioContext | null {
  const AC = (window as any).AudioContext || (window as any).webkitAudioContext;
  if (!AC) return null;
  if (!_ctx) _ctx = new AC();
  if (_ctx.state === "suspended") _ctx.resume();
  return _ctx;
}

function warmAudio() {
  const ctx = getCtx();
  if (!ctx) return;
  const buf = ctx.createBuffer(1, 1, 22050);
  const src = ctx.createBufferSource();
  src.buffer = buf;
  src.connect(ctx.destination);
  src.start(0);
}

function haptic(enabled: boolean, pattern: any = 10) {
  if (!enabled) return;
  if (typeof navigator !== "undefined" && navigator.vibrate) navigator.vibrate(pattern);
}

function playClick(enabled: boolean) {
  if (!enabled) return;
  const ctx = getCtx();
  if (!ctx) return;
  const now = ctx.currentTime;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = "sine";
  osc.frequency.setValueAtTime(400, now);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.04, now + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.06);
  osc.connect(gain); gain.connect(ctx.destination);
  osc.start(now); osc.stop(now + 0.07);
}

function playSwoosh(enabled: boolean) {
  if (!enabled) return;
  const ctx = getCtx();
  if (!ctx) return;
  const now = ctx.currentTime;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  const filter = ctx.createBiquadFilter();
  osc.type = "triangle";
  osc.frequency.setValueAtTime(540, now);
  osc.frequency.exponentialRampToValueAtTime(220, now + 0.22);
  filter.type = "lowpass"; filter.frequency.setValueAtTime(1400, now);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.06, now + 0.03);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.24);
  osc.connect(filter); filter.connect(gain); gain.connect(ctx.destination);
  osc.start(now); osc.stop(now + 0.26);
}

function playPop(enabled: boolean) {
  if (!enabled) return;
  const ctx = getCtx();
  if (!ctx) return;
  const now = ctx.currentTime;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = "sine";
  osc.frequency.setValueAtTime(660, now);
  osc.frequency.exponentialRampToValueAtTime(900, now + 0.08);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.055, now + 0.015);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.14);
  osc.connect(gain); gain.connect(ctx.destination);
  osc.start(now); osc.stop(now + 0.16);
}

function playAlert(enabled: boolean) {
  if (!enabled) return;
  const ctx = getCtx();
  if (!ctx) return;
  const now = ctx.currentTime;
  [0, 0.18, 0.36].forEach(offset => {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(180, now + offset);
    gain.gain.setValueAtTime(0.0001, now + offset);
    gain.gain.exponentialRampToValueAtTime(0.07, now + offset + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + offset + 0.14);
    osc.connect(gain); gain.connect(ctx.destination);
    osc.start(now + offset); osc.stop(now + offset + 0.16);
  });
}

function playTing(enabled: boolean) {
  if (!enabled) return;
  const ctx = getCtx();
  if (!ctx) return;
  const now = ctx.currentTime;
  [[880, 0.06], [1320, 0.03]].forEach(([freq, vol]) => {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(freq as number, now);
    gain.gain.setValueAtTime(vol as number, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.4);
    osc.connect(gain); gain.connect(ctx.destination);
    osc.start(now); osc.stop(now + 1.5);
  });
}

// ─── timeAgo ─────────────────────────────────────────────────────────────────
function timeAgo(isoTime: string): string {
  const diff = Math.floor((Date.now() - new Date(isoTime).getTime()) / 1000);
  if (diff < 5) return "just now";
  if (diff < 60) return `${diff}s ago`;
  const min = Math.floor(diff / 60);
  if (min < 60) return `${min}m ago`;
  return `${Math.floor(min / 60)}h ago`;
}

// ─── LiveStatusDot ────────────────────────────────────────────────────────────
function LiveStatusDot({ color, variant = "blink" }: { color: string; variant?: "blink" | "pulse" | "ping" }) {
  if (variant === "ping") {
    return (
      <span style={{ position: "relative", display: "inline-flex", alignItems: "center",
        justifyContent: "center", width: 9, height: 9, flexShrink: 0 }}>
        <span className="animate-ping" style={{
          position: "absolute", width: "100%", height: "100%",
          borderRadius: "50%", background: color, opacity: 0.6,
        }} />
        <span style={{ width: 7, height: 7, borderRadius: "50%", background: color,
          boxShadow: `0 0 8px ${color}`, position: "relative" }} />
      </span>
    );
  }
  if (variant === "pulse") {
    return (
      <span className="animate-pulse" style={{
        width: 9, height: 9, borderRadius: "50%", background: color,
        display: "inline-block", flexShrink: 0,
        boxShadow: `0 0 10px ${color}`,
      }} />
    );
  }
  return (
    <span style={{
      width: 9, height: 9, borderRadius: "50%", background: color,
      display: "inline-block", flexShrink: 0,
      animation: "statusBlink 1.8s ease-in-out infinite",
      boxShadow: `0 0 10px ${color}`,
    }} />
  );
}

// ─── LivePulse ───────────────────────────────────────────────────────────────
function LivePulse({ theme }: { theme: string }) {
  const dark = theme === "dark";
  return (
    <div className="live-pulse" style={{
      display: "inline-flex", alignItems: "center", gap: 8,
      padding: "6px 12px", borderRadius: 999,
      background: dark ? "rgba(255,255,255,0.05)" : "rgba(28,44,69,0.06)",
      border: "1px solid rgba(196,154,71,0.22)",
    }}>
      <span style={{
        width: 8, height: 8, borderRadius: "50%", background: "#6EE7B7",
        animation: "pulseDot 1.4s ease-in-out infinite",
      }} />
      <span style={{ fontSize: 11, color: dark ? "rgba(255,255,255,0.72)" : "rgba(28,44,69,0.72)" }}>
        Live scan active
      </span>
    </div>
  );
}

// ─── ThreatBadge ──────────────────────────────────────────────────────────────
function ThreatBadge({ status, theme }: { status: string; theme?: string }) {
  const dark = theme !== "light";
  const levelMap: Record<string, "low" | "warning" | "critical" | "stabilized"> = {
    secure:     "low",
    monitoring: "low",
    warning:    "warning",
    correcting: "warning",
    breach:     "critical",
    resolved:   "stabilized",
  };
  const level = levelMap[status] ?? "low";

  const darkStyles: Record<string, string> = {
    low:        "bg-blue-500/10 text-blue-300 border-blue-400/30",
    warning:    "bg-yellow-500/10 text-yellow-300 border-yellow-400/30",
    critical:   "bg-red-500/10 text-red-300 border-red-400/30",
    stabilized: "bg-emerald-500/10 text-emerald-300 border-emerald-400/30",
  };

  const lightStyles: Record<string, string> = {
    low:        "bg-blue-100 text-blue-800 border-blue-400/50",
    warning:    "bg-yellow-100 text-yellow-800 border-yellow-500/50",
    critical:   "bg-red-100 text-red-800 border-red-400/50",
    stabilized: "bg-emerald-100 text-emerald-800 border-emerald-500/50",
  };

  const styles = dark ? darkStyles : lightStyles;
  const dotClass = level === "critical" ? "animate-threat-pulse" : "animate-pulse";

  const label = {
    low:        "Threat Level: Low",
    warning:    "Threat Level: Warning",
    critical:   "Threat Level: Critical",
    stabilized: "Threat Level: Stabilized",
  }[level];

  return (
    <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold ${styles[level]}`}>
      <span className={`h-2.5 w-2.5 rounded-full bg-current ${dotClass}`} />
      {label}
    </div>
  );
}

// ─── CommandTicker ────────────────────────────────────────────────────────────
function CommandTicker({ theme }: { theme: string }) {
  const dark = theme === "dark";
  return (
    <div className="cmd-ticker" style={{
      overflow: "hidden", whiteSpace: "nowrap", borderRadius: 12,
      border: "1px solid rgba(196,154,71,0.18)",
      background: dark ? "rgba(17,17,17,0.6)" : "rgba(255,255,255,0.85)",
      padding: "8px 0", marginBottom: 12,
    }}>
      <div style={{
        display: "inline-block", paddingLeft: "100%",
        animation: "tickerScroll 16s linear infinite",
        color: dark ? "rgba(255,255,255,0.65)" : "rgba(28,44,69,0.65)",
        fontSize: 12,
      }}>
        Live monitoring active&nbsp;&nbsp;•&nbsp;&nbsp;Secret enforcement armed&nbsp;&nbsp;•&nbsp;&nbsp;Merge protection online&nbsp;&nbsp;•&nbsp;&nbsp;Repo integrity checks running&nbsp;&nbsp;•&nbsp;&nbsp;
      </div>
    </div>
  );
}

// ─── StatusBadge ─────────────────────────────────────────────────────────────
function StatusBadge({ status, theme }: { status: string; theme: string }) {
  const dark = theme !== "light";

  type Entry = { label: string; darkColor: string; lightColor: string; variant: "blink" | "pulse" | "ping" };
  const map: Record<string, Entry> = {
    secure:     { label: "Secure",          darkColor: "#6EE7B7", lightColor: "#065f46", variant: "pulse" },
    monitoring: { label: "Monitoring",      darkColor: "#93C5FD", lightColor: "#1e40af", variant: "pulse" },
    warning:    { label: "Warning",         darkColor: "#FCD34D", lightColor: "#92400e", variant: "ping"  },
    breach:     { label: "Breach Detected", darkColor: "#FCA5A5", lightColor: "#991b1b", variant: "ping"  },
    correcting: { label: "Correcting",      darkColor: "#FCD34D", lightColor: "#92400e", variant: "pulse" },
    resolved:   { label: "Resolved",        darkColor: "#6EE7B7", lightColor: "#065f46", variant: "pulse" },
  };
  const item = map[status] || map.monitoring;
  const color = dark ? item.darkColor : item.lightColor;

  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "5px 10px", borderRadius: 999,
      background: dark ? "rgba(255,255,255,0.06)" : `${color}18`,
      border: `1px solid ${color}55`, color,
      fontSize: 12, whiteSpace: "nowrap", fontWeight: 600,
    }}>
      <LiveStatusDot color={color} variant={item.variant} />
      {item.label}
    </span>
  );
}

// ─── MetricCard ───────────────────────────────────────────────────────────────
function MetricCard({ title, value, subvalue, theme }: any) {
  const dark = theme === "dark";
  return (
    <div className="relative overflow-hidden rounded-2xl" style={{
      background: dark ? "rgba(17,17,17,0.72)" : "rgba(255,255,255,0.9)",
      border: dark ? "1px solid rgba(196,154,71,0.20)" : "1px solid rgba(28,44,69,0.12)",
      padding: "16px 18px",
      backdropFilter: "blur(12px)",
      WebkitBackdropFilter: "blur(12px)",
      boxShadow: dark
        ? "0 4px 20px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.04)"
        : "0 4px 20px rgba(28,44,69,0.08), inset 0 1px 0 rgba(255,255,255,0.80)",
    }}>
      <div className="pointer-events-none absolute inset-y-0 w-16 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-scan-sweep" />
      <div className="relative">
        <div style={{ fontSize: 11, color: dark ? "rgba(255,255,255,0.50)" : "rgba(28,44,69,0.50)",
          marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.07em", fontWeight: 600 }}>
          {title}
        </div>
        <div style={{ fontSize: 26, fontWeight: 700, color: "#C49A47", lineHeight: 1.1 }}>{value}</div>
        {subvalue && <div style={{ marginTop: 5, fontSize: 12, color: dark ? "rgba(255,255,255,0.50)" : "rgba(28,44,69,0.50)" }}>{subvalue}</div>}
      </div>
    </div>
  );
}

// ─── RepoRow ─────────────────────────────────────────────────────────────────
function RepoRow({ repo, theme, sourceLabel }: any) {
  const dark = theme === "dark";
  const isMobile = useIsMobile();
  const severityMap: Record<string, { label: string; color: string }> = {
    critical: { label: "Critical", color: "#FCA5A5" },
    warning:  { label: "Warning",  color: "#FCD34D" },
    minor:    { label: "Minor",    color: "#93C5FD" },
    none:     { label: "Secure",   color: "#6EE7B7" },
    secure:   { label: "Secure",   color: "#6EE7B7" },
  };
  const sev = severityMap[repo.severity] || severityMap.none;
  const label = repo.status === "resolved" ? "Resolved" : sev.label;

  const ComplianceBlock = () => (
    <div style={{ fontWeight: 700, fontSize: 13 }}>
      <span style={{ color: repo.before < 80 ? "#FCA5A5" : repo.before < 95 ? "#FCD34D" : "#93C5FD" }}>
        {repo.before}%
      </span>
      <span style={{ margin: "0 5px", color: dark ? "rgba(255,255,255,0.35)" : "rgba(28,44,69,0.30)" }}>→</span>
      <span style={{ color: "#6EE7B7" }}>{repo.after}%</span>
    </div>
  );

  const BadgeBlock = () => (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 7,
      padding: "5px 10px", borderRadius: 999,
      background: dark ? "rgba(255,255,255,0.06)" : "rgba(28,44,69,0.06)",
      border: `1px solid ${sev.color}55`, color: sev.color,
      fontSize: 12, fontWeight: 600, whiteSpace: "nowrap",
    }}>
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: sev.color,
        flexShrink: 0, boxShadow: `0 0 8px ${sev.color}88` }} />
      {label}
    </span>
  );

  return (
    <div style={{
      padding: "12px 14px",
      background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
      borderRadius: 14,
      border: dark ? "1px solid rgba(255,255,255,0.06)" : "1px solid rgba(28,44,69,0.08)",
      marginBottom: 10,
    }}>
      {/* Top row: name + (desktop: compliance + badge inline) */}
      <div style={{
        display: "grid",
        gridTemplateColumns: isMobile ? "1fr" : "1.5fr 1fr auto",
        gap: isMobile ? 0 : 12,
        alignItems: "center",
      }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 14 }}>
            <span style={{ color: "#C49A47" }}>{sourceLabel || repo.source}</span>
            {(sourceLabel || repo.source) ? " · " : ""}{repo.name}
          </div>
          <div style={{ color: dark ? "rgba(255,255,255,0.65)" : "rgba(28,44,69,0.65)", fontSize: 12, marginTop: 2 }}>
            {repo.issue}
          </div>
        </div>
        {!isMobile && <ComplianceBlock />}
        {!isMobile && (
          <div style={{ textAlign: "right" }}>
            <BadgeBlock />
          </div>
        )}
      </div>

      {/* Mobile second row: compliance left, badge right */}
      {isMobile && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
          marginTop: 10, paddingTop: 8,
          borderTop: dark ? "1px solid rgba(255,255,255,0.05)" : "1px solid rgba(28,44,69,0.07)" }}>
          <ComplianceBlock />
          <BadgeBlock />
        </div>
      )}
    </div>
  );
}

// ─── Panel wrapper ────────────────────────────────────────────────────────────
function Panel({ children }: { children: React.ReactNode }) {
  return <div style={{ animation: "fadeSlide 280ms ease" }}>{children}</div>;
}

// ─── SettingsModal ────────────────────────────────────────────────────────────
function SettingsModal({ open, onClose, settings, setSettings, theme, repos, onScan }: any) {
  if (!open) return null;
  const dark = theme === "dark";
  const cardBg = dark ? "rgba(18,18,18,0.98)" : "rgba(255,255,255,0.99)";
  const text = dark ? "#FFFFFF" : "#1C2C45";
  const sep = dark ? "rgba(255,255,255,0.08)" : "rgba(28,44,69,0.08)";

  const Row = ({ label, sublabel, children }: any) => (
    <div style={{ padding: "14px 0", borderBottom: `1px solid ${sep}` }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <span style={{ fontSize: 15 }}>{label}</span>
          {sublabel && <div style={{ fontSize: 11, color: dark ? "rgba(255,255,255,0.40)" : "rgba(28,44,69,0.45)", marginTop: 2 }}>{sublabel}</div>}
        </div>
        <div>{children}</div>
      </div>
    </div>
  );

  const Toggle = ({ value, onChange }: any) => (
    <button onClick={onChange} style={{
      background: value ? "#C49A47" : dark ? "rgba(255,255,255,0.12)" : "rgba(28,44,69,0.10)",
      color: value ? "#111" : text, border: "none", borderRadius: 999,
      padding: "8px 16px", cursor: "pointer", fontWeight: 700, fontSize: 14,
      minWidth: 60, minHeight: 38, fontFamily: "inherit",
    }}>
      {value ? "On" : "Off"}
    </button>
  );

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.52)",
      display: "grid", placeItems: "center", zIndex: 1000, padding: 16, overflowY: "auto" }}>
      <div style={{ width: "100%", maxWidth: 480, background: cardBg, color: text,
        borderRadius: 20, padding: "20px 24px", boxShadow: "0 28px 80px rgba(0,0,0,0.32)",
        margin: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>Settings</h2>
          <button onClick={onClose} style={{ border: "none",
            background: dark ? "rgba(255,255,255,0.08)" : "rgba(28,44,69,0.07)",
            color: text, fontSize: 18, cursor: "pointer", borderRadius: 8,
            width: 36, height: 36, display: "flex", alignItems: "center", justifyContent: "center" }}>✕</button>
        </div>

        <Row label="Sound effects">
          <Toggle value={settings.sound} onChange={() => setSettings((s: any) => ({ ...s, sound: !s.sound }))} />
        </Row>
        <Row label="Haptic feedback">
          <Toggle value={settings.haptics} onChange={() => setSettings((s: any) => ({ ...s, haptics: !s.haptics }))} />
        </Row>
        <Row label="Appearance">
          <div style={{ display: "flex", gap: 8 }}>
            {["Light", "Dark"].map(t => (
              <button key={t} onClick={() => setSettings((s: any) => ({ ...s, theme: t.toLowerCase() }))}
                style={{
                  border: "none", borderRadius: 10, padding: "8px 14px",
                  cursor: "pointer", fontWeight: 700, fontSize: 14, minHeight: 38, fontFamily: "inherit",
                  background: settings.theme === t.toLowerCase() ? "#C49A47" : dark ? "rgba(255,255,255,0.10)" : "rgba(28,44,69,0.08)",
                  color: settings.theme === t.toLowerCase() ? "#111" : text,
                }}>
                {t}
              </button>
            ))}
          </div>
        </Row>

        {/* Repository source picker */}
        <div style={{ padding: "14px 0" }}>
          <RepositorySourcePicker
            repos={(repos || []).map((r: any) => ({ id: r.name, name: r.name, status: r.status }))}
            selectedPlatforms={settings.repoTargets?.length ? settings.repoTargets : ["GitHub"]}
            selectedRepo={settings.selectedRepo || null}
            onPlatformChange={(platform: string) => setSettings((s: any) => {
              const current: string[] = s.repoTargets?.length ? s.repoTargets : ["GitHub"];
              const next = current.includes(platform)
                ? current.filter((p: string) => p !== platform)
                : [...current, platform];
              return { ...s, repoTargets: next.length > 0 ? next : ["GitHub"] };
            })}
            onRepoChange={(repo: RepoItem) => setSettings((s: any) => ({ ...s, selectedRepo: repo }))}
            onScan={() => { onScan?.(); onClose(); }}
          />
        </div>

        <button onClick={onClose} style={{
          marginTop: 8, width: "100%", background: "#C49A47", color: "#111",
          border: "none", borderRadius: 12, padding: "13px 0", fontWeight: 700,
          fontSize: 15, cursor: "pointer", fontFamily: "inherit",
        }}>Done</button>
      </div>
    </div>
  );
}

// ─── AuthScreen ───────────────────────────────────────────────────────────────
type BootPhase = "booting" | "verifying" | "secure" | "handoff" | "login";

const BOOT_LINES = [
  "Initializing secure execution layer...",
  "Validating runtime integrity...",
  "Verifying authorization chain...",
  "Loading protected interface...",
];

function AuthScreen({ sound, haptics, onAuthenticated }: any) {
  const [email, setEmail] = useState("demo@repoguard.ai");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"email" | "code">("email");
  const [demoCode, setDemoCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [bootPhase, setBootPhase] = useState<BootPhase>("booting");
  const [bootLineIdx, setBootLineIdx] = useState(0);

  // ── Boot state machine ──────────────────────────────────────────────────────
  useEffect(() => {
    let alive = true;
    const wait = (ms: number) => new Promise<void>(r => setTimeout(r, ms));

    (async () => {
      // booting → verifying
      await wait(500);
      if (!alive) return;
      setBootPhase("verifying");

      // Run API verify in background; guarantee at least 2200ms in verifying
      fetch("/api/repoguard/verify").catch(() => null);
      await wait(2200);
      if (!alive) return;
      setBootPhase("secure");

      // Show secure confirmation briefly
      await wait(1000);
      if (!alive) return;
      setBootPhase("handoff");

      // Handoff animation plays out
      await wait(650);
      if (!alive) return;
      setBootPhase("login");
    })();

    return () => { alive = false; };
  }, []);

  // ── Rotate boot messages while verifying ───────────────────────────────────
  useEffect(() => {
    if (bootPhase !== "verifying") return;
    const t = setInterval(() => setBootLineIdx(i => (i + 1) % BOOT_LINES.length), 1400);
    return () => clearInterval(t);
  }, [bootPhase]);

  // ── Auth logic (unchanged) ─────────────────────────────────────────────────
  const sendCode = async () => {
    if (!email.trim()) return;
    warmAudio();
    playClick(sound);
    haptic(haptics, 10);
    setLoading(true); setError("");
    try {
      const res = await fetch("/api/auth/request-code", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      setDemoCode(data.demo_code);
      setStep("code");
      playSwoosh(sound);
    } catch {
      setError("Connection error — is the backend running?");
    } finally { setLoading(false); }
  };

  const verifyCode = async () => {
    if (!code.trim()) return;
    playClick(sound);
    haptic(haptics, 10);
    setLoading(true); setError("");
    try {
      const res = await fetch("/api/auth/verify-code", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code }),
      });
      const data = await res.json();
      if (data.verified) {
        playSwoosh(sound);
        haptic(haptics, [10, 30, 10]);
        onAuthenticated(email);
      } else {
        setError("Incorrect code — check the code shown above.");
        haptic(haptics, [50, 50, 50]);
      }
    } catch {
      setError("Connection error — is the backend running?");
    } finally { setLoading(false); }
  };

  // ── Shared styles ──────────────────────────────────────────────────────────
  const BG = "linear-gradient(180deg, #040c14 0%, #030810 100%)";
  const sub = "rgba(255,255,255,0.45)";

  const inputStyle: React.CSSProperties = {
    width: "100%", padding: "13px 16px", borderRadius: 12,
    background: "rgba(255,255,255,0.05)", border: "1px solid rgba(30,144,255,0.22)",
    color: "#fff", fontSize: 15, outline: "none", boxSizing: "border-box",
    fontFamily: "inherit", transition: "border-color 0.2s",
  };

  const btnStyle: React.CSSProperties = {
    width: "100%", padding: "15px", borderRadius: 12,
    background: "linear-gradient(135deg, #C49A47 0%, #a87d2e 100%)",
    color: "#0a0a0a", border: "none", fontWeight: 800, fontSize: 15,
    cursor: loading ? "not-allowed" : "pointer",
    opacity: loading ? 0.7 : 1, fontFamily: "inherit",
    boxShadow: "0 4px 24px rgba(196,154,71,0.35)",
    letterSpacing: "0.02em",
  };

  // ── Ring dimensions (responsive) ──────────────────────────────────────────
  const RING = 220;
  const HALF = RING / 2;

  // ── RENDER ─────────────────────────────────────────────────────────────────
  const showBoot = bootPhase !== "login";
  const isHandoff = bootPhase === "handoff";
  const isSecure = bootPhase === "secure";
  const isVerifying = bootPhase === "verifying";

  return (
    <div style={{ fontFamily: "Inter, system-ui, sans-serif", minHeight: "100dvh", background: BG }}>

      {/* ── BOOT SCREEN ─────────────────────────────────────────────────── */}
      {showBoot && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 60,
          background: BG,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          overflow: "hidden",
          animation: isHandoff
            ? "rgBootOut 0.65s ease-in-out forwards"
            : "rgBootIn 0.6s ease-out",
        }}>

          {/* Ghost watermark */}
          <img src="/rg-ghost.jpeg" alt="" aria-hidden="true" style={{
            position: "absolute", inset: 0, width: "100%", height: "100%",
            objectFit: "cover", opacity: 0.04, filter: "blur(10px)",
            transform: "scale(1.1)", pointerEvents: "none",
          }} />

          {/* Ambient radial glow */}
          <div style={{
            position: "absolute",
            top: "38%", left: "50%",
            width: 480, height: 480,
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(30,144,255,0.20) 0%, rgba(30,144,255,0.07) 45%, transparent 70%)",
            pointerEvents: "none",
            animation: "rgAmbientGlow 4.5s ease-in-out infinite",
            transform: "translate(-50%, -50%)",
          }} />

          {/* Ring + emblem assembly */}
          <div style={{ position: "relative", width: RING, height: RING, marginBottom: 44, flexShrink: 0 }}>

            {/* Outer segmented ring — CW */}
            <svg
              viewBox={`0 0 ${RING} ${RING}`}
              width={RING} height={RING}
              style={{ position: "absolute", inset: 0, animation: "rgSpin 11s linear infinite" }}
            >
              <circle
                cx={HALF} cy={HALF} r={HALF - 4}
                fill="none" stroke="#1E90FF" strokeWidth="1.5"
                strokeDasharray="16 9" opacity="0.75"
              />
            </svg>

            {/* Mid segmented ring — CCW */}
            <svg
              viewBox={`0 0 ${RING} ${RING}`}
              width={RING} height={RING}
              style={{ position: "absolute", inset: 0, animation: "rgSpin 17s linear infinite reverse" }}
            >
              <circle
                cx={HALF} cy={HALF} r={HALF - 18}
                fill="none" stroke="#1E90FF" strokeWidth="1"
                strokeDasharray="7 14" opacity="0.45"
              />
            </svg>

            {/* Thin inner accent ring */}
            <div style={{
              position: "absolute", inset: 36,
              borderRadius: "50%",
              border: "1px solid rgba(30,144,255,0.22)",
            }} />

            {/* Ambient blue halo behind emblem */}
            <div style={{
              position: "absolute", inset: 42,
              borderRadius: "50%",
              background: "radial-gradient(circle, rgba(30,144,255,0.18) 0%, transparent 70%)",
            }} />

            {/* Center emblem circle */}
            <div style={{
              position: "absolute", inset: 44,
              borderRadius: "50%",
              background: "linear-gradient(145deg, #0b1828, #060e1c)",
              display: "flex", alignItems: "center", justifyContent: "center",
              animation: "rgCoreHalo 3.5s ease-in-out infinite",
            }}>
              <img
                src="/rg-core.jpeg"
                alt="REPOGUARD"
                style={{
                  width: "76%", height: "76%",
                  objectFit: "cover",
                  borderRadius: "50%",
                  opacity: isSecure ? 1 : 0.92,
                  filter: isSecure ? "brightness(1.15) drop-shadow(0 0 8px rgba(110,231,183,0.4))" : "none",
                  transition: "filter 0.8s, opacity 0.8s",
                }}
              />
            </div>

            {/* Orbital dots */}
            {[0, 90, 180, 270].map((deg, i) => (
              <div key={i} style={{
                position: "absolute", top: "50%", left: "50%",
                width: 7, height: 7, borderRadius: "50%",
                background: isSecure ? "#6EE7B7" : "#1E90FF",
                boxShadow: `0 0 8px ${isSecure ? "#6EE7B7" : "#1E90FF"}`,
                transform: `rotate(${deg}deg) translateX(${HALF - 6}px) translateY(-50%)`,
                opacity: 0.8,
                transition: "background 0.8s, box-shadow 0.8s",
              }} />
            ))}
          </div>

          {/* ── Text stack ──────────────────────────────────────────────── */}
          <div style={{
            textAlign: "center", position: "relative", zIndex: 1,
            padding: "0 24px", maxWidth: 340,
          }}>
            <div style={{
              fontSize: 30, fontWeight: 800, letterSpacing: "0.20em",
              color: "#C49A47",
              textShadow: "0 0 30px rgba(196,154,71,0.4)",
              marginBottom: 8,
            }}>REPOGUARD</div>

            <div style={{
              fontSize: 10, color: "rgba(30,144,255,0.75)", fontWeight: 700,
              letterSpacing: "0.26em", marginBottom: 14,
            }}>AION SECURITY CORE</div>

            <div style={{
              width: 40, height: 1,
              background: "linear-gradient(90deg, transparent, rgba(196,154,71,0.5), transparent)",
              margin: "0 auto 14px",
            }} />

            <div style={{
              fontSize: 9, color: "rgba(255,255,255,0.22)", letterSpacing: "0.18em",
              fontWeight: 600, marginBottom: 28,
            }}>
              MONITORING · VALIDATION · ENFORCEMENT · CONTROL
            </div>

            {/* Boot status line */}
            {isSecure ? (
              <div style={{
                fontSize: 12, color: "#6EE7B7", letterSpacing: "0.18em",
                fontWeight: 700, animation: "rgSecureConfirm 0.9s ease-out",
                textShadow: "0 0 14px rgba(110,231,183,0.5)",
              }}>
                AUTHORIZATION CONFIRMED
              </div>
            ) : (
              <div
                key={bootLineIdx}
                style={{
                  fontSize: 13, color: "rgba(255,255,255,0.7)",
                  letterSpacing: "0.03em", fontFamily: "monospace",
                  animation: "rgBootLineIn 0.4s ease-out",
                  minHeight: 20,
                }}
              >
                {BOOT_LINES[bootLineIdx]}
              </div>
            )}

            {/* Progress dots */}
            {isVerifying && (
              <div style={{ display: "flex", justifyContent: "center", gap: 7, marginTop: 18 }}>
                {[0, 1, 2].map(i => (
                  <div key={i} style={{
                    width: 5, height: 5, borderRadius: "50%",
                    background: "#1E90FF",
                    boxShadow: "0 0 8px rgba(30,144,255,0.7)",
                    animation: `rgDotBounce 1.5s ${i * 0.22}s ease-in-out infinite`,
                  }} />
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div style={{
            position: "absolute", bottom: 28,
            fontSize: 9, color: "rgba(255,255,255,0.18)",
            letterSpacing: "0.22em", fontWeight: 600, textAlign: "center",
          }}>
            NO EXECUTION WITHOUT AUTHORIZATION
          </div>
        </div>
      )}

      {/* ── AUTH FORM (mounts immediately, visible only after handoff) ───── */}
      <div style={{
        minHeight: "100dvh",
        display: bootPhase === "login" ? "flex" : "none",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "28px 20px",
        position: "relative",
        overflow: "hidden",
        animation: bootPhase === "login" ? "rgAuthSlideIn 0.7s ease-out" : "none",
      }}>

        {/* Ghost watermark */}
        <img src="/rg-ghost.jpeg" alt="" aria-hidden="true" style={{
          position: "absolute", inset: 0, width: "100%", height: "100%",
          objectFit: "cover", opacity: 0.05, filter: "blur(10px)",
          transform: "scale(1.1)", pointerEvents: "none",
        }} />

        {/* Ambient halo */}
        <div style={{
          position: "absolute", top: "20%", left: "50%",
          width: 360, height: 360, borderRadius: "50%",
          background: "radial-gradient(circle, rgba(30,144,255,0.10) 0%, transparent 65%)",
          transform: "translate(-50%, -50%)", pointerEvents: "none",
        }} />

        <div style={{
          position: "relative", zIndex: 1,
          width: "100%", maxWidth: 400,
          display: "flex", flexDirection: "column", alignItems: "center", gap: 24,
        }}>

          {/* REPOGUARD mini-badge */}
          <div style={{
            display: "flex", alignItems: "center", gap: 10,
            padding: "8px 18px",
            background: "rgba(30,144,255,0.08)",
            border: "1px solid rgba(30,144,255,0.20)",
            borderRadius: 100,
          }}>
            <img src="/rg-core.jpeg" alt="" style={{
              width: 24, height: 24, borderRadius: "50%", objectFit: "cover",
            }} />
            <span style={{
              fontSize: 11, fontWeight: 700, letterSpacing: "0.18em",
              color: "#C49A47",
            }}>REPOGUARD</span>
            <span style={{
              fontSize: 9, color: "#6EE7B7", fontWeight: 600,
              letterSpacing: "0.12em", marginLeft: 2,
            }}>● SECURE</span>
          </div>

          {/* Auth card */}
          <div style={{
            width: "100%",
            background: "rgba(8,16,28,0.88)",
            borderRadius: 20,
            padding: "28px 24px",
            border: "1px solid rgba(30,144,255,0.14)",
            boxShadow: "0 24px 64px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.04)",
            backdropFilter: "blur(12px)",
          }}>

            {/* Card header */}
            <div style={{ marginBottom: 26 }}>
              <div style={{
                fontSize: 22, fontWeight: 800, color: "#C49A47",
                letterSpacing: "0.04em", lineHeight: 1.1,
              }}>Sign in</div>
              <div style={{
                color: sub, marginTop: 5, fontSize: 13, letterSpacing: "0.01em",
              }}>Secure access · Email & 2FA</div>
            </div>

            {step === "email" ? (
              <div style={{ display: "grid", gap: 14 }}>
                <div>
                  <label style={{
                    display: "block", fontSize: 10, color: "rgba(255,255,255,0.35)",
                    marginBottom: 7, fontWeight: 700,
                    textTransform: "uppercase", letterSpacing: "0.10em",
                  }}>Email address</label>
                  <input
                    style={inputStyle} value={email}
                    onChange={e => setEmail(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && sendCode()}
                    type="email" autoComplete="email"
                  />
                </div>
                {error && (
                  <div style={{
                    color: "#FCA5A5", fontSize: 13, padding: "9px 12px",
                    background: "rgba(252,165,165,0.07)", borderRadius: 8,
                    border: "1px solid rgba(252,165,165,0.15)",
                  }}>{error}</div>
                )}
                <button style={btnStyle} onClick={sendCode} disabled={loading}>
                  {loading ? "Sending…" : "Send verification code"}
                </button>
                <div style={{
                  textAlign: "center", fontSize: 11, color: "rgba(255,255,255,0.25)",
                  letterSpacing: "0.02em",
                }}>
                  Demo code will appear instantly
                </div>
              </div>
            ) : (
              <div style={{ display: "grid", gap: 14 }}>
                <div style={{
                  background: "rgba(196,154,71,0.08)",
                  border: "1px solid rgba(196,154,71,0.28)",
                  borderRadius: 12, padding: "14px 16px",
                }}>
                  <div style={{
                    fontSize: 10, color: "#C49A47", fontWeight: 700,
                    textTransform: "uppercase", letterSpacing: "0.10em", marginBottom: 8,
                  }}>Demo verification code</div>
                  <div style={{
                    fontFamily: "monospace", fontSize: 30, fontWeight: 800,
                    color: "#C49A47", letterSpacing: "0.22em",
                    textShadow: "0 0 16px rgba(196,154,71,0.4)",
                  }}>{demoCode}</div>
                  <div style={{ fontSize: 11, color: sub, marginTop: 5 }}>Sent to {email}</div>
                </div>

                <div>
                  <label style={{
                    display: "block", fontSize: 10, color: "rgba(255,255,255,0.35)",
                    marginBottom: 7, fontWeight: 700,
                    textTransform: "uppercase", letterSpacing: "0.10em",
                  }}>Enter code</label>
                  <input
                    style={{ ...inputStyle, fontFamily: "monospace", fontSize: 24,
                      letterSpacing: "0.24em", textAlign: "center" }}
                    value={code}
                    onChange={e => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    onKeyDown={e => e.key === "Enter" && verifyCode()}
                    placeholder="000000" inputMode="numeric" maxLength={6} autoFocus
                  />
                </div>

                {error && (
                  <div style={{
                    color: "#FCA5A5", fontSize: 13, padding: "9px 12px",
                    background: "rgba(252,165,165,0.07)", borderRadius: 8,
                    border: "1px solid rgba(252,165,165,0.15)",
                  }}>{error}</div>
                )}

                <button style={btnStyle} onClick={verifyCode} disabled={loading}>
                  {loading ? "Verifying…" : "Verify and enter"}
                </button>

                <button
                  onClick={() => { setStep("email"); setCode(""); setError(""); }}
                  style={{
                    background: "transparent", border: "none",
                    color: "rgba(255,255,255,0.35)",
                    cursor: "pointer", fontSize: 13, padding: "2px 0",
                    fontFamily: "inherit", letterSpacing: "0.01em",
                  }}
                >
                  ← Use a different email
                </button>
              </div>
            )}
          </div>

          {/* Auth footer */}
          <div style={{
            fontSize: 9, color: "rgba(255,255,255,0.15)",
            letterSpacing: "0.18em", fontWeight: 600,
          }}>
            NO EXECUTION WITHOUT AUTHORIZATION
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState("Command");
  const [events, setEvents] = useState<any[]>([]);
  const [repos, setRepos] = useState<any[]>([]);
  const [score, setScore] = useState({ before: 72, after: 72 });
  const [status, setStatus] = useState("secure");
  const [animatingScore, setAnimatingScore] = useState(72);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [authenticatedUser, setAuthenticatedUser] = useState("");
  const [settings, setSettings] = useState<any>(() => {
    try {
      const saved = JSON.parse(localStorage.getItem("repoguard-settings") || "");
      const repoTargets = saved.repoTargets?.length
        ? saved.repoTargets
        : saved.repoTarget ? [saved.repoTarget] : ["GitHub"];
      return { sound: true, haptics: true, theme: "dark", ...saved, repoTargets };
    }
    catch { return { sound: true, haptics: true, theme: "dark", repoTargets: ["GitHub"] }; }
  });
  const lastEventCount = useRef(0);
  const activeIndex = useMemo(() => pages.indexOf(page), [page]);
  const theme = settings.theme;

  useEffect(() => {
    localStorage.setItem("repoguard-settings", JSON.stringify(settings));
  }, [settings]);

  async function refreshState() {
    const [evR, reR, scR, stR] = await Promise.all([
      fetch("/api/events"), fetch("/api/repos"),
      fetch("/api/compliance"), fetch("/api/system-status"),
    ]);
    setEvents(await evR.json());
    setRepos(await reR.json());
    setScore(await scR.json());
    setStatus((await stR.json()).status);
  }

  useEffect(() => {
    if (!authenticatedUser) return;
    refreshState();
    const id = setInterval(refreshState, 1200);
    return () => clearInterval(id);
  }, [authenticatedUser]);

  useEffect(() => {
    const target = score.after;
    let current = animatingScore;
    if (current === target) return;
    const step = current < target ? 1 : -1;
    const timer = setInterval(() => {
      current += step;
      setAnimatingScore(current);
      if (current === target) clearInterval(timer);
    }, 22);
    return () => clearInterval(timer);
  }, [score.after]);

  useEffect(() => {
    if (events.length > lastEventCount.current) {
      lastEventCount.current = events.length;
    }
  }, [events]);

  // Force 1-second re-renders so timeAgo labels stay fresh
  useEffect(() => {
    const tick = setInterval(() => setEvents((prev: any[]) => [...prev]), 1000);
    return () => clearInterval(tick);
  }, []);

  const triggerDemo = async () => {
    warmAudio();
    haptic(settings.haptics, 18);

    // Phase 1 — set breach in backend, jump to Breach page
    await fetch("/api/demo-trigger", { method: "POST" });
    await refreshState();
    setPage("Breach");
    playAlert(settings.sound);
    haptic(settings.haptics, [30, 20, 30, 20, 30]);

    // Phase 2 — Correction page after 4 s
    setTimeout(() => {
      setPage("Correction");
      playSwoosh(settings.sound);
      haptic(settings.haptics, 18);
    }, 4000);

    // Phase 3 — Resolve backend, jump to Resolution page after 8 s
    setTimeout(async () => {
      await fetch("/api/demo-resolve", { method: "POST" });
      await refreshState();
      setPage("Resolution");
      playTing(settings.sound);
      haptic(settings.haptics, [10, 30, 10]);
    }, 8000);
  };

  const goPage = (nextPage: string) => {
    setPage(nextPage);
    playSwoosh(settings.sound);
    haptic(settings.haptics, 10);
  };

  // ── Page-driven threat display — overrides backend status for non-Command pages ──
  const displayStatus =
    page === "Breach"     ? "breach"     :
    page === "Correction" ? "correcting" :
    page === "Resolution" ? "resolved"   :
    status; // Command page reads live backend status

  // ── Derived: filter repos by selected platform (must be before early return) ──
  const activePlatforms: string[] = settings.repoTargets?.length ? settings.repoTargets : ["GitHub"];
  const platformLabel = activePlatforms.length === 1
    ? activePlatforms[0]
    : `${activePlatforms.length} Sources`;
  const displayedRepos = useMemo(
    () => repos.filter((r: any) => activePlatforms.includes(r.source)),
    [repos, activePlatforms.join(",")]
  );

  if (!authenticatedUser) {
    return <AuthScreen theme={theme} sound={settings.sound} haptics={settings.haptics} onAuthenticated={setAuthenticatedUser} />;
  }

  const dark = theme === "dark";
  const shellBg = dark
    ? "linear-gradient(180deg,#1C2C45 0%,#142237 100%)"
    : "linear-gradient(180deg,#DDD0B8 0%,#C9BB9E 100%)";
  const shellText = dark ? "white" : "#1C2C45";
  const cardBg = dark ? "rgba(17,17,17,0.74)" : "rgba(255,255,255,0.92)";
  const cardBorder = dark ? "1px solid rgba(196,154,71,0.18)" : "1px solid rgba(28,44,69,0.10)";
  const subText = dark ? "rgba(255,255,255,0.58)" : "rgba(28,44,69,0.58)";

  // ── Page content ─────────────────────────────────────────────────────────
  const pageContent: Record<string, React.ReactNode> = {

    Command: (
      <Panel>
        {/* Hero block */}
        <div className="relative overflow-hidden" style={{ marginBottom: 20, padding: "22px 20px 24px",
          background: dark ? "rgba(17,17,17,0.74)" : "rgba(255,255,255,0.92)",
          border: cardBorder, borderRadius: 18,
          backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)",
          boxShadow: dark ? "0 8px 32px rgba(0,0,0,0.32)" : "0 8px 32px rgba(28,44,69,0.08)" }}>
          <div className="pointer-events-none absolute inset-y-0 w-32 bg-gradient-to-r from-transparent via-white/4 to-transparent animate-scan-sweep" />
          <div className="relative">
          <div style={{ fontSize: 13, color: "#C49A47", fontWeight: 700,
            textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
            Security Monitoring
          </div>
          <div style={{ fontSize: "clamp(20px, 4vw, 28px)", fontWeight: 800,
            lineHeight: 1.15, color: shellText, margin: "0 0 6px" }}>
            Your API keys are already leaking.
          </div>
          <div style={{ color: subText, marginTop: 4, marginBottom: 20, fontSize: 14, lineHeight: 1.6, maxWidth: 500 }}>
            RepoGuard blocks insecure code before it merges—automatically.
          </div>
          <button onClick={triggerDemo} style={{
            background: "#C49A47", color: "#111", border: "none",
            borderRadius: 12, padding: "14px 28px",
            fontWeight: 800, fontSize: 15, cursor: "pointer",
            boxShadow: "0 6px 24px rgba(196,154,71,0.35)",
            fontFamily: "inherit", letterSpacing: "0.01em",
          }}>
            Simulate Breach (10s demo)
          </button>
          </div>{/* end relative wrapper */}
        </div>

        {/* Metrics */}
        <div className="metrics-grid" style={{ marginBottom: 16 }}>
          <MetricCard title="System Status"
            value={status === "breach" ? "Active Breach" : status === "resolved" ? "Resolved" : "Monitoring"}
            subvalue="Autonomous enforcement online" theme={theme} />
          <MetricCard title="Compliance Score"
            value={`${animatingScore}%`}
            subvalue={`${score.before}% → ${score.after}%`} theme={theme} />
          <MetricCard title="Connected Sources"
            value={String(activePlatforms.length)}
            subvalue={`${platformLabel} · Actively monitored`} theme={theme} />
        </div>

        {/* Repo board — with scan-sweep */}
        <div className="relative overflow-hidden rounded-2xl" style={{ border: cardBorder, background: cardBg, padding: "16px" }}>
          <div className="pointer-events-none absolute inset-y-0 w-24 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-scan-sweep" />
          <div className="relative">
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
              <div style={{ color: "#C49A47", fontWeight: 700, fontSize: 15 }}>Repository Status</div>
              <span style={{
                fontSize: 11, fontWeight: 700, padding: "3px 9px", borderRadius: 999,
                background: "rgba(196,154,71,0.12)", color: "#C49A47",
                border: "1px solid rgba(196,154,71,0.25)", letterSpacing: "0.04em",
              }}>
                {platformLabel}
              </span>
            </div>
            {displayedRepos.length === 0
              ? <div style={{ padding: "18px 0", textAlign: "center", color: subText, fontSize: 13 }}>
                  No repositories connected for the selected sources.
                </div>
              : displayedRepos.map((repo: any) => <RepoRow key={repo.name} repo={repo} theme={theme} />)}
          </div>
        </div>
      </Panel>
    ),

    Breach: (
      <Panel>
        <div style={{ background: cardBg, border: "1px solid rgba(252,165,165,0.30)",
          borderRadius: 18, padding: "18px 16px", position: "relative", overflow: "hidden" }}>

          {/* Pulsing red glow behind card */}
          <div style={{ position: "absolute", inset: 0, borderRadius: 18, pointerEvents: "none",
            background: "radial-gradient(ellipse at 50% 40%, rgba(252,165,165,0.07) 0%, transparent 70%)",
            animation: "redPulse 1.8s ease-in-out infinite" }} />

          {/* Scan-sweep effect */}
          <div className="pointer-events-none absolute inset-y-0 w-24 bg-gradient-to-r from-transparent via-red-400/10 to-transparent animate-scan-sweep" />
          <div className="relative">
          {/* Header row */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start",
            marginBottom: 14, flexWrap: "wrap", gap: 8 }}>
            <div>
              <div style={{ fontSize: 11, color: "#FCA5A5", fontWeight: 700,
                textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 4 }}>
                Live key detected in commit diff
              </div>
              <h2 style={{ margin: 0, fontSize: 20, color: "#FCA5A5" }}>Detected Breach</h2>
            </div>
            <span style={{ background: "rgba(252,165,165,0.12)", border: "1px solid rgba(252,165,165,0.35)",
              color: "#FCA5A5", borderRadius: 8, padding: "5px 10px", fontSize: 12, fontWeight: 700,
              whiteSpace: "nowrap" }}>
              Severity: Critical
            </span>
          </div>

          {/* Severity label + exposed key with scan highlight */}
          <div style={{ color: "#FCA5A5", fontWeight: 700, marginBottom: 6, fontSize: 13 }}>
            Severity: CRITICAL
          </div>
          <div style={{ position: "relative", background: "rgba(252,165,165,0.07)",
            border: "1px solid rgba(252,165,165,0.28)", borderRadius: 12,
            padding: "14px 16px", overflow: "hidden", marginBottom: 14 }}>
            <div style={{ fontFamily: "monospace", fontSize: 13, lineHeight: 1.6, color: "#FCA5A5", position: "relative", zIndex: 1 }}>
              {`OPENAI_API_KEY = "sk-demo1234567890EXPOSED"`}
            </div>
            {/* Scan highlight */}
            <div style={{ position: "absolute", top: 0, left: 0, width: "45%", height: "100%",
              background: "linear-gradient(90deg, transparent, rgba(252,165,165,0.20), transparent)",
              animation: "scanPass 1.6s ease-in-out infinite", pointerEvents: "none" }} />
          </div>

          <div style={{ color: subText, fontSize: 14, lineHeight: 1.65, marginBottom: 16, position: "relative" }}>
            A sensitive secret was detected in a pull request diff. RepoGuard halted the merge, revoked the credential, and triggered automated remediation.
          </div>

          <div style={{ position: "relative" }}>
            {repos.map(repo => <RepoRow key={repo.name} repo={repo} theme={theme} />)}
          </div>
          </div>{/* end relative wrapper */}
        </div>
      </Panel>
    ),

    Correction: (
      <Panel>
        <div className="relative overflow-hidden" style={{ background: cardBg, border: cardBorder, borderRadius: 18, padding: "18px 16px",
          backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)",
          boxShadow: dark ? "0 8px 32px rgba(0,0,0,0.32)" : "0 8px 32px rgba(28,44,69,0.08)" }}>
          <div className="pointer-events-none absolute inset-y-0 w-24 bg-gradient-to-r from-transparent via-emerald-400/5 to-transparent animate-scan-sweep" />
          <div className="relative">
            {/* Header + badge */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start",
              marginBottom: 16, flexWrap: "wrap", gap: 8 }}>
              <h2 style={{ color: "#C49A47", margin: 0, fontSize: 20 }}>Automated Correction</h2>
              <span style={{ background: "rgba(110,231,183,0.10)", border: "1px solid rgba(110,231,183,0.30)",
                color: "#6EE7B7", borderRadius: 8, padding: "5px 10px", fontSize: 12, fontWeight: 700,
                whiteSpace: "nowrap" }}>
                PR Created · Merge Blocked
              </span>
            </div>

            {/* Animated diff */}
            <div style={{ borderRadius: 12, overflow: "hidden",
              border: "1px solid rgba(255,255,255,0.08)", marginBottom: 14 }}>
              {/* Removed line */}
              <div style={{ fontFamily: "monospace", fontSize: 13, lineHeight: 1.8,
                padding: "10px 16px", background: "rgba(252,165,165,0.10)",
                color: "#FCA5A5", animation: "fadeOutRed 400ms ease-out 200ms both",
                borderBottom: "1px solid rgba(252,165,165,0.12)" }}>
                {`- OPENAI_API_KEY = "sk-demo1234567890EXPOSED"`}
              </div>
              {/* Added line */}
              <div style={{ fontFamily: "monospace", fontSize: 13, lineHeight: 1.8,
                padding: "10px 16px", background: "rgba(110,231,183,0.08)",
                color: "#6EE7B7", animation: "slideInGreen 400ms ease-out 500ms both" }}>
                {`+ OPENAI_API_KEY = "[REVOKED — rotated via Secret Engine]"`}
              </div>
            </div>

            <div style={{ color: subText, fontSize: 14, lineHeight: 1.65 }}>
              Secrets moved to secure runtime. Direct access removed.
            </div>
          </div>
        </div>
      </Panel>
    ),

    Resolution: (
      <Panel>
        <div className="relative overflow-hidden" style={{ background: cardBg, border: cardBorder, borderRadius: 18, padding: "20px 18px",
          backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)",
          boxShadow: dark ? "0 8px 32px rgba(0,0,0,0.32)" : "0 8px 32px rgba(28,44,69,0.08)" }}>
          <div className="pointer-events-none absolute inset-y-0 w-24 bg-gradient-to-r from-transparent via-yellow-400/5 to-transparent animate-scan-sweep" />
          <div className="relative">
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
            <h2 style={{ color: "#C49A47", margin: 0, fontSize: 20 }}>Resolution</h2>
            <span style={{
              fontSize: 11, fontWeight: 700, padding: "3px 9px", borderRadius: 999,
              background: "rgba(196,154,71,0.12)", color: "#C49A47",
              border: "1px solid rgba(196,154,71,0.25)", letterSpacing: "0.04em",
            }}>
              {platformLabel}
            </span>
          </div>

          {/* Big stat */}
          <div style={{ textAlign: "center", padding: "20px 0 24px",
            borderBottom: dark ? "1px solid rgba(255,255,255,0.07)" : "1px solid rgba(28,44,69,0.08)",
            marginBottom: 20 }}>
            <div style={{ fontSize: 11, color: subText, fontWeight: 700,
              textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>
              Compliance Score
            </div>
            <div style={{ fontSize: "clamp(40px, 10vw, 64px)", fontWeight: 800,
              color: "#C49A47", lineHeight: 1, letterSpacing: "-0.02em" }}>
              {score.before}% → {animatingScore}%
            </div>
          </div>

          {/* 3 badges */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "center", marginBottom: 20, marginTop: 12 }}>
            {["Key Revoked", "Checks Passed", "Merge Unblocked"].map(t => (
              <span key={t} style={{
                padding: "6px 10px", borderRadius: 999,
                background: "rgba(110,231,183,0.12)",
                border: "1px solid rgba(110,231,183,0.35)",
                color: "#6EE7B7", fontSize: 12, fontWeight: 600,
                animation: "popIn 350ms ease both",
              }}>{t}</span>
            ))}
          </div>

          <div style={{ marginTop: 14, display: "grid", gap: 8 }}>
            {activePlatforms.map((platform: string) => {
              const platformRepos = repos.filter((r: any) => r.source === platform);
              return platformRepos.length > 0
                ? platformRepos.map((repo: any) => (
                    <div key={repo.id} style={{ fontSize: 14 }}>
                      <span style={{ color: "#C49A47", fontWeight: 700 }}>{repo.source}</span>
                      {" · "}
                      {repo.name}
                      {" — "}
                      <span style={{ color: "#6EE7B7", fontWeight: 700 }}>
                        {repo.before}% → {repo.after}%
                      </span>
                    </div>
                  ))
                : (
                    <div key={platform} style={{ fontSize: 14 }}>
                      <span style={{ color: "#C49A47", fontWeight: 700 }}>{platform}</span>
                      {" · "}
                      <span style={{ color: subText }}>All clear — no incidents</span>
                    </div>
                  );
            })}
          </div>
          </div>{/* end relative wrapper */}
        </div>
      </Panel>
    ),
  };

  return (
    <div style={{ minHeight: "100dvh", background: shellBg, color: shellText,
      fontFamily: "Inter, system-ui, sans-serif", padding: "0 0 48px", position: "relative" }}>

      {/* Ambient background orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden" style={{ zIndex: 0 }}>
        <div className="absolute -left-24 -top-24 h-80 w-80 rounded-full blur-3xl animate-drift-slow"
          style={{ background: "rgba(196,154,71,0.10)" }} />
        <div className="absolute -right-24 bottom-0 h-96 w-96 rounded-full blur-3xl animate-drift-reverse"
          style={{ background: "rgba(59,130,246,0.09)" }} />
        <div className="absolute left-1/3 top-1/4 h-64 w-64 rounded-full blur-3xl animate-drift-slower"
          style={{ background: "rgba(239,68,68,0.05)" }} />
      </div>

      <style>{`
        * { box-sizing: border-box; }

        @keyframes fadeSlide {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes redPulse {
          0%, 100% { opacity: 0.6; }
          50%       { opacity: 1; }
        }
        @keyframes scanPass {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(320%); }
        }
        @keyframes fadeOutRed {
          from { opacity: 1; }
          to   { opacity: 0.35; }
        }
        @keyframes slideInGreen {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes popIn {
          from { opacity: 0; transform: scale(0.88); }
          to   { opacity: 1; transform: scale(1); }
        }
        @keyframes eventPop {
          0%   { opacity: 0; transform: translateY(10px) scale(0.98); }
          100% { opacity: 1; transform: translateY(0px)  scale(1); }
        }
        @keyframes glowFade {
          0%   { box-shadow: 0 0 20px rgba(196,154,71,0.35); }
          100% { box-shadow: 0 0 0   rgba(196,154,71,0); }
        }
        @keyframes pulseDot {
          0%   { transform: scale(1);    opacity: 0.85; box-shadow: 0 0 0 0   rgba(110,231,183,0.45); }
          70%  { transform: scale(1.05); opacity: 1;    box-shadow: 0 0 0 10px rgba(110,231,183,0); }
          100% { transform: scale(1);    opacity: 0.85; box-shadow: 0 0 0 0   rgba(110,231,183,0); }
        }
        @keyframes statusBlink {
          0%, 100% { opacity: 0.7; transform: scale(1); }
          50%       { opacity: 1;   transform: scale(1.12); }
        }
        @keyframes tickerScroll {
          0%   { transform: translateX(0); }
          100% { transform: translateX(-100%); }
        }
        @keyframes driftOne {
          from { transform: translate(0, 0); }
          to   { transform: translate(40px, 20px); }
        }
        @keyframes driftTwo {
          from { transform: translate(0, 0); }
          to   { transform: translate(-30px, -20px); }
        }

        .rg-wrap {
          max-width: 1160px;
          margin: 0 auto;
          padding: 18px 16px 0;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
        }

        .main-grid {
          display: grid;
          grid-template-columns: 1fr 290px;
          gap: 16px;
          align-items: start;
        }

        .nav-row {
          display: flex;
          gap: 8px;
          margin-bottom: 18px;
          overflow-x: auto;
          -webkit-overflow-scrolling: touch;
          scrollbar-width: none;
          padding-bottom: 2px;
        }
        .nav-row::-webkit-scrollbar { display: none; }

        .nav-btn {
          background: ${dark ? "rgba(255,255,255,0.06)" : "rgba(28,44,69,0.07)"};
          border: 1px solid ${dark ? "rgba(255,255,255,0.09)" : "rgba(28,44,69,0.10)"};
          color: ${shellText};
          border-radius: 12px;
          padding: 10px 18px;
          cursor: pointer;
          transition: background 150ms ease;
          white-space: nowrap;
          flex-shrink: 0;
          font-size: 14px;
          font-weight: 600;
          font-family: inherit;
          min-height: 42px;
        }
        .nav-btn:hover { background: ${dark ? "rgba(255,255,255,0.10)" : "rgba(28,44,69,0.11)"}; }
        .nav-btn.active {
          background: #C49A47 !important;
          color: #111 !important;
          border-color: #C49A47 !important;
          box-shadow: 0 4px 16px rgba(196,154,71,0.28);
        }

        .rg-wrap { position: relative; z-index: 1; }

        @media (max-width: 820px) {
          .main-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 767px) {
          .cmd-ticker   { display: none; }
          .event-scroll { max-height: 340px; overflow-y: auto; }
          .live-pulse   { display: none; }
          .rg-wrap      { padding: 12px 12px 0; }
          .metrics-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
        }
        @media (max-width: 400px) {
          .metrics-grid { grid-template-columns: 1fr; }
        }
      `}</style>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)}
        settings={settings} setSettings={setSettings} theme={theme}
        repos={repos} onScan={triggerDemo} />

      <div className="rg-wrap">

        {/* App header — brand · threat · live scan | settings · status */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
          marginBottom: 18, gap: 12, flexWrap: "wrap" }}>

          {/* Left: shield core · title · threat badge · live pulse */}
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <RepoGuardCore
              status={
                displayStatus === "breach"     ? "breach"    :
                displayStatus === "correcting" ? "verifying" :
                displayStatus === "warning"    ? "verifying" :
                "secure"
              }
              size="sm"
              showLabel={false}
              showImage={false}
            />
            <div style={{ color: "#C49A47", fontSize: 20, fontWeight: 800, letterSpacing: "-0.01em" }}>
              RepoGuard
            </div>
            <ThreatBadge status={displayStatus} theme={theme} />
            <LivePulse theme={theme} />
          </div>

          {/* Right: settings + status badge */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
            <button onClick={() => { haptic(settings.haptics, 10); setSettingsOpen(true); }}
              style={{ background: cardBg, border: cardBorder, color: shellText,
                borderRadius: 10, padding: "8px 14px", cursor: "pointer",
                fontWeight: 600, fontSize: 13, minHeight: 40, fontFamily: "inherit" }}>
              ⚙ Settings
            </button>
            <StatusBadge status={status} theme={theme} />
          </div>
        </div>

        {/* Nav tabs */}
        <div className="nav-row">
          {pages.map((p, i) => (
            <button key={p} className={`nav-btn${activeIndex === i ? " active" : ""}`}
              onClick={() => goPage(p)}>
              {p}
            </button>
          ))}
        </div>

        {/* Main grid */}
        <div className="main-grid">
          <div>{pageContent[page]}</div>

          {/* War Room Feed */}
          <WarRoomFeed theme={theme} />
        </div>

      </div>
    </div>
  );
}

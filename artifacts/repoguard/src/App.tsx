import React, { useEffect, useMemo, useRef, useState } from "react";
import { RepositorySourcePicker, type RepoItem } from "./components/RepositorySourcePicker";

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

// ─── StatusBadge ─────────────────────────────────────────────────────────────
function StatusBadge({ status, theme }: { status: string; theme: string }) {
  const map: Record<string, { label: string; color: string }> = {
    secure:     { label: "Secure",          color: "#6EE7B7" },
    monitoring: { label: "Monitoring",      color: "#93C5FD" },
    warning:    { label: "Warning",         color: "#FCD34D" },
    breach:     { label: "Breach Detected", color: "#FCA5A5" },
    correcting: { label: "Correcting",      color: "#FCD34D" },
    resolved:   { label: "Resolved",        color: "#6EE7B7" },
  };
  const item = map[status] || map.monitoring;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "5px 10px", borderRadius: 999,
      background: theme === "dark" ? "rgba(255,255,255,0.06)" : "rgba(28,44,69,0.05)",
      border: `1px solid ${item.color}55`, color: item.color,
      fontSize: 12, whiteSpace: "nowrap", fontWeight: 600,
    }}>
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: item.color,
        flexShrink: 0, boxShadow: `0 0 8px ${item.color}99` }} />
      {item.label}
    </span>
  );
}

// ─── MetricCard ───────────────────────────────────────────────────────────────
function MetricCard({ title, value, subvalue, theme }: any) {
  const dark = theme === "dark";
  return (
    <div style={{
      background: dark ? "rgba(17,17,17,0.72)" : "rgba(255,255,255,0.9)",
      border: dark ? "1px solid rgba(196,154,71,0.20)" : "1px solid rgba(28,44,69,0.12)",
      borderRadius: 16, padding: "16px 18px",
    }}>
      <div style={{ fontSize: 11, color: dark ? "rgba(255,255,255,0.50)" : "rgba(28,44,69,0.50)",
        marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.07em", fontWeight: 600 }}>
        {title}
      </div>
      <div style={{ fontSize: 26, fontWeight: 700, color: "#C49A47", lineHeight: 1.1 }}>{value}</div>
      {subvalue && <div style={{ marginTop: 5, fontSize: 12, color: dark ? "rgba(255,255,255,0.50)" : "rgba(28,44,69,0.50)" }}>{subvalue}</div>}
    </div>
  );
}

// ─── RepoRow ─────────────────────────────────────────────────────────────────
function RepoRow({ repo, theme }: any) {
  const dark = theme === "dark";
  const severityMap: Record<string, { label: string; color: string }> = {
    critical: { label: "Critical", color: "#FCA5A5" },
    warning:  { label: "Warning",  color: "#FCD34D" },
    minor:    { label: "Minor",    color: "#93C5FD" },
    none:     { label: "Secure",   color: "#6EE7B7" },
    secure:   { label: "Secure",   color: "#6EE7B7" },
  };
  const sev = severityMap[repo.severity] || severityMap.none;
  return (
    <div style={{
      display: "grid", gridTemplateColumns: "1.5fr 1fr auto", gap: 12,
      padding: "14px 16px",
      background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
      borderRadius: 14, border: dark ? "1px solid rgba(255,255,255,0.06)" : "1px solid rgba(28,44,69,0.08)",
      marginBottom: 10,
    }}>
      <div>
        <div style={{ fontWeight: 700, fontSize: 14 }}>
          <span style={{ color: "#C49A47" }}>{repo.source}</span>
          {repo.source ? " · " : ""}{repo.name}
        </div>
        <div style={{ color: dark ? "rgba(255,255,255,0.72)" : "rgba(28,44,69,0.72)", fontSize: 12, marginTop: 3 }}>
          {repo.issue}
        </div>
      </div>
      <div style={{ alignSelf: "center", fontWeight: 600, fontSize: 13,
        color: dark ? "rgba(255,255,255,0.70)" : "rgba(28,44,69,0.70)" }}>
        {repo.before}% → {repo.after}%
      </div>
      <div style={{ textAlign: "right", alignSelf: "center" }}>
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 8,
          padding: "6px 12px", borderRadius: 999,
          background: dark ? "rgba(255,255,255,0.06)" : "rgba(28,44,69,0.06)",
          border: `1px solid ${sev.color}55`, color: sev.color,
          fontSize: 13, fontWeight: 600,
        }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: sev.color,
            flexShrink: 0, boxShadow: `0 0 10px ${sev.color}88` }} />
          {repo.status === "resolved" ? "Resolved" : sev.label}
        </span>
      </div>
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
            selectedPlatform={settings.repoTarget || "GitHub"}
            selectedRepo={settings.selectedRepo || null}
            onPlatformChange={(platform: string) => setSettings((s: any) => ({ ...s, repoTarget: platform }))}
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
function AuthScreen({ theme, sound, haptics, onAuthenticated }: any) {
  const [email, setEmail] = useState("demo@repoguard.ai");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"email" | "code">("email");
  const [demoCode, setDemoCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const dark = theme === "dark";
  const bg = dark ? "linear-gradient(180deg,#1C2C45 0%,#142237 100%)" : "linear-gradient(180deg,#F7F4EE 0%,#EBE3D6 100%)";
  const text = dark ? "#fff" : "#1C2C45";
  const cardBg = dark ? "rgba(10,10,10,0.82)" : "rgba(255,255,255,0.96)";
  const border = dark ? "rgba(255,255,255,0.10)" : "rgba(28,44,69,0.12)";
  const inputBg = dark ? "rgba(255,255,255,0.06)" : "rgba(28,44,69,0.04)";
  const sub = dark ? "rgba(255,255,255,0.50)" : "rgba(28,44,69,0.50)";

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

  const inputStyle: React.CSSProperties = {
    width: "100%", padding: "13px 14px", borderRadius: 12,
    background: inputBg, border: `1px solid ${border}`,
    color: text, fontSize: 15, outline: "none", boxSizing: "border-box",
    fontFamily: "inherit",
  };

  const btnStyle: React.CSSProperties = {
    width: "100%", padding: "14px", borderRadius: 12,
    background: "#C49A47", color: "#111",
    border: "none", fontWeight: 800, fontSize: 15,
    cursor: loading ? "not-allowed" : "pointer",
    opacity: loading ? 0.7 : 1, fontFamily: "inherit",
  };

  return (
    <div style={{ minHeight: "100dvh", background: bg, display: "grid",
      placeItems: "center", padding: "20px 16px",
      fontFamily: "Inter, system-ui, sans-serif" }}>
      <div style={{ width: "100%", maxWidth: 420, background: cardBg, color: text,
        borderRadius: 20, padding: "28px 24px",
        border: `1px solid ${border}`, boxShadow: "0 20px 60px rgba(0,0,0,0.22)" }}>

        <div style={{ marginBottom: 24 }}>
          <div style={{ color: "#C49A47", fontSize: 28, fontWeight: 800, lineHeight: 1.1 }}>RepoGuard</div>
          <div style={{ color: sub, marginTop: 5, fontSize: 14 }}>Secure sign in with email and 2FA.</div>
        </div>

        {step === "email" ? (
          <div style={{ display: "grid", gap: 14 }}>
            <div>
              <label style={{ display: "block", fontSize: 11, color: sub, marginBottom: 6,
                fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>Email</label>
              <input style={inputStyle} value={email}
                onChange={e => setEmail(e.target.value)}
                onKeyDown={e => e.key === "Enter" && sendCode()}
                type="email" autoComplete="email" />
            </div>
            {error && <div style={{ color: "#FCA5A5", fontSize: 13, padding: "8px 12px",
              background: "rgba(252,165,165,0.08)", borderRadius: 8 }}>{error}</div>}
            <button style={btnStyle} onClick={sendCode} disabled={loading}>
              {loading ? "Sending…" : "Send code"}
            </button>
            <div style={{ textAlign: "center", fontSize: 12, color: sub, marginTop: -4 }}>
              Use the code shown to enter instantly.
            </div>
          </div>
        ) : (
          <div style={{ display: "grid", gap: 14 }}>
            <div style={{ background: dark ? "rgba(196,154,71,0.10)" : "rgba(196,154,71,0.08)",
              border: "1px solid rgba(196,154,71,0.32)", borderRadius: 12, padding: "14px 16px" }}>
              <div style={{ fontSize: 11, color: "#C49A47", fontWeight: 700,
                textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 8 }}>
                Demo verification code
              </div>
              <div style={{ fontFamily: "monospace", fontSize: 30, fontWeight: 800,
                color: "#C49A47", letterSpacing: "0.18em" }}>
                {demoCode}
              </div>
              <div style={{ fontSize: 11, color: sub, marginTop: 4 }}>Sent to {email}</div>
            </div>

            <div>
              <label style={{ display: "block", fontSize: 11, color: sub, marginBottom: 6,
                fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>Enter code</label>
              <input style={{ ...inputStyle, fontFamily: "monospace", fontSize: 22,
                letterSpacing: "0.22em", textAlign: "center" }}
                value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                onKeyDown={e => e.key === "Enter" && verifyCode()}
                placeholder="000000" inputMode="numeric" maxLength={6} autoFocus />
            </div>
            {error && <div style={{ color: "#FCA5A5", fontSize: 13, padding: "8px 12px",
              background: "rgba(252,165,165,0.08)", borderRadius: 8 }}>{error}</div>}
            <button style={btnStyle} onClick={verifyCode} disabled={loading}>
              {loading ? "Verifying…" : "Verify and enter"}
            </button>
            <button onClick={() => { setStep("email"); setCode(""); setError(""); }}
              style={{ background: "transparent", border: "none", color: sub,
                cursor: "pointer", fontSize: 13, padding: "2px 0", fontFamily: "inherit" }}>
              ← Use a different email
            </button>
          </div>
        )}
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
      return { sound: true, haptics: true, theme: "dark", repoTarget: "GitHub", ...saved };
    }
    catch { return { sound: true, haptics: true, theme: "dark", repoTarget: "GitHub" }; }
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
      playPop(settings.sound);
      haptic(settings.haptics, [10, 20, 10]);
      lastEventCount.current = events.length;
    }
  }, [events, settings.sound, settings.haptics]);

  const triggerDemo = async () => {
    warmAudio();
    playClick(settings.sound);
    haptic(settings.haptics, 18);

    await fetch("/api/demo-trigger", { method: "POST" });
    playSwoosh(settings.sound);
    refreshState();

    setPage("Breach");
    playAlert(settings.sound);
    haptic(settings.haptics, [30, 20, 30, 20, 30]);

    setTimeout(() => {
      setPage("Correction");
      playSwoosh(settings.sound);
      haptic(settings.haptics, 18);
    }, 800);

    setTimeout(() => {
      setPage("Resolution");
      playTing(settings.sound);
      haptic(settings.haptics, [10, 30, 10]);
    }, 1600);
  };

  const goPage = (nextPage: string) => {
    setPage(nextPage);
    playSwoosh(settings.sound);
    haptic(settings.haptics, 10);
  };

  if (!authenticatedUser) {
    return <AuthScreen theme={theme} sound={settings.sound} haptics={settings.haptics} onAuthenticated={setAuthenticatedUser} />;
  }

  const dark = theme === "dark";
  const shellBg = dark
    ? "linear-gradient(180deg,#1C2C45 0%,#142237 100%)"
    : "linear-gradient(180deg,#F7F4EE 0%,#EBE3D6 100%)";
  const shellText = dark ? "white" : "#1C2C45";
  const cardBg = dark ? "rgba(17,17,17,0.74)" : "rgba(255,255,255,0.92)";
  const cardBorder = dark ? "1px solid rgba(196,154,71,0.18)" : "1px solid rgba(28,44,69,0.10)";
  const subText = dark ? "rgba(255,255,255,0.58)" : "rgba(28,44,69,0.58)";

  // ── Page content ─────────────────────────────────────────────────────────
  const pageContent: Record<string, React.ReactNode> = {

    Command: (
      <Panel>
        {/* Hero block */}
        <div style={{ marginBottom: 20, padding: "22px 20px 24px",
          background: dark ? "rgba(17,17,17,0.74)" : "rgba(255,255,255,0.92)",
          border: cardBorder, borderRadius: 18 }}>
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
            value={String(new Set(repos.map((r: any) => r.source).filter(Boolean)).size)}
            subvalue="Actively monitored" theme={theme} />
        </div>

        {/* Repo board */}
        <div style={{ background: cardBg, border: cardBorder, borderRadius: 18, padding: "16px" }}>
          <div style={{ color: "#C49A47", fontWeight: 700, fontSize: 15, marginBottom: 12 }}>
            Repository Status
          </div>
          {repos.map(repo => <RepoRow key={repo.name} repo={repo} theme={theme} />)}
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

          {/* Header row */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start",
            marginBottom: 14, flexWrap: "wrap", gap: 8, position: "relative" }}>
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
        </div>
      </Panel>
    ),

    Correction: (
      <Panel>
        <div style={{ background: cardBg, border: cardBorder, borderRadius: 18, padding: "18px 16px" }}>
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
      </Panel>
    ),

    Resolution: (
      <Panel>
        <div style={{ background: cardBg, border: cardBorder, borderRadius: 18, padding: "20px 18px" }}>
          <h2 style={{ color: "#C49A47", margin: "0 0 20px", fontSize: 20 }}>Resolution</h2>

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
            {repos.map((repo: any) => (
              <div key={repo.id} style={{ fontSize: 14 }}>
                <span style={{ color: "#C49A47", fontWeight: 700 }}>{repo.source}</span>
                {" · "}
                {repo.name}
                {" — "}
                <span style={{ color: "#6EE7B7", fontWeight: 700 }}>
                  {repo.before}% → {repo.after}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </Panel>
    ),
  };

  return (
    <div style={{ minHeight: "100dvh", background: shellBg, color: shellText,
      fontFamily: "Inter, system-ui, sans-serif", padding: "0 0 48px" }}>

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

        @media (max-width: 820px) {
          .main-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 640px) {
          .rg-wrap { padding: 12px 12px 0; }
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

        {/* App header — brand + controls */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
          marginBottom: 16, gap: 12 }}>
          <div style={{ color: "#C49A47", fontSize: 20, fontWeight: 800, letterSpacing: "-0.01em" }}>
            RepoGuard
          </div>
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

          {/* Live Event Feed */}
          <div style={{ background: cardBg, border: cardBorder, borderRadius: 18,
            padding: "16px", height: "fit-content" }}>
            <div style={{ color: "#C49A47", fontWeight: 700, fontSize: 14, marginBottom: 12 }}>
              Live Event Feed
            </div>
            <div style={{ display: "grid", gap: 8 }}>
              {events.map((ev, i) => (
                <div key={`${ev.message}-${i}`} style={{
                  background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
                  border: dark ? "1px solid rgba(255,255,255,0.05)" : "1px solid rgba(28,44,69,0.07)",
                  borderRadius: 10, padding: "10px 12px",
                  animation: "fadeSlide 220ms ease",
                }}>
                  <div style={{ fontSize: 13, lineHeight: 1.4 }}>{ev.message}</div>
                  <div style={{ marginTop: 3, fontSize: 11, color: subText }}>{ev.time}</div>
                </div>
              ))}
              {events.length === 0 && (
                <div style={{ color: subText, fontSize: 13 }}>No active events.</div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

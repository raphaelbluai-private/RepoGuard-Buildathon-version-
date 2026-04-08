import React, { useEffect, useMemo, useRef, useState } from "react";

const pages = ["Command", "Breach", "Correction", "Resolution"];

function haptic(enabled, pattern: any = 10) {
  if (!enabled) return;
  if (typeof navigator !== "undefined" && navigator.vibrate) {
    navigator.vibrate(pattern);
  }
}

function playSwoosh(enabled) {
  if (!enabled) return;
  const AudioCtx = (window as any).AudioContext || (window as any).webkitAudioContext;
  if (!AudioCtx) return;
  const ctx = new AudioCtx();
  const now = ctx.currentTime;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  const filter = ctx.createBiquadFilter();
  osc.type = "triangle";
  osc.frequency.setValueAtTime(520, now);
  osc.frequency.exponentialRampToValueAtTime(260, now + 0.18);
  filter.type = "lowpass";
  filter.frequency.setValueAtTime(1200, now);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.04, now + 0.03);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.2);
  osc.connect(filter);
  filter.connect(gain);
  gain.connect(ctx.destination);
  osc.start(now);
  osc.stop(now + 0.22);
  setTimeout(() => ctx.close(), 350);
}

function playPop(enabled) {
  if (!enabled) return;
  const AudioCtx = (window as any).AudioContext || (window as any).webkitAudioContext;
  if (!AudioCtx) return;
  const ctx = new AudioCtx();
  const now = ctx.currentTime;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = "sine";
  osc.frequency.setValueAtTime(640, now);
  osc.frequency.exponentialRampToValueAtTime(880, now + 0.08);
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.05, now + 0.015);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.12);
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start(now);
  osc.stop(now + 0.14);
  setTimeout(() => ctx.close(), 300);
}

function StatusBadge({ status, theme }) {
  const map: Record<string, { label: string; color: string }> = {
    secure:     { label: "Secure",           color: "#6EE7B7" },
    monitoring: { label: "Monitoring",       color: "#93C5FD" },
    breach:     { label: "Breach Detected",  color: "#FCA5A5" },
    correcting: { label: "Correcting",       color: "#FCD34D" },
    resolved:   { label: "Resolved",         color: "#6EE7B7" },
  };
  const item = map[status] || map.monitoring;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "6px 10px", borderRadius: 999,
      background: theme === "dark" ? "rgba(255,255,255,0.06)" : "rgba(28,44,69,0.06)",
      border: `1px solid ${item.color}55`, color: item.color, fontSize: 12, whiteSpace: "nowrap",
    }}>
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: item.color, flexShrink: 0,
        boxShadow: `0 0 8px ${item.color}88` }} />
      {item.label}
    </span>
  );
}

function MetricCard({ title, value, subvalue, theme }) {
  const dark = theme === "dark";
  return (
    <div style={{
      background: dark ? "rgba(17,17,17,0.72)" : "rgba(255,255,255,0.9)",
      border: dark ? "1px solid rgba(196,154,71,0.20)" : "1px solid rgba(28,44,69,0.12)",
      borderRadius: 16, padding: "16px 18px",
      boxShadow: "0 4px 20px rgba(0,0,0,0.10)",
    }}>
      <div style={{ fontSize: 12, color: dark ? "rgba(255,255,255,0.55)" : "rgba(28,44,69,0.55)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.06em" }}>
        {title}
      </div>
      <div style={{ fontSize: 26, fontWeight: 700, color: "#C49A47", lineHeight: 1.1 }}>{value}</div>
      {subvalue && (
        <div style={{ marginTop: 5, fontSize: 12, color: dark ? "rgba(255,255,255,0.55)" : "rgba(28,44,69,0.55)" }}>{subvalue}</div>
      )}
    </div>
  );
}

function RepoRow({ repo, theme }) {
  const dark = theme === "dark";
  return (
    <div className="repo-row" style={{
      background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
      borderRadius: 12,
      border: dark ? "1px solid rgba(255,255,255,0.06)" : "1px solid rgba(28,44,69,0.08)",
      marginBottom: 8, padding: "12px 14px",
    }}>
      <div style={{ fontWeight: 600, fontSize: 14 }}>{repo.name}</div>
      <div style={{ color: dark ? "rgba(255,255,255,0.65)" : "rgba(28,44,69,0.65)", fontSize: 13, marginTop: 2 }}>{repo.issue}</div>
      <div style={{ marginTop: 6 }}>
        <StatusBadge status={repo.status} theme={theme} />
      </div>
    </div>
  );
}

function Panel({ children }) {
  return <div style={{ animation: "fadeSlide 280ms ease" }}>{children}</div>;
}

function SettingsModal({ open, onClose, settings, setSettings, theme }) {
  if (!open) return null;
  const dark = theme === "dark";
  const cardBg = dark ? "rgba(22,22,22,0.98)" : "rgba(255,255,255,0.99)";
  const text = dark ? "#FFFFFF" : "#1C2C45";
  const borderColor = dark ? "rgba(255,255,255,0.08)" : "rgba(28,44,69,0.08)";

  const Row = ({ label, children }) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "14px 0", borderBottom: `1px solid ${borderColor}` }}>
      <span style={{ fontSize: 15 }}>{label}</span>
      <div>{children}</div>
    </div>
  );

  const Toggle = ({ value, onChange }) => (
    <button onClick={onChange} style={{
      background: value ? "#C49A47" : dark ? "rgba(255,255,255,0.12)" : "rgba(28,44,69,0.10)",
      color: value ? "#111111" : text, border: "none", borderRadius: 999,
      padding: "8px 16px", cursor: "pointer", fontWeight: 700, fontSize: 14,
      minWidth: 60, minHeight: 38,
    }}>
      {value ? "On" : "Off"}
    </button>
  );

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
      display: "grid", placeItems: "center", zIndex: 1000, padding: 16 }}>
      <div style={{ width: "100%", maxWidth: 480, background: cardBg, color: text,
        borderRadius: 20, padding: "20px 24px", boxShadow: "0 28px 80px rgba(0,0,0,0.30)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>Settings</h2>
          <button onClick={onClose} style={{ border: "none", background: dark ? "rgba(255,255,255,0.08)" : "rgba(28,44,69,0.08)",
            color: text, fontSize: 18, cursor: "pointer", borderRadius: 8, width: 36, height: 36,
            display: "flex", alignItems: "center", justifyContent: "center" }}>✕</button>
        </div>
        <Row label="Sound effects"><Toggle value={settings.sound} onChange={() => setSettings(s => ({ ...s, sound: !s.sound }))} /></Row>
        <Row label="Haptic feedback"><Toggle value={settings.haptics} onChange={() => setSettings(s => ({ ...s, haptics: !s.haptics }))} /></Row>
        <Row label="Appearance">
          <div style={{ display: "flex", gap: 8 }}>
            {["Light", "Dark"].map(t => (
              <button key={t} onClick={() => setSettings(s => ({ ...s, theme: t.toLowerCase() }))}
                style={{
                  border: "none", borderRadius: 10, padding: "8px 14px", cursor: "pointer",
                  fontWeight: 700, fontSize: 14, minHeight: 38,
                  background: settings.theme === t.toLowerCase() ? "#C49A47" : dark ? "rgba(255,255,255,0.10)" : "rgba(28,44,69,0.08)",
                  color: settings.theme === t.toLowerCase() ? "#111111" : text,
                }}>
                {t}
              </button>
            ))}
          </div>
        </Row>
        <button onClick={onClose} style={{
          marginTop: 20, width: "100%", background: "#C49A47", color: "#111111",
          border: "none", borderRadius: 12, padding: "13px 0", fontWeight: 700,
          fontSize: 15, cursor: "pointer",
        }}>Done</button>
      </div>
    </div>
  );
}

function AuthScreen({ theme, sound, haptics, onAuthenticated }) {
  const [email, setEmail] = useState("demo@repoguard.ai");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"email" | "code">("email");
  const [demoCode, setDemoCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const dark = theme === "dark";
  const bg = dark ? "linear-gradient(180deg,#1C2C45 0%,#142237 100%)" : "linear-gradient(180deg,#F7F4EE 0%,#EBE3D6 100%)";
  const text = dark ? "#ffffff" : "#1C2C45";
  const cardBg = dark ? "rgba(10,10,10,0.80)" : "rgba(255,255,255,0.95)";
  const borderColor = dark ? "rgba(255,255,255,0.10)" : "rgba(28,44,69,0.12)";
  const inputBg = dark ? "rgba(255,255,255,0.06)" : "rgba(28,44,69,0.04)";
  const subText = dark ? "rgba(255,255,255,0.55)" : "rgba(28,44,69,0.55)";

  const sendCode = async () => {
    if (!email.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/auth/request-code", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      setDemoCode(data.demo_code);
      setStep("code");
      playSwoosh(sound);
      haptic(haptics, 10);
    } catch {
      setError("Connection error. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const verifyCode = async () => {
    if (!code.trim()) return;
    setLoading(true);
    setError("");
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
      setError("Connection error. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: "100%", padding: "13px 14px", borderRadius: 12,
    background: inputBg, border: `1px solid ${borderColor}`,
    color: text, fontSize: 15, outline: "none", boxSizing: "border-box" as const,
    fontFamily: "inherit",
  };

  const btnStyle = {
    width: "100%", padding: "14px", borderRadius: 12,
    background: "#C49A47", color: "#111111",
    border: "none", fontWeight: 800, fontSize: 15, cursor: "pointer",
    opacity: loading ? 0.7 : 1,
  };

  return (
    <div style={{ minHeight: "100dvh", background: bg, display: "grid", placeItems: "center",
      padding: "20px 16px", fontFamily: "Inter, system-ui, sans-serif" }}>
      <div style={{ width: "100%", maxWidth: 420, background: cardBg, color: text,
        borderRadius: 20, padding: "28px 24px",
        border: `1px solid ${borderColor}`, boxShadow: "0 20px 60px rgba(0,0,0,0.20)" }}>

        <div style={{ marginBottom: 24 }}>
          <div style={{ color: "#C49A47", fontSize: 28, fontWeight: 800, lineHeight: 1.1 }}>RepoGuard</div>
          <div style={{ color: subText, marginTop: 5, fontSize: 14 }}>Secure sign in with email and 2FA.</div>
        </div>

        {step === "email" ? (
          <div style={{ display: "grid", gap: 14 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, color: subText, marginBottom: 6, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>Email</label>
              <input
                style={inputStyle}
                value={email}
                onChange={e => setEmail(e.target.value)}
                onKeyDown={e => e.key === "Enter" && sendCode()}
                type="email"
                autoComplete="email"
              />
            </div>
            {error && <div style={{ color: "#FCA5A5", fontSize: 13, padding: "8px 12px", background: "rgba(252,165,165,0.08)", borderRadius: 8 }}>{error}</div>}
            <button style={btnStyle} onClick={sendCode} disabled={loading}>
              {loading ? "Sending…" : "Send code"}
            </button>
          </div>
        ) : (
          <div style={{ display: "grid", gap: 14 }}>
            <div style={{ background: dark ? "rgba(196,154,71,0.10)" : "rgba(196,154,71,0.08)",
              border: "1px solid rgba(196,154,71,0.30)", borderRadius: 12, padding: "12px 14px" }}>
              <div style={{ fontSize: 12, color: "#C49A47", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>
                Demo verification code
              </div>
              <div style={{ fontFamily: "monospace", fontSize: 28, fontWeight: 800, color: "#C49A47", letterSpacing: "0.15em" }}>
                {demoCode}
              </div>
              <div style={{ fontSize: 12, color: subText, marginTop: 4 }}>
                Sent to {email}
              </div>
            </div>

            <div>
              <label style={{ display: "block", fontSize: 12, color: subText, marginBottom: 6, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>Enter code</label>
              <input
                style={{ ...inputStyle, fontFamily: "monospace", fontSize: 20, letterSpacing: "0.2em", textAlign: "center" }}
                value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                onKeyDown={e => e.key === "Enter" && verifyCode()}
                placeholder="000000"
                inputMode="numeric"
                maxLength={6}
                autoFocus
              />
            </div>
            {error && <div style={{ color: "#FCA5A5", fontSize: 13, padding: "8px 12px", background: "rgba(252,165,165,0.08)", borderRadius: 8 }}>{error}</div>}
            <button style={btnStyle} onClick={verifyCode} disabled={loading}>
              {loading ? "Verifying…" : "Verify and enter"}
            </button>
            <button onClick={() => { setStep("email"); setCode(""); setError(""); }}
              style={{ background: "transparent", border: "none", color: subText, cursor: "pointer", fontSize: 14, padding: "4px 0" }}>
              ← Use a different email
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState("Command");
  const [events, setEvents] = useState<any[]>([]);
  const [repos, setRepos] = useState<any[]>([]);
  const [score, setScore] = useState({ before: 72, after: 72 });
  const [status, setStatus] = useState("monitoring");
  const [animatingScore, setAnimatingScore] = useState(72);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [authenticatedUser, setAuthenticatedUser] = useState("");
  const [settings, setSettings] = useState(() => {
    try { return JSON.parse(localStorage.getItem("repoguard-settings") || ""); }
    catch { return { sound: true, haptics: true, theme: "dark" }; }
  });
  const lastEventCount = useRef(0);
  const activeIndex = useMemo(() => pages.indexOf(page), [page]);
  const theme = settings.theme;

  useEffect(() => {
    localStorage.setItem("repoguard-settings", JSON.stringify(settings));
  }, [settings]);

  async function refreshState() {
    const [eventsRes, reposRes, scoreRes, statusRes] = await Promise.all([
      fetch("/api/events"), fetch("/api/repos"),
      fetch("/api/compliance"), fetch("/api/system-status"),
    ]);
    setEvents(await eventsRes.json());
    setRepos(await reposRes.json());
    setScore(await scoreRes.json());
    setStatus((await statusRes.json()).status);
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
    }, 28);
    return () => clearInterval(timer);
  }, [score.after]);

  useEffect(() => {
    if (events.length > lastEventCount.current) {
      playPop(settings.sound);
      haptic(settings.haptics, [10, 30, 10]);
      lastEventCount.current = events.length;
    }
  }, [events, settings.sound, settings.haptics]);

  const triggerDemo = async () => {
    haptic(settings.haptics, 18);
    setPage("Command");
    await fetch("/api/demo-trigger", { method: "POST" });
    playSwoosh(settings.sound);
    await refreshState();
    setTimeout(() => { setPage("Breach");     playSwoosh(settings.sound); haptic(settings.haptics, 18); }, 800);
    setTimeout(() => { setPage("Correction"); playSwoosh(settings.sound); haptic(settings.haptics, 18); }, 2800);
    setTimeout(() => { setPage("Resolution"); playSwoosh(settings.sound); haptic(settings.haptics, 18); }, 5200);
  };

  const goPage = (nextPage) => {
    setPage(nextPage);
    playSwoosh(settings.sound);
    haptic(settings.haptics, 10);
  };

  if (!authenticatedUser) {
    return <AuthScreen theme={theme} sound={settings.sound} haptics={settings.haptics} onAuthenticated={setAuthenticatedUser} />;
  }

  const dark = theme === "dark";
  const shellBg = dark ? "linear-gradient(180deg,#1C2C45 0%,#142237 100%)" : "linear-gradient(180deg,#F7F4EE 0%,#EBE3D6 100%)";
  const shellText = dark ? "white" : "#1C2C45";
  const cardBg = dark ? "rgba(17,17,17,0.72)" : "rgba(255,255,255,0.90)";
  const cardBorder = dark ? "1px solid rgba(196,154,71,0.18)" : "1px solid rgba(28,44,69,0.10)";
  const subText = dark ? "rgba(255,255,255,0.60)" : "rgba(28,44,69,0.60)";

  const pageContent = {
    Command: (
      <Panel>
        <div className="metrics-grid">
          <MetricCard title="System Status" value={status === "breach" ? "Active Breach" : status === "resolved" ? "Resolved" : "Monitoring"} subvalue="Autonomous enforcement online" theme={theme} />
          <MetricCard title="Compliance Score" value={`${animatingScore}%`} subvalue={`${score.before}% → ${score.after}%`} theme={theme} />
          <MetricCard title="Repositories" value={String(repos.length)} subvalue="Live monitored" theme={theme} />
        </div>

        <div style={{ marginTop: 18, background: cardBg, border: cardBorder, borderRadius: 18, padding: "18px 16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 10 }}>
            <h2 style={{ color: "#C49A47", margin: 0, fontSize: 17 }}>Repository Status</h2>
            <button onClick={triggerDemo} style={{
              background: "#C49A47", color: "#111111", border: "none",
              borderRadius: 10, padding: "10px 16px", fontWeight: 700,
              cursor: "pointer", fontSize: 14, whiteSpace: "nowrap",
            }}>
              Run Demo
            </button>
          </div>
          {repos.map(repo => <RepoRow key={repo.name} repo={repo} theme={theme} />)}
        </div>
      </Panel>
    ),

    Breach: (
      <Panel>
        <div style={{ background: cardBg, border: cardBorder, borderRadius: 18, padding: "18px 16px" }}>
          <h2 style={{ color: "#C49A47", margin: "0 0 12px" }}>Detected Breach</h2>
          <div style={{ background: dark ? "rgba(252,165,165,0.08)" : "rgba(252,165,165,0.10)",
            border: "1px solid rgba(252,165,165,0.30)", borderRadius: 12, padding: "14px 16px",
            fontFamily: "monospace", fontSize: 13, lineHeight: 1.6, color: "#FCA5A5", overflowX: "auto" }}>
            {`OPENAI_API_KEY = "sk-demo1234567890EXPOSED"`}
          </div>
          <div style={{ marginTop: 14, color: subText, fontSize: 14, lineHeight: 1.6 }}>
            A sensitive secret was detected in a pull request diff. RepoGuard halted the merge, revoked the credential, and triggered automated remediation.
          </div>
          <div style={{ marginTop: 16 }}>
            {repos.map(repo => <RepoRow key={repo.name} repo={repo} theme={theme} />)}
          </div>
        </div>
      </Panel>
    ),

    Correction: (
      <Panel>
        <div style={{ background: cardBg, border: cardBorder, borderRadius: 18, padding: "18px 16px" }}>
          <h2 style={{ color: "#C49A47", margin: "0 0 12px" }}>Automated Correction</h2>
          <div style={{ background: dark ? "rgba(252,211,77,0.06)" : "rgba(252,211,77,0.08)",
            border: "1px solid rgba(252,211,77,0.25)", borderRadius: 12, padding: "14px 16px",
            fontFamily: "monospace", fontSize: 13, lineHeight: 1.8, color: dark ? "#FCD34D" : "#92660a", overflowX: "auto" }}>
            {`- OPENAI_API_KEY = "sk-demo1234567890EXPOSED"\n+ OPENAI_API_KEY = "[REVOKED — rotated via Secret Engine]"`}
          </div>
          <div style={{ marginTop: 14, color: subText, fontSize: 14, lineHeight: 1.6 }}>
            The exposed key was revoked within milliseconds. A replacement was injected into the secret store and a corrected PR was automatically opened.
          </div>
        </div>
      </Panel>
    ),

    Resolution: (
      <Panel>
        <div style={{ background: cardBg, border: cardBorder, borderRadius: 18, padding: "18px 16px" }}>
          <h2 style={{ color: "#C49A47", margin: "0 0 14px" }}>Resolution</h2>
          <div className="metrics-grid" style={{ marginBottom: 16 }}>
            <MetricCard title="Compliance Score" value={`${animatingScore}%`} subvalue={`${score.before}% → ${score.after}%`} theme={theme} />
            <MetricCard title="Time to Resolve" value="< 1s" subvalue="Fully automated" theme={theme} />
            <MetricCard title="Secrets Rotated" value="1" subvalue="Zero human action" theme={theme} />
          </div>
          <div style={{ color: subText, fontSize: 14, lineHeight: 1.6 }}>
            All checks passed. The repository is now secure. No human intervention was required — RepoGuard handled detection, revocation, and remediation end-to-end.
          </div>
        </div>
      </Panel>
    ),
  };

  return (
    <div style={{ minHeight: "100dvh", background: shellBg, color: shellText,
      fontFamily: "Inter, system-ui, sans-serif", padding: "0 0 40px" }}>

      <style>{`
        * { box-sizing: border-box; }

        @keyframes fadeSlide {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .rg-wrap {
          max-width: 1160px;
          margin: 0 auto;
          padding: 20px 16px 0;
        }

        /* Metric cards grid */
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
        }

        /* Repo rows always stack */
        .repo-row {
          display: block;
        }

        /* Main 2-col layout: content left, feed right */
        .main-grid {
          display: grid;
          grid-template-columns: 1fr 300px;
          gap: 16px;
          align-items: start;
        }

        /* Nav row */
        .nav-row {
          display: flex;
          gap: 8px;
          margin-bottom: 20px;
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
          padding: 10px 16px;
          cursor: pointer;
          transition: all 160ms ease;
          white-space: nowrap;
          flex-shrink: 0;
          font-size: 14px;
          font-weight: 600;
          font-family: inherit;
          min-height: 42px;
        }
        .nav-btn:hover { background: ${dark ? "rgba(255,255,255,0.10)" : "rgba(28,44,69,0.12)"}; }
        .nav-btn.active {
          background: #C49A47 !important;
          color: #111111 !important;
          border-color: #C49A47 !important;
          box-shadow: 0 4px 16px rgba(196,154,71,0.30);
        }

        /* Tablet: stack sidebar */
        @media (max-width: 820px) {
          .main-grid {
            grid-template-columns: 1fr;
          }
        }

        /* Mobile: 2-col metrics */
        @media (max-width: 640px) {
          .rg-wrap { padding: 14px 12px 0; }
          .metrics-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
        }

        /* Small mobile: 1-col metrics */
        @media (max-width: 400px) {
          .metrics-grid { grid-template-columns: 1fr; }
        }
      `}</style>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)}
        settings={settings} setSettings={setSettings} theme={theme} />

      <div className="rg-wrap">

        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start",
          marginBottom: 20, gap: 12 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ color: "#C49A47", fontSize: 26, fontWeight: 800, lineHeight: 1.1 }}>RepoGuard</div>
            <div style={{ color: subText, marginTop: 3, fontSize: 13 }}>Stop insecure code before it merges.</div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
            <span style={{ fontSize: 12, color: subText, display: "none", maxWidth: 120,
              overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
              className="user-email">
              {authenticatedUser}
            </span>
            <button onClick={() => { haptic(settings.haptics, 10); setSettingsOpen(true); }}
              style={{ background: cardBg, border: cardBorder, color: shellText,
                borderRadius: 10, padding: "9px 14px", cursor: "pointer",
                fontWeight: 600, fontSize: 14, whiteSpace: "nowrap", minHeight: 42, fontFamily: "inherit" }}>
              ⚙ Settings
            </button>
            <StatusBadge status={status} theme={theme} />
          </div>
        </div>

        {/* Nav tabs */}
        <div className="nav-row">
          {pages.map((p, i) => (
            <button key={p} className={`nav-btn${activeIndex === i ? " active" : ""}`} onClick={() => goPage(p)}>
              {p}
            </button>
          ))}
        </div>

        {/* Main grid */}
        <div className="main-grid">
          <div>{pageContent[page]}</div>

          {/* Live event feed */}
          <div style={{ background: cardBg, border: cardBorder, borderRadius: 18,
            padding: "16px", height: "fit-content" }}>
            <div style={{ color: "#C49A47", fontWeight: 700, marginBottom: 12, fontSize: 15 }}>
              Live Event Feed
            </div>
            <div style={{ display: "grid", gap: 8 }}>
              {events.map((ev, i) => (
                <div key={`${ev.message}-${i}`} style={{
                  background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
                  border: dark ? "1px solid rgba(255,255,255,0.05)" : "1px solid rgba(28,44,69,0.07)",
                  borderRadius: 10, padding: "10px 12px",
                  animation: "fadeSlide 240ms ease",
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

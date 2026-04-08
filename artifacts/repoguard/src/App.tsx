import React, { useEffect, useMemo, useRef, useState } from "react";

const pages = ["Command", "Breach", "Correction", "Resolution"];

function haptic(enabled, pattern = 10) {
  if (!enabled) return;
  if (typeof navigator !== "undefined" && navigator.vibrate) {
    navigator.vibrate(pattern);
  }
}

function playSwoosh(enabled) {
  if (!enabled) return;
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
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
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
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
  const map = {
    secure: { label: "Secure", color: "#6EE7B7" },
    monitoring: { label: "Monitoring", color: "#93C5FD" },
    breach: { label: "Breach Detected", color: "#FCA5A5" },
    correcting: { label: "Correcting", color: "#FCD34D" },
    resolved: { label: "Resolved", color: "#6EE7B7" },
  };
  const item = map[status] || map.monitoring;

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "8px 12px",
        borderRadius: 999,
        background: theme === "dark" ? "rgba(255,255,255,0.06)" : "rgba(28,44,69,0.06)",
        border: `1px solid ${item.color}55`,
        color: item.color,
        fontSize: 13,
      }}
    >
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: item.color,
          boxShadow: `0 0 10px ${item.color}88`,
        }}
      />
      {item.label}
    </span>
  );
}

function MetricCard({ title, value, subvalue, theme }) {
  const dark = theme === "dark";
  return (
    <div
      style={{
        background: dark ? "rgba(17,17,17,0.72)" : "rgba(255,255,255,0.9)",
        border: dark ? "1px solid rgba(196,154,71,0.20)" : "1px solid rgba(28,44,69,0.12)",
        borderRadius: 18,
        padding: 20,
        boxShadow: "0 18px 40px rgba(0,0,0,0.12)",
      }}
    >
      <div style={{ fontSize: 13, color: dark ? "rgba(255,255,255,0.65)" : "rgba(28,44,69,0.65)", marginBottom: 10 }}>
        {title}
      </div>
      <div style={{ fontSize: 28, fontWeight: 700, color: "#C49A47" }}>{value}</div>
      {subvalue ? (
        <div style={{ marginTop: 6, fontSize: 13, color: dark ? "rgba(255,255,255,0.7)" : "rgba(28,44,69,0.72)" }}>{subvalue}</div>
      ) : null}
    </div>
  );
}

function RepoRow({ repo, theme }) {
  const dark = theme === "dark";
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1.2fr 1fr 0.8fr",
        gap: 12,
        padding: "14px 16px",
        background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
        borderRadius: 14,
        border: dark ? "1px solid rgba(255,255,255,0.06)" : "1px solid rgba(28,44,69,0.08)",
        marginBottom: 10,
      }}
    >
      <div style={{ fontWeight: 600 }}>{repo.name}</div>
      <div style={{ color: dark ? "rgba(255,255,255,0.72)" : "rgba(28,44,69,0.72)" }}>{repo.issue}</div>
      <div style={{ textAlign: "right" }}>
        <StatusBadge status={repo.status} theme={theme} />
      </div>
    </div>
  );
}

function Panel({ children }) {
  return <div style={{ animation: "fadeSlide 300ms ease" }}>{children}</div>;
}

function SettingsModal({ open, onClose, settings, setSettings, theme }) {
  if (!open) return null;
  const dark = theme === "dark";
  const cardBg = dark ? "rgba(17,17,17,0.95)" : "rgba(255,255,255,0.98)";
  const text = dark ? "#FFFFFF" : "#1C2C45";

  const Toggle = ({ label, value, onChange }) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 0", borderBottom: `1px solid ${dark ? "rgba(255,255,255,0.08)" : "rgba(28,44,69,0.08)"}` }}>
      <div>{label}</div>
      <button
        onClick={onChange}
        style={{
          background: value ? "#C49A47" : dark ? "rgba(255,255,255,0.12)" : "rgba(28,44,69,0.12)",
          color: value ? "#111111" : text,
          border: "none",
          borderRadius: 999,
          padding: "8px 14px",
          cursor: "pointer",
          fontWeight: 700,
        }}
      >
        {value ? "On" : "Off"}
      </button>
    </div>
  );

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", display: "grid", placeItems: "center", zIndex: 1000 }}>
      <div style={{ width: 560, maxWidth: "92vw", background: cardBg, color: text, borderRadius: 22, padding: 24, boxShadow: "0 28px 80px rgba(0,0,0,0.28)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h2 style={{ margin: 0 }}>Settings</h2>
          <button onClick={onClose} style={{ border: "none", background: "transparent", color: text, fontSize: 22, cursor: "pointer" }}>×</button>
        </div>
        <Toggle label="Sound effects" value={settings.sound} onChange={() => setSettings((s) => ({ ...s, sound: !s.sound }))} />
        <Toggle label="Haptic feedback" value={settings.haptics} onChange={() => setSettings((s) => ({ ...s, haptics: !s.haptics }))} />
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 0" }}>
          <div>Appearance</div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => setSettings((s) => ({ ...s, theme: "light" }))}
              style={{
                border: "none",
                borderRadius: 12,
                padding: "8px 12px",
                cursor: "pointer",
                background: settings.theme === "light" ? "#C49A47" : dark ? "rgba(255,255,255,0.12)" : "rgba(28,44,69,0.12)",
                color: settings.theme === "light" ? "#111111" : text,
                fontWeight: 700,
              }}
            >
              Light
            </button>
            <button
              onClick={() => setSettings((s) => ({ ...s, theme: "dark" }))}
              style={{
                border: "none",
                borderRadius: 12,
                padding: "8px 12px",
                cursor: "pointer",
                background: settings.theme === "dark" ? "#C49A47" : dark ? "rgba(255,255,255,0.12)" : "rgba(28,44,69,0.12)",
                color: settings.theme === "dark" ? "#111111" : text,
                fontWeight: 700,
              }}
            >
              Dark
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function AuthScreen({ theme, sound, haptics, onAuthenticated }) {
  const dark = theme === "dark";
  const [stage, setStage] = useState("email");
  const [email, setEmail] = useState("demo@repoguard.ai");
  const [code, setCode] = useState("");
  const [message, setMessage] = useState("Enter your email to receive a verification code.");

  const submitEmail = async () => {
    haptic(haptics, 14);
    playSwoosh(sound);
    const res = await fetch("/api/auth/request-code", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const data = await res.json();
    setMessage(`Verification code sent to ${data.email}. Demo code: ${data.demo_code}`);
    setStage("code");
  };

  const verifyCode = async () => {
    haptic(haptics, 18);
    const res = await fetch("/api/auth/verify-code", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code }),
    });
    const data = await res.json();
    if (data.verified) {
      playPop(sound);
      haptic(haptics, [10, 30, 10]);
      onAuthenticated(email);
    } else {
      setMessage("Invalid code. Use the demo code displayed above.");
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        background: dark
          ? "linear-gradient(180deg, #1C2C45 0%, #142237 100%)"
          : "linear-gradient(180deg, #F7F4EE 0%, #EBE3D6 100%)",
        color: dark ? "white" : "#1C2C45",
        padding: 24,
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          width: 520,
          maxWidth: "92vw",
          background: dark ? "rgba(17,17,17,0.78)" : "rgba(255,255,255,0.92)",
          borderRadius: 24,
          padding: 28,
          border: dark ? "1px solid rgba(196,154,71,0.20)" : "1px solid rgba(28,44,69,0.10)",
          boxShadow: "0 30px 80px rgba(0,0,0,0.18)",
        }}
      >
        <div style={{ color: "#C49A47", fontSize: 34, fontWeight: 800 }}>RepoGuard</div>
        <div style={{ marginTop: 6, color: dark ? "rgba(255,255,255,0.72)" : "rgba(28,44,69,0.72)" }}>
          Secure sign in with email and 2FA.
        </div>

        <div style={{ marginTop: 22 }}>
          <div style={{ fontSize: 13, marginBottom: 8, color: dark ? "rgba(255,255,255,0.72)" : "rgba(28,44,69,0.72)" }}>Email</div>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={stage === "code"}
            style={{
              width: "100%",
              boxSizing: "border-box",
              padding: "14px 16px",
              borderRadius: 14,
              border: dark ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(28,44,69,0.10)",
              background: dark ? "#0F1722" : "#FFFFFF",
              color: dark ? "white" : "#1C2C45",
              outline: "none",
            }}
          />
        </div>

        {stage === "code" ? (
          <div style={{ marginTop: 18 }}>
            <div style={{ fontSize: 13, marginBottom: 8, color: dark ? "rgba(255,255,255,0.72)" : "rgba(28,44,69,0.72)" }}>Verification code</div>
            <input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Enter 6-digit code"
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "14px 16px",
                borderRadius: 14,
                border: dark ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(28,44,69,0.10)",
                background: dark ? "#0F1722" : "#FFFFFF",
                color: dark ? "white" : "#1C2C45",
                outline: "none",
              }}
            />
          </div>
        ) : null}

        <div style={{ marginTop: 18, color: dark ? "rgba(255,255,255,0.74)" : "rgba(28,44,69,0.74)", lineHeight: 1.6 }}>
          {message}
        </div>

        <div style={{ display: "flex", gap: 10, marginTop: 24 }}>
          {stage === "email" ? (
            <button
              onClick={submitEmail}
              style={{
                background: "#C49A47",
                color: "#111111",
                border: "none",
                borderRadius: 14,
                padding: "12px 16px",
                fontWeight: 800,
                cursor: "pointer",
              }}
            >
              Send code
            </button>
          ) : (
            <button
              onClick={verifyCode}
              style={{
                background: "#C49A47",
                color: "#111111",
                border: "none",
                borderRadius: 14,
                padding: "12px 16px",
                fontWeight: 800,
                cursor: "pointer",
              }}
            >
              Verify and enter
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState("Command");
  const [events, setEvents] = useState([]);
  const [repos, setRepos] = useState([]);
  const [score, setScore] = useState({ before: 72, after: 72 });
  const [status, setStatus] = useState("monitoring");
  const [animatingScore, setAnimatingScore] = useState(72);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [authenticatedUser, setAuthenticatedUser] = useState("");
  const [settings, setSettings] = useState(() => {
    const raw = localStorage.getItem("repoguard-settings");
    return raw ? JSON.parse(raw) : { sound: true, haptics: true, theme: "dark" };
  });
  const lastEventCount = useRef(0);
  const activeIndex = useMemo(() => pages.indexOf(page), [page]);
  const theme = settings.theme;

  useEffect(() => {
    localStorage.setItem("repoguard-settings", JSON.stringify(settings));
  }, [settings]);

  async function refreshState() {
    const [eventsRes, reposRes, scoreRes, statusRes] = await Promise.all([
      fetch("/api/events"),
      fetch("/api/repos"),
      fetch("/api/compliance"),
      fetch("/api/system-status"),
    ]);

    const eventsData = await eventsRes.json();
    const reposData = await reposRes.json();
    const scoreData = await scoreRes.json();
    const statusData = await statusRes.json();

    setEvents(eventsData);
    setRepos(reposData);
    setScore(scoreData);
    setStatus(statusData.status);
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

    setTimeout(() => {
      setPage("Breach");
      playSwoosh(settings.sound);
      haptic(settings.haptics, 18);
    }, 800);

    setTimeout(() => {
      setPage("Correction");
      playSwoosh(settings.sound);
      haptic(settings.haptics, 18);
    }, 2800);

    setTimeout(() => {
      setPage("Resolution");
      playSwoosh(settings.sound);
      haptic(settings.haptics, 18);
    }, 5200);
  };

  const goPage = (nextPage) => {
    setPage(nextPage);
    playSwoosh(settings.sound);
    haptic(settings.haptics, 10);
  };

  if (!authenticatedUser) {
    return (
      <AuthScreen
        theme={theme}
        sound={settings.sound}
        haptics={settings.haptics}
        onAuthenticated={setAuthenticatedUser}
      />
    );
  }

  const dark = theme === "dark";
  const shellBg = dark
    ? "linear-gradient(180deg, #1C2C45 0%, #142237 100%)"
    : "linear-gradient(180deg, #F7F4EE 0%, #EBE3D6 100%)";
  const shellText = dark ? "white" : "#1C2C45";
  const cardBg = dark ? "rgba(17,17,17,0.72)" : "rgba(255,255,255,0.90)";
  const cardBorder = dark ? "1px solid rgba(196,154,71,0.20)" : "1px solid rgba(28,44,69,0.10)";
  const subText = dark ? "rgba(255,255,255,0.68)" : "rgba(28,44,69,0.68)";

  const pageContent = {
    Command: (
      <Panel>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 18 }}>
          <MetricCard title="System Status" value={status === "breach" ? "Active Breach" : status === "resolved" ? "Resolved" : "Monitoring"} subvalue="Autonomous enforcement online" theme={theme} />
          <MetricCard title="Compliance Score" value={`${animatingScore}%`} subvalue={`${score.before}% → ${score.after}%`} theme={theme} />
          <MetricCard title="Repositories" value={String(repos.length)} subvalue="Live monitored inventory" theme={theme} />
        </div>

        <div style={{ marginTop: 22, background: cardBg, border: cardBorder, borderRadius: 20, padding: 22 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h2 style={{ color: "#C49A47", margin: 0 }}>Repository Status Board</h2>
            <button
              onClick={triggerDemo}
              style={{
                background: "#C49A47",
                color: "#111111",
                border: "none",
                borderRadius: 12,
                padding: "10px 14px",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Run Demo
            </button>
          </div>
          {repos.map((repo) => (
            <RepoRow key={repo.name} repo={repo} theme={theme} />
          ))}
        </div>
      </Panel>
    ),
    Breach: (
      <Panel>
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 18 }}>
          <div style={{ background: cardBg, borderRadius: 20, padding: 22, border: dark ? "1px solid rgba(252,165,165,0.22)" : "1px solid rgba(252,165,165,0.28)" }}>
            <h2 style={{ color: "#C49A47", marginTop: 0 }}>Detected Breach</h2>
            <div style={{ color: "#FCA5A5", marginBottom: 12 }}>Critical secret exposure detected in api-service</div>
            <pre style={{ background: dark ? "#0A0A0A" : "#F9F7F2", padding: 18, borderRadius: 14, overflow: "auto", color: "#C2410C" }}>
{`# insecure pattern detected
OPENAI_API_KEY = "sk-demo1234567890EXPOSED"
client = OpenAI(api_key=OPENAI_API_KEY)`}
            </pre>
          </div>
          <div style={{ background: cardBg, borderRadius: 20, padding: 22, border: cardBorder }}>
            <h2 style={{ color: "#C49A47", marginTop: 0 }}>Impact</h2>
            <div style={{ marginBottom: 12 }}><StatusBadge status="breach" theme={theme} /></div>
            <div style={{ color: subText, lineHeight: 1.7 }}>
              RepoGuard classified the event as a confirmed secret exposure and triggered containment.
            </div>
          </div>
        </div>
      </Panel>
    ),
    Correction: (
      <Panel>
        <div style={{ background: cardBg, borderRadius: 20, padding: 22, border: dark ? "1px solid rgba(252,211,77,0.20)" : "1px solid rgba(196,154,71,0.24)" }}>
          <h2 style={{ color: "#C49A47", marginTop: 0 }}>Automated Correction</h2>
          <pre style={{ background: dark ? "#0A0A0A" : "#F9F7F2", padding: 18, borderRadius: 14, overflow: "auto", color: "#047857" }}>
{`- OPENAI_API_KEY = "sk-demo1234567890EXPOSED"
- client = OpenAI(api_key=OPENAI_API_KEY)

+ from secret_engine import get_secret
+ OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
+ client = OpenAI(api_key=OPENAI_API_KEY)`}
          </pre>
          <div style={{ marginTop: 12, color: subText }}>
            Pull request created. Enforcement check failed. Merge remained blocked until remediation.
          </div>
        </div>
      </Panel>
    ),
    Resolution: (
      <Panel>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
          <div style={{ background: cardBg, borderRadius: 20, padding: 22, border: dark ? "1px solid rgba(110,231,183,0.24)" : "1px solid rgba(110,231,183,0.28)" }}>
            <h2 style={{ color: "#C49A47", marginTop: 0 }}>Resolved State</h2>
            <ul style={{ lineHeight: 1.9, color: subText }}>
              <li>Key revoked</li>
              <li>Code patched</li>
              <li>Checks passed</li>
              <li>Repository returned to secure state</li>
            </ul>
          </div>
          <div style={{ background: cardBg, borderRadius: 20, padding: 22, border: cardBorder }}>
            <h2 style={{ color: "#C49A47", marginTop: 0 }}>Compliance Improvement</h2>
            <div style={{ fontSize: 38, fontWeight: 800, color: "#6EE7B7" }}>
              {score.before}% → {score.after}%
            </div>
            <div style={{ marginTop: 10, color: subText }}>
              RepoGuard restored policy alignment and secured the repo lifecycle.
            </div>
          </div>
        </div>
      </Panel>
    ),
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: shellBg,
        color: shellText,
        padding: 24,
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <style>{`
        @keyframes fadeSlide {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .nav-btn {
          background: ${dark ? "rgba(255,255,255,0.04)" : "rgba(28,44,69,0.06)"};
          border: 1px solid ${dark ? "rgba(255,255,255,0.08)" : "rgba(28,44,69,0.10)"};
          color: ${shellText};
          border-radius: 14px;
          padding: 10px 16px;
          cursor: pointer;
          transition: all 180ms ease;
        }
        .nav-btn:hover {
          transform: translateY(-1px);
        }
        .nav-btn.active {
          background: #C49A47;
          color: #111111;
          border-color: #C49A47;
          box-shadow: 0 8px 24px rgba(196,154,71,0.25);
        }
      `}</style>

      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={settings}
        setSettings={setSettings}
        theme={theme}
      />

      <div style={{ maxWidth: 1240, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <div>
            <div style={{ color: "#C49A47", fontSize: 34, fontWeight: 800 }}>RepoGuard</div>
            <div style={{ color: subText, marginTop: 4 }}>
              Stop insecure code before it merges.
            </div>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <div style={{ fontSize: 13, color: subText }}>{authenticatedUser}</div>
            <button
              onClick={() => {
                haptic(settings.haptics, 10);
                setSettingsOpen(true);
              }}
              style={{
                background: cardBg,
                border: cardBorder,
                color: shellText,
                borderRadius: 12,
                padding: "10px 14px",
                cursor: "pointer",
              }}
            >
              Settings
            </button>
            <StatusBadge status={status === "secure" ? "secure" : status} theme={theme} />
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, marginBottom: 24, flexWrap: "wrap" }}>
          {pages.map((p, index) => (
            <button
              key={p}
              className={`nav-btn ${activeIndex === index ? "active" : ""}`}
              onClick={() => goPage(p)}
            >
              {p}
            </button>
          ))}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 20 }}>
          <div>{pageContent[page]}</div>

          <div style={{ background: cardBg, border: cardBorder, borderRadius: 20, padding: 20, height: "fit-content" }}>
            <div style={{ color: "#C49A47", fontWeight: 700, marginBottom: 14 }}>Live Event Feed</div>
            <div style={{ display: "grid", gap: 10 }}>
              {events.map((event, i) => (
                <div
                  key={`${event.message}-${i}`}
                  style={{
                    background: dark ? "rgba(255,255,255,0.03)" : "rgba(28,44,69,0.04)",
                    border: dark ? "1px solid rgba(255,255,255,0.05)" : "1px solid rgba(28,44,69,0.08)",
                    borderRadius: 14,
                    padding: "12px 14px",
                    animation: "fadeSlide 240ms ease",
                  }}
                >
                  <div style={{ fontSize: 14 }}>{event.message}</div>
                  <div style={{ marginTop: 4, fontSize: 12, color: subText }}>{event.time}</div>
                </div>
              ))}
              {events.length === 0 ? (
                <div style={{ color: subText }}>No active events.</div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

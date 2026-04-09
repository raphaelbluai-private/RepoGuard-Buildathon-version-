import { useEffect, useRef, useState } from "react";

type EventType = "info" | "warning" | "critical";

interface FeedEvent {
  id: number;
  message: string;
  type: EventType;
  timestamp: number;
}

const EVENT_TEMPLATES: { message: string; type: EventType }[] = [
  { message: "Scanning repository integrity...",       type: "info"     },
  { message: "Anomaly detected in dependency tree",    type: "warning"  },
  { message: "Auto enforcement triggered",             type: "critical" },
  { message: "Secrets rotated successfully",           type: "info"     },
  { message: "Unauthorized access attempt blocked",    type: "critical" },
  { message: "Compliance recalculating...",            type: "info"     },
  { message: "Branch protection rule verified",        type: "info"     },
  { message: "Suspicious commit pattern flagged",      type: "warning"  },
  { message: "Secret exposure detected in diff",       type: "critical" },
  { message: "Merge request quarantined",              type: "warning"  },
  { message: "Dependency audit passed",                type: "info"     },
  { message: "Unauthorized push attempt blocked",      type: "critical" },
  { message: "Webhook signature mismatch detected",    type: "warning"  },
  { message: "Policy enforcement re-armed",            type: "info"     },
  { message: "Repo integrity scan complete",           type: "info"     },
];

export function getElapsed(seconds: number): string {
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

// ─── Individual feed item ─────────────────────────────────────────────────────
function FeedItem({ event, dark }: { event: FeedEvent; dark: boolean }) {
  const [elapsed, setElapsed] = useState(
    Math.floor((Date.now() - event.timestamp) / 1000)
  );

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - event.timestamp) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, [event.timestamp]);

  const colorMap: Record<EventType, string> = {
    info:     "#93C5FD",
    warning:  "#FCD34D",
    critical: "#FCA5A5",
  };

  const bgMap: Record<EventType, string> = {
    info:     "rgba(147,197,253,0.07)",
    warning:  "rgba(252,211,77,0.07)",
    critical: "rgba(252,165,165,0.09)",
  };

  const color = colorMap[event.type];

  const Dot = () => {
    const base: React.CSSProperties = {
      width: 8, height: 8, borderRadius: "50%",
      background: color, flexShrink: 0, display: "inline-block",
    };
    if (event.type === "critical") return <span className="animate-ping"  style={base} />;
    if (event.type === "warning")  return <span className="animate-pulse" style={base} />;
    return <span style={{ ...base, boxShadow: `0 0 6px ${color}88` }} />;
  };

  return (
    <div
      style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "9px 12px", borderRadius: 12,
        background: dark ? bgMap[event.type] : bgMap[event.type].replace(/0\.\d+\)$/, "0.12)"),
        border: `1px solid ${color}2E`,
        boxShadow: `0 1px 6px rgba(0,0,0,${dark ? "0.18" : "0.06"})`,
        animation: "warEventIn 220ms ease both",
        flexShrink: 0,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
        <Dot />
        <span style={{
          fontSize: 12, lineHeight: 1.4,
          color: dark ? "rgba(255,255,255,0.82)" : "#1C2C45",
          overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
        }}>
          {event.message}
        </span>
      </div>
      <span style={{
        fontSize: 11, marginLeft: 10, flexShrink: 0,
        color: dark ? "rgba(255,255,255,0.38)" : "rgba(28,44,69,0.42)",
      }}>
        {getElapsed(elapsed)}
      </span>
    </div>
  );
}

// ─── War Room Feed ────────────────────────────────────────────────────────────
export default function WarRoomFeed({ theme }: { theme: string }) {
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const dark = theme === "dark";

  // Auto-generate a new event every 2 s
  useEffect(() => {
    const interval = setInterval(() => {
      const tpl = EVENT_TEMPLATES[Math.floor(Math.random() * EVENT_TEMPLATES.length)];
      setEvents(prev => [
        { id: Date.now(), message: tpl.message, type: tpl.type, timestamp: Date.now() },
        ...prev,
      ].slice(0, 20));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Smoothly scroll the container up continuously
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    let frame: number;
    const tick = () => {
      el.scrollTop += 0.4;
      // Reset when we've scrolled past half the content (creates loop illusion)
      if (el.scrollTop >= el.scrollHeight / 2) el.scrollTop = 0;
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <div
      style={{
        background: dark
          ? "rgba(10,10,10,0.72)"
          : "rgba(255,255,255,0.88)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        border: dark
          ? "1px solid rgba(196,154,71,0.20)"
          : "1px solid rgba(28,44,69,0.12)",
        borderRadius: 18,
        padding: 16,
        boxShadow: dark
          ? "0 8px 32px rgba(0,0,0,0.42), inset 0 1px 0 rgba(255,255,255,0.04)"
          : "0 8px 32px rgba(28,44,69,0.10), inset 0 1px 0 rgba(255,255,255,0.80)",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <span style={{
          color: "#C49A47", fontWeight: 700, fontSize: 12,
          textTransform: "uppercase", letterSpacing: "0.10em",
        }}>
          Live Event Feed
        </span>
        <span style={{
          display: "inline-flex", alignItems: "center", gap: 5,
          padding: "3px 9px", borderRadius: 999,
          background: dark ? "rgba(110,231,183,0.10)" : "rgba(110,231,183,0.14)",
          border: "1px solid rgba(110,231,183,0.32)",
        }}>
          <span className="animate-pulse" style={{
            width: 6, height: 6, borderRadius: "50%",
            background: "#6EE7B7", display: "inline-block",
          }} />
          <span style={{ fontSize: 10, color: "#6EE7B7", fontWeight: 700, letterSpacing: "0.05em" }}>LIVE</span>
        </span>
      </div>

      {/* Scrolling feed */}
      <div style={{ position: "relative", height: 340 }}>
        <div
          ref={scrollRef}
          style={{
            height: "100%",
            overflowY: "hidden",
            display: "flex",
            flexDirection: "column",
            gap: 6,
          }}
        >
          {/* Render list twice for seamless loop */}
          {[...events, ...events].map((event, i) => (
            <FeedItem key={`${event.id}-${i}`} event={event} dark={dark} />
          ))}
          {events.length === 0 && (
            <div style={{
              fontSize: 12, paddingTop: 6,
              color: dark ? "rgba(255,255,255,0.35)" : "rgba(28,44,69,0.38)",
            }}>
              Initialising feed…
            </div>
          )}
        </div>

        {/* Top fade */}
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0, height: 32,
          background: dark
            ? "linear-gradient(rgba(10,10,10,0.72), transparent)"
            : "linear-gradient(rgba(255,255,255,0.88), transparent)",
          pointerEvents: "none",
        }} />

        {/* Bottom fade */}
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0, height: 48,
          background: dark
            ? "linear-gradient(transparent, rgba(10,10,10,0.90))"
            : "linear-gradient(transparent, rgba(255,255,255,0.92))",
          pointerEvents: "none",
        }} />
      </div>
    </div>
  );
}

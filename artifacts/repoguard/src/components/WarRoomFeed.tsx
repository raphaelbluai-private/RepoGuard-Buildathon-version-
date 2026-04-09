import { useEffect, useRef, useState } from "react";

type EventType = "info" | "warning" | "critical";

interface FeedEvent {
  id: number;
  message: string;
  type: EventType;
  timestamp: number;
}

const EVENT_TEMPLATES: { message: string; type: EventType }[] = [
  { message: "Critical secret exposure detected in GitHub / api-service",   type: "critical" },
  { message: "Auto enforcement triggered",                                   type: "critical" },
  { message: "Credential invalidation sequence started",                    type: "critical" },
  { message: "Secure runtime injection patch generated",                    type: "info"     },
  { message: "Merge protection locked unsafe branch",                       type: "warning"  },
  { message: "Repository integrity restored",                               type: "info"     },
  { message: "Unauthorized access attempt blocked",                         type: "critical" },
  { message: "Compliance recalculating...",                                 type: "info"     },
  { message: "Anomaly detected in dependency tree",                         type: "warning"  },
  { message: "Secrets rotated successfully",                                type: "info"     },
  { message: "Webhook signature mismatch — request quarantined",            type: "warning"  },
  { message: "Branch protection rule verified",                             type: "info"     },
  { message: "Suspicious commit pattern flagged",                           type: "warning"  },
  { message: "Policy engine synchronised",                                  type: "info"     },
  { message: "Repo integrity scan complete",                                type: "info"     },
];

export function getElapsed(seconds: number): string {
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

// ─── Individual feed item ─────────────────────────────────────────────────────
function FeedItem({ event }: { event: FeedEvent }) {
  const [elapsed, setElapsed] = useState(
    Math.floor((Date.now() - event.timestamp) / 1000)
  );

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - event.timestamp) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, [event.timestamp]);

  const dotClass =
    event.type === "critical"
      ? "bg-red-400 animate-threat-pulse"
      : event.type === "warning"
      ? "bg-yellow-300 animate-pulse"
      : "bg-blue-300 animate-pulse";

  return (
    <div className="animate-fade-rise rounded-xl border border-white/10 bg-white/5 px-4 py-3 shadow-[0_8px_24px_rgba(0,0,0,0.16)] backdrop-blur-sm"
      style={{ flexShrink: 0 }}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <span className={`h-2.5 w-2.5 rounded-full flex-shrink-0 ${dotClass}`} />
          <span className="text-sm text-neutral-800 truncate">{event.message}</span>
        </div>
        <span className="text-xs text-neutral-500 flex-shrink-0">{elapsed}s ago</span>
      </div>
    </div>
  );
}

// ─── Cinematic Ticker ─────────────────────────────────────────────────────────
function CinematicTicker() {
  return (
    <div className="overflow-hidden rounded-xl border border-yellow-500/20 bg-black/30 backdrop-blur-md mb-3">
      <div className="whitespace-nowrap py-2 text-xs tracking-wide text-white/70 animate-ticker-scroll">
        <span className="inline-block pl-[100%]">
          LIVE MONITORING ACTIVE&nbsp;&nbsp;•&nbsp;&nbsp;ENFORCEMENT ARMED&nbsp;&nbsp;•&nbsp;&nbsp;SECRET ROTATION ONLINE&nbsp;&nbsp;•&nbsp;&nbsp;MERGE PROTECTION ACTIVE&nbsp;&nbsp;•&nbsp;&nbsp;POLICY ENGINE SYNCHRONIZED&nbsp;&nbsp;•&nbsp;&nbsp;REPO INTEGRITY CHECKS RUNNING&nbsp;&nbsp;•&nbsp;&nbsp;
        </span>
      </div>
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
      if (el.scrollTop >= el.scrollHeight / 2) el.scrollTop = 0;
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <div className="relative overflow-hidden rounded-2xl"
      style={{
        background: dark ? "rgba(10,10,10,0.72)" : "rgba(255,255,255,0.88)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        border: dark ? "1px solid rgba(196,154,71,0.20)" : "1px solid rgba(28,44,69,0.12)",
        padding: 16,
        boxShadow: dark
          ? "0 8px 32px rgba(0,0,0,0.42), inset 0 1px 0 rgba(255,255,255,0.04)"
          : "0 8px 32px rgba(28,44,69,0.10), inset 0 1px 0 rgba(255,255,255,0.80)",
      }}
    >
      {/* Scan-sweep */}
      <div className="pointer-events-none absolute inset-y-0 w-24 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-scan-sweep" />

      <div className="relative">
        {/* Header */}
        <div className="flex justify-between items-center mb-3">
          <span style={{
            color: "#C49A47", fontWeight: 700, fontSize: 12,
            textTransform: "uppercase", letterSpacing: "0.10em",
          }}>
            Live Event Feed
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border"
            style={{
              background: dark ? "rgba(110,231,183,0.10)" : "rgba(110,231,183,0.14)",
              borderColor: "rgba(110,231,183,0.32)",
            }}>
            <span className="animate-pulse w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
            <span className="text-emerald-400 font-bold" style={{ fontSize: 10, letterSpacing: "0.05em" }}>LIVE</span>
          </span>
        </div>

        {/* Cinematic ticker */}
        <CinematicTicker />

        {/* Scrolling feed */}
        <div style={{ position: "relative", height: 300 }}>
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
            {[...events, ...events].map((event, i) => (
              <FeedItem key={`${event.id}-${i}`} event={event} />
            ))}
            {events.length === 0 && (
              <div className="text-xs pt-1" style={{
                color: dark ? "rgba(255,255,255,0.35)" : "rgba(28,44,69,0.38)",
              }}>
                Initialising feed…
              </div>
            )}
          </div>

          {/* Top fade */}
          <div className="pointer-events-none absolute top-0 left-0 right-0 h-8"
            style={{
              background: dark
                ? "linear-gradient(rgba(10,10,10,0.72), transparent)"
                : "linear-gradient(rgba(255,255,255,0.88), transparent)",
            }} />

          {/* Bottom fade */}
          <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-12"
            style={{
              background: dark
                ? "linear-gradient(transparent, rgba(10,10,10,0.90))"
                : "linear-gradient(transparent, rgba(255,255,255,0.92))",
            }} />
        </div>
      </div>
    </div>
  );
}

import React from "react";

export type RGStatus = "secure" | "verifying" | "breach" | "locked";

const CONFIG: Record<RGStatus, {
  color: string;
  ringAnimation: string;
  coreAnimation: string;
  label: string;
  sublabel: string;
}> = {
  secure: {
    color: "#32CD32",
    ringAnimation: "rgPulseRing 2s ease-in-out infinite",
    coreAnimation: "rgPulseRing 2s ease-in-out infinite",
    label: "SECURE",
    sublabel: "Integrity verified",
  },
  verifying: {
    color: "#1E90FF",
    ringAnimation: "rgSpin 2s linear infinite",
    coreAnimation: "rgGlow 1.6s ease-in-out infinite",
    label: "VERIFYING",
    sublabel: "Running policy checks…",
  },
  breach: {
    color: "#FF4136",
    ringAnimation: "rgShake 0.6s ease-in-out infinite",
    coreAnimation: "rgShake 0.6s ease-in-out infinite",
    label: "BREACH",
    sublabel: "Unauthorized activity detected",
  },
  locked: {
    color: "#00BFFF",
    ringAnimation: "none",
    coreAnimation: "rgGlow 2.5s ease-in-out infinite",
    label: "LOCKED",
    sublabel: "Execution blocked",
  },
};

interface RepoGuardCoreProps {
  status?: RGStatus;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  showImage?: boolean;
}

export function RepoGuardCore({
  status = "secure",
  size = "md",
  showLabel = true,
  showImage = true,
}: RepoGuardCoreProps) {
  const cfg = CONFIG[status];

  const dim = { sm: 80, md: 140, lg: 200 }[size];
  const imgDim = { sm: 44, md: 80, lg: 120 }[size];
  const fontSize = { sm: 10, md: 13, lg: 16 }[size];
  const sublabelSize = { sm: 9, md: 11, lg: 13 }[size];

  const dashedSegments = status === "verifying";

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>

      <div style={{ position: "relative", width: dim, height: dim, flexShrink: 0 }}>

        {/* Outer glow ring */}
        <div style={{
          position: "absolute", inset: 0, borderRadius: "50%",
          border: `2px ${dashedSegments ? "dashed" : "solid"} ${cfg.color}`,
          opacity: 0.5,
          animation: cfg.ringAnimation,
          boxShadow: `0 0 16px ${cfg.color}66`,
          "--rg-color": cfg.color,
        } as React.CSSProperties} />

        {/* Inner ring */}
        <div style={{
          position: "absolute", inset: dim * 0.1, borderRadius: "50%",
          border: `1px solid ${cfg.color}44`,
        }} />

        {/* Core image or fallback shield */}
        <div style={{
          position: "absolute",
          inset: dim * 0.15,
          borderRadius: "50%",
          background: "rgba(10,26,47,0.9)",
          border: `1px solid ${cfg.color}33`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          animation: cfg.coreAnimation,
          "--rg-color": cfg.color,
        } as React.CSSProperties}>
          {showImage ? (
            <img
              src="/rg-shield.png"
              alt="REPOGUARD"
              style={{
                width: imgDim,
                height: imgDim,
                objectFit: "cover",
                borderRadius: "50%",
                filter: status === "breach"
                  ? "hue-rotate(300deg) saturate(1.5)"
                  : status === "locked"
                  ? "hue-rotate(180deg) saturate(1.2)"
                  : "none",
                opacity: 0.95,
              }}
            />
          ) : (
            <img
              src="/rg-shield.png"
              alt="REPOGUARD"
              style={{ width: imgDim, height: imgDim, objectFit: "cover", borderRadius: "50%", opacity: 0.95 }}
            />
          )}
        </div>

        {/* State-specific corner dots */}
        {[0, 90, 180, 270].map((deg, i) => (
          <div key={i} style={{
            position: "absolute",
            top: "50%", left: "50%",
            width: size === "sm" ? 5 : 7,
            height: size === "sm" ? 5 : 7,
            borderRadius: "50%",
            background: cfg.color,
            boxShadow: `0 0 6px ${cfg.color}`,
            transform: `rotate(${deg}deg) translateX(${dim / 2 - (size === "sm" ? 3 : 5)}px) translateY(-50%)`,
            opacity: status === "locked" ? 1 : 0.7,
          }} />
        ))}
      </div>

      {showLabel && (
        <div style={{ textAlign: "center" }}>
          <div style={{
            fontSize, fontWeight: 800, letterSpacing: "0.12em",
            color: cfg.color,
            textShadow: `0 0 12px ${cfg.color}88`,
          }}>
            {cfg.label}
          </div>
          <div style={{
            fontSize: sublabelSize, color: "rgba(255,255,255,0.45)",
            letterSpacing: "0.04em", marginTop: 3,
          }}>
            {cfg.sublabel}
          </div>
        </div>
      )}
    </div>
  );
}

export default RepoGuardCore;

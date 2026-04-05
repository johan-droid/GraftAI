import React, { useMemo } from "react";
import { motion } from "framer-motion";

type DataPoint = {
  bucket: string;
  meetings: number;
  hours: number;
  categories?: Record<string, number>;
  dominant_category?: string | null;
};

interface Props {
  data: DataPoint[];
  height?: number;
  className?: string;
}

const DEFAULT_COLORS: Record<string, string> = {
  meeting: "#7c3aed",
  event: "#06b6d4",
  birthday: "#f97316",
  task: "#10b981",
  other: "#94a3b8",
};

function colorForCategory(cat?: string | null) {
  if (!cat) return "#7c3aed";
  return DEFAULT_COLORS[cat] ?? DEFAULT_COLORS.other;
}

export default function TimelineLineChart({ data, height = 140, className = "" }: Props) {
  const points = useMemo(() => data || [], [data]);

  const padding = { left: 22, right: 12, top: 12, bottom: 28 };
  const vw = Math.max(300, Math.max(1, points.length - 1) * 48 + padding.left + padding.right);
  const vh = height;
  const innerW = vw - padding.left - padding.right;
  const innerH = vh - padding.top - padding.bottom;

  const maxVal = Math.max(1, ...points.map((p) => p.meetings));

  const coords = points.map((p, i) => {
    const x = padding.left + (points.length === 1 ? innerW / 2 : (i * innerW) / Math.max(1, points.length - 1));
    const y = padding.top + innerH * (1 - p.meetings / maxVal);
    return { x, y, p };
  });

  // Group contiguous segments by dominant_category
  const segments: Array<{ color: string; points: typeof coords }> = [];
  let curSeg: { color: string; points: typeof coords } | null = null;
  coords.forEach((pt) => {
    const cat = pt.p.dominant_category ?? null;
    const color = colorForCategory(cat);
    if (!curSeg || curSeg.color !== color) {
      curSeg = { color, points: [pt] };
      segments.push(curSeg);
    } else {
      curSeg.points.push(pt);
    }
  });

  const pathForPoints = (pts: typeof coords) => pts.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt.x.toFixed(2)} ${pt.y.toFixed(2)}`).join(' ');

  const areaPathForPoints = (pts: typeof coords) => {
    if (pts.length === 0) return '';
    const top = pts.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt.x.toFixed(2)} ${pt.y.toFixed(2)}`).join(' ');
    const left = `L ${pts[pts.length - 1].x.toFixed(2)} ${(padding.top + innerH).toFixed(2)}`;
    const back = `L ${pts[0].x.toFixed(2)} ${(padding.top + innerH).toFixed(2)} Z`;
    return `${top} ${left} ${back}`;
  };

  return (
    <div className={`w-full ${className}`}>
      <svg width="100%" height={vh} viewBox={`0 0 ${vw} ${vh}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id="fade" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#7c3aed" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#7c3aed" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* draw grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const y = padding.top + innerH * t;
          return <line key={t} x1={padding.left} x2={vw - padding.right} y1={y} y2={y} stroke="#ffffff09" strokeWidth={1} />;
        })}

        {/* segments area + line */}
        {segments.map((seg, idx) => (
          <g key={idx}>
            {seg.points.length > 1 && (
              <motion.path
                d={areaPathForPoints(seg.points)}
                fill={seg.color}
                fillOpacity={0.06}
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1, delay: 0.05 * idx }}
              />
            )}

            <motion.path
              d={pathForPoints(seg.points)}
              stroke={seg.color}
              strokeWidth={2.5}
              fill="none"
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1, delay: 0.05 * idx }}
            />
          </g>
        ))}

        {/* points and x labels */}
        {coords.map((c, i) => (
          <g key={i}>
            <motion.circle
              cx={c.x}
              cy={c.y}
              r={4}
              fill={colorForCategory(c.p.dominant_category)}
              stroke="#0f172a22"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.04 * i }}
            >
              <title>{`${c.p.bucket}: ${c.p.meetings} meetings`}</title>
            </motion.circle>
            <text x={c.x} y={vh - 8} fontSize={9} fill="#94a3b8" textAnchor="middle">
              {c.p.bucket}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

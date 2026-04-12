"use client";

import { Box, BoxProps } from "@mui/material";
import { keyframes } from "@emotion/react";

const shimmer = keyframes`
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
`;

interface SkeletonProps extends Omit<BoxProps, 'sx'> {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
}

const skeletonGradient = `
  linear-gradient(
    90deg,
    hsl(240, 24%, 14%) 0%,
    hsl(240, 24%, 18%) 50%,
    hsl(240, 24%, 14%) 100%
  )
`;

export function Skeleton({
  width = "100%",
  height = 16,
  borderRadius = 8,
  className,
}: SkeletonProps) {
  return (
    <Box
      className={className}
      sx={{
        width,
        height,
        borderRadius,
        background: skeletonGradient,
        backgroundSize: "200% 100%",
        animation: `${shimmer} 1.5s ease-in-out infinite`,
      }}
    />
  );
}

// Pre-built skeleton patterns
export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? "75%" : "100%"}
          height={14}
          borderRadius={4}
        />
      ))}
    </Box>
  );
}

export function SkeletonCard() {
  return (
    <Box
      sx={{
        p: 3,
        background: "hsl(240, 24%, 14%)",
        border: "1px solid hsla(239, 84%, 67%, 0.1)",
        borderRadius: 3,
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
        <Skeleton width={48} height={48} borderRadius="12px" />
        <Box sx={{ flex: 1 }}>
          <Skeleton width="60%" height={20} borderRadius={4} />
          <Box sx={{ mt: 1 }}>
            <Skeleton width="40%" height={14} borderRadius={4} />
          </Box>
        </Box>
      </Box>
      <SkeletonText lines={2} />
    </Box>
  );
}

// Aliases for compatibility
export const CardSkeleton = SkeletonCard;
export const StatCardSkeleton = SkeletonCard;
export const PluginCardSkeleton = SkeletonCard;

export function SkeletonAvatar({ size = 40 }: { size?: number }) {
  return <Skeleton width={size} height={size} borderRadius="50%" />;
}

export function SkeletonButton({ width = 120 }: { width?: number }) {
  return <Skeleton width={width} height={40} borderRadius="12px" />;
}

export function SkeletonStat() {
  return (
    <Box sx={{ textAlign: "center" }}>
      <Box sx={{ display: "flex", justifyContent: "center" }}>
        <Skeleton width={80} height={40} borderRadius={8} />
      </Box>
      <Box sx={{ mt: 1, display: "flex", justifyContent: "center" }}>
        <Skeleton width={100} height={16} borderRadius={4} />
      </Box>
    </Box>
  );
}

export function SkeletonList({ items = 5 }: { items?: number }) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {Array.from({ length: items }).map((_, i) => (
        <Box key={i} sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <SkeletonAvatar size={40} />
          <Box sx={{ flex: 1 }}>
            <Skeleton width="70%" height={16} borderRadius={4} />
            <Box sx={{ mt: 0.5 }}>
              <Skeleton width="40%" height={12} borderRadius={4} />
            </Box>
          </Box>
          <Skeleton width={60} height={24} borderRadius={4} />
        </Box>
      ))}
    </Box>
  );
}

export function SkeletonTable({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: "flex", gap: 2, mb: 2, pb: 2, borderBottom: "1px solid hsla(239, 84%, 67%, 0.1)" }}>
        {Array.from({ length: columns }).map((_, i) => (
          <Box key={i} sx={{ flex: 1 }}>
            <Skeleton width="80%" height={20} borderRadius={4} />
          </Box>
        ))}
      </Box>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <Box
          key={rowIndex}
          sx={{
            display: "flex",
            gap: 2,
            py: 2,
            borderBottom: "1px solid hsla(239, 84%, 67%, 0.05)",
          }}
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Box key={colIndex} sx={{ flex: 1 }}>
              <Skeleton width={colIndex === 0 ? "60%" : "80%"} height={16} borderRadius={4} />
            </Box>
          ))}
        </Box>
      ))}
    </Box>
  );
}

export function SkeletonDashboard() {
  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Skeleton width={200} height={32} borderRadius={8} />
        <Box sx={{ mt: 1 }}>
          <Skeleton width={300} height={16} borderRadius={4} />
        </Box>
      </Box>

      {/* Stats Row */}
      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 3, mb: 4 }}>
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </Box>

      {/* Main Content */}
      <Box sx={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 3 }}>
        <SkeletonCard />
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          <SkeletonCard />
          <SkeletonCard />
        </Box>
      </Box>
    </Box>
  );
}

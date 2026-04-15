// Professional Theme System for GraftAI - Developer "Deep Black" Edition
// Inspired by high-end developer tools and system terminals.

export type ThemeMode = "light" | "dark" | "auto";

// Precision Technical Palette
const colors = {
  // Brand colors - Neon Spectrum
  brand: {
    primary: { h: 157, s: 100, l: 50 },      // #00FF9C - Neon Green
    secondary: { h: 187, s: 100, l: 50 },    // #00E0FF - Electric Cyan
    accent: { h: 331, s: 100, l: 50 },       // #FF007A - Matrix Magenta
    muted: { h: 157, s: 100, l: 10 },        // Dark Neon Tint
  },
  
  // Semantic colors (Technical variants)
  semantic: {
    success: { h: 157, s: 100, l: 50 },    // Neon Green
    warning: { h: 38, s: 92, l: 50 },       // Amber
    error: { h: 0, s: 84, l: 60 },          // Red
    info: { h: 187, s: 100, l: 50 },        // Cyan
  },
  
  // Deep Black Theme - Ultimate Contrast
  dark: {
    background: {
      base: { h: 0, s: 0, l: 2 },           // #050505 - Deep Black
      elevated: { h: 0, s: 0, l: 5 },       // #0D0D0D - Elevated
      surface: { h: 217, s: 15, l: 7 },     // #111418 - Technical Slate
      raised: { h: 0, s: 0, l: 8 },         // #141414 - Card Dark
      overlay: { h: 0, s: 0, l: 0, a: 0.85 }, // Heavy overlay
    },
    text: {
      primary: { h: 0, s: 0, l: 98 },       // #FAFAFA - Pure White
      secondary: { h: 0, s: 0, l: 65 },     // Medium Gray
      tertiary: { h: 0, s: 0, l: 45 },      // Muted Gray
      muted: { h: 0, s: 0, l: 30 },         // Dark Gray
      inverse: { h: 0, s: 0, l: 5 },        // Deep Black
    },
    border: {
      subtle: { h: 0, s: 0, l: 12 },        // #1F1F1F - Subtle
      light: { h: 157, s: 100, l: 20 },     // Neon Green Tint
      medium: { h: 0, s: 0, l: 18 },        // Medium
      focus: { h: 157, s: 100, l: 50 },     // Neon Green Focus
    },
  },

  // Pure White Theme - Light Mode Equivalent
  light: {
    background: {
      base: { h: 0, s: 0, l: 98 },           // Near White
      elevated: { h: 0, s: 0, l: 100 },      // Pure White
      surface: { h: 217, s: 15, l: 95 },     // Very Light Slate
      raised: { h: 0, s: 0, l: 96 },         // Card Light
      overlay: { h: 0, s: 0, l: 100, a: 0.85 }, // Light overlay
    },
    text: {
      primary: { h: 0, s: 0, l: 10 },       // Deep Black
      secondary: { h: 0, s: 0, l: 35 },     // Medium Dark Gray
      tertiary: { h: 0, s: 0, l: 50 },      // Muted Gray
      muted: { h: 0, s: 0, l: 65 },         // Light Gray
      inverse: { h: 0, s: 0, l: 98 },       // White
    },
    border: {
      subtle: { h: 0, s: 0, l: 90 },        // Subtle light border
      light: { h: 157, s: 100, l: 80 },     // Neon Green Tint
      medium: { h: 0, s: 0, l: 82 },        // Medium
      focus: { h: 157, s: 100, l: 50 },     // Neon Green Focus
    },
  },
};

// Helper function to convert HSL to string
export function hsl(color: { h: number; s: number; l: number }): string {
  return `hsl(${color.h}, ${color.s}%, ${color.l}%)`;
}

export function hsla(color: { h: number; s: number; l: number }, alpha: number): string {
  return `hsla(${color.h}, ${color.s}%, ${color.l}%, ${alpha})`;
}

// Get theme colors based on mode
export function getThemeColors(mode: ThemeMode = "dark") {
  let resolvedMode = mode;
  if (resolvedMode === "auto") {
    resolvedMode = typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  
  const theme = resolvedMode === "light" ? colors.light : colors.dark;
  
  return {
    isDark: resolvedMode === "dark",
    brand: colors.brand,
    semantic: colors.semantic,
    background: theme.background,
    text: theme.text,
    border: theme.border,
    
    // Gradients - Technical & Precise
    gradients: {
      primary: `linear-gradient(135deg, ${hsl(colors.brand.primary)} 0%, ${hsl(colors.brand.secondary)} 100%)`,
      technical: `linear-gradient(180deg, ${hsla(theme.background.elevated, 0.5)} 0%, ${hsla(theme.background.base, 0.5)} 100%)`,
      glow: `radial-gradient(circle at center, ${hsla(colors.brand.primary, 0.15)} 0%, transparent 70%)`,
    },
    
    // Shadows - Technical Depth
    shadows: {
      card: "0 4px 20px -5px rgba(0, 0, 0, 0.8)",
      elevated: "0 20px 40px -15px rgba(0, 0, 0, 0.9)",
      glow: `0 0 20px ${hsla(colors.brand.primary, 0.3)}`,
      cyan: `0 0 20px ${hsla(colors.brand.secondary, 0.3)}`,
    },
    
    // Transitions
    transitions: {
      fast: "150ms cubic-bezier(0.4, 0, 0.2, 1)",
      normal: "250ms cubic-bezier(0.4, 0, 0.2, 1)",
      slow: "350ms cubic-bezier(0.4, 0, 0.2, 1)",
      motion: "500ms cubic-bezier(0.2, 0.8, 0.2, 1)",
    },
  };
}

// Time-based greeting generator (Technical)
export function getGreeting(name: string): { text: string; emoji: string; status: string } {
  const hour = new Date().getHours();
  const base = name.split(' ')[0].toUpperCase();
  
  if (hour >= 5 && hour < 12) {
    return { text: `SYSTEM_INIT // MORNING_SYNC_COMPLETE: ${base}`, emoji: "⚙️", status: "READY" };
  } else if (hour >= 12 && hour < 17) {
    return { text: `PEAK_PHASE // AFTERNOON_OPTIMIZED: ${base}`, emoji: "⚡", status: "STABLE" };
  } else if (hour >= 17 && hour < 22) {
    return { text: `EVENING_CYCLE // DATA_GATHERING: ${base}`, emoji: "🌙", status: "ACTIVE" };
  } else {
    return { text: `NIGHT_WATCH // BACKGROUND_TASKS_RUNNING: ${base}`, emoji: "⭐", status: "SCANNING" };
  }
}

// Format user name from email or full name
export function formatUserName(identifier: string): string {
  if (identifier.includes("@")) {
    const localPart = identifier.split("@")[0];
    return localPart.replace(/[_-]/g, " ").toUpperCase();
  }
  return identifier.toUpperCase();
}

// Create CSS variables for theme
export function generateThemeCSS(mode: ThemeMode = "dark"): string {
  const colors = getThemeColors(mode);
  
  return `
    :root {
      --bg-base: ${hsl(colors.background.base)};
      --bg-elevated: ${hsl(colors.background.elevated)};
      --bg-surface: ${hsl(colors.background.surface)};
      --bg-raised: ${hsl(colors.background.raised)};
      
      --text-primary: ${hsl(colors.text.primary)};
      --text-secondary: ${hsl(colors.text.secondary)};
      --text-tertiary: ${hsl(colors.text.tertiary)};
      --text-muted: ${hsl(colors.text.muted)};
      
      --brand-primary: ${hsl(colors.brand.primary)};
      --brand-primary-light: ${hsl(colors.brand.secondary)};
      --brand-accent: ${hsl(colors.brand.accent)};
      
      --semantic-success: ${hsl(colors.semantic.success)};
      --semantic-warning: ${hsl(colors.semantic.warning)};
      --semantic-error: ${hsl(colors.semantic.error)};
      --semantic-info: ${hsl(colors.semantic.info)};
      
      --shadow-card: ${colors.shadows.card};
      --shadow-glow: ${colors.shadows.glow};
      
      --transition-fast: ${colors.transitions.fast};
      --transition-normal: ${colors.transitions.normal};
      --transition-slow: ${colors.transitions.slow};
      --transition-motion: ${colors.transitions.motion};
      
      --border-technical: 1px solid rgba(255, 255, 255, 0.1);
      --border-neon: 1px solid ${hsla(colors.brand.primary, 0.3)};
      --border-dotted: 1px dashed rgba(255, 255, 255, 0.2);
    }

    [data-theme="dark"] {
      background-color: var(--bg-base);
      color: var(--text-primary);
    }
  `;
}


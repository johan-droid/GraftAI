// Professional Theme System for GraftAI
// Blue + White (Light) | Black + White (Dark)

export type ThemeMode = "light" | "dark" | "auto";

// Professional Color Palette - Blue, White, Black
const colors = {
  // Brand colors - Professional Blue
  brand: {
    primary: { h: 217, s: 91, l: 60 },      // #2563eb - Royal Blue
    primaryLight: { h: 217, s: 91, l: 90 }, // #dbeafe - Light Blue
    primaryDark: { h: 217, s: 91, l: 40 },  // #1d4ed8 - Dark Blue
    accent: { h: 217, s: 91, l: 50 },       // #3b82f6 - Accent Blue
  },
  
  // Semantic colors
  semantic: {
    success: { h: 142, s: 76, l: 36 },    // #16a34a - Green
    warning: { h: 38, s: 92, l: 50 },       // #f59e0b - Orange
    error: { h: 0, s: 84, l: 60 },          // #dc2626 - Red
    info: { h: 217, s: 91, l: 60 },         // #2563eb - Blue
  },
  
  // Light theme - White background with Blue accents
  light: {
    background: {
      base: { h: 0, s: 0, l: 100 },         // #ffffff - Pure White
      elevated: { h: 0, s: 0, l: 98 },      // #fafafa - Off White
      surface: { h: 217, s: 33, l: 97 },    // #eff6ff - Blue-tinted White
      raised: { h: 0, s: 0, l: 100 },      // #ffffff - Card White
      overlay: { h: 0, s: 0, l: 0, a: 0.5 }, // Black overlay
    },
    text: {
      primary: { h: 0, s: 0, l: 10 },       // #1a1a1a - Near Black
      secondary: { h: 0, s: 0, l: 40 },     // #666666 - Dark Gray
      tertiary: { h: 0, s: 0, l: 60 },      // #999999 - Medium Gray
      muted: { h: 0, s: 0, l: 75 },         // #bfbfbf - Light Gray
      inverse: { h: 0, s: 0, l: 100 },     // #ffffff - White
    },
    border: {
      subtle: { h: 0, s: 0, l: 90 },       // #e6e6e6 - Very Light Gray
      light: { h: 217, s: 91, l: 90 },      // #dbeafe - Light Blue Border
      medium: { h: 0, s: 0, l: 80 },       // #cccccc - Medium Gray
      focus: { h: 217, s: 91, l: 60 },     // #2563eb - Blue Focus
    },
  },
  
  // Dark theme - Black background with White text
  dark: {
    background: {
      base: { h: 0, s: 0, l: 8 },          // #141414 - Deep Black
      elevated: { h: 0, s: 0, l: 12 },     // #1f1f1f - Elevated Black
      surface: { h: 217, s: 20, l: 15 },   // #1a2332 - Blue-tinted Dark
      raised: { h: 0, s: 0, l: 15 },       // #262626 - Card Dark
      overlay: { h: 0, s: 0, l: 0, a: 0.7 }, // Dark overlay
    },
    text: {
      primary: { h: 0, s: 0, l: 98 },      // #fafafa - Near White
      secondary: { h: 0, s: 0, l: 70 },    // #b3b3b3 - Light Gray
      tertiary: { h: 0, s: 0, l: 50 },     // #808080 - Medium Gray
      muted: { h: 0, s: 0, l: 35 },        // #595959 - Dark Gray
      inverse: { h: 0, s: 0, l: 10 },     // #1a1a1a - Black
    },
    border: {
      subtle: { h: 0, s: 0, l: 20 },       // #333333 - Dark Gray
      light: { h: 217, s: 91, l: 40 },      // #1d4ed8 - Dark Blue
      medium: { h: 0, s: 0, l: 30 },       // #4d4d4d - Medium Border
      focus: { h: 217, s: 91, l: 60 },     // #2563eb - Blue Focus
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
export function getThemeColors(mode: ThemeMode) {
  const isDark = mode === "dark" || (mode === "auto" && typeof window !== "undefined" 
    ? window.matchMedia("(prefers-color-scheme: dark)").matches 
    : true);
  
  const theme = isDark ? colors.dark : colors.light;
  
  return {
    isDark,
    brand: colors.brand,
    semantic: colors.semantic,
    background: theme.background,
    text: theme.text,
    border: theme.border,
    
    // Gradients
    gradients: {
      primary: `linear-gradient(135deg, hsl(${colors.brand.primary.h}, ${colors.brand.primary.s}%, ${colors.brand.primary.l}%) 0%, hsl(${colors.brand.accent.h}, ${colors.brand.accent.s}%, ${colors.brand.accent.l}%) 100%)`,
      card: isDark 
        ? `linear-gradient(135deg, ${hsla(theme.background.elevated, 0.9)} 0%, ${hsla(theme.background.surface, 0.95)} 100%)`
        : `linear-gradient(135deg, ${hsl(theme.background.elevated)} 0%, ${hsl(theme.background.surface)} 100%)`,
    },
    
    // Shadows
    shadows: {
      card: isDark 
        ? "0 10px 30px -10px rgba(0, 0, 0, 0.5)"
        : "0 10px 30px -10px rgba(0, 0, 0, 0.1)",
      elevated: isDark
        ? "0 25px 50px -12px rgba(0, 0, 0, 0.5)"
        : "0 25px 50px -12px rgba(0, 0, 0, 0.15)",
      glow: isDark
        ? `0 0 30px ${hsla(colors.brand.primary, 0.3)}`
        : `0 0 30px ${hsla(colors.brand.primary, 0.2)}`,
    },
    
    // Transitions
    transitions: {
      fast: "150ms cubic-bezier(0.4, 0, 0.2, 1)",
      normal: "250ms cubic-bezier(0.4, 0, 0.2, 1)",
      slow: "350ms cubic-bezier(0.4, 0, 0.2, 1)",
    },
  };
}

// Time-based greeting generator
export function getGreeting(name: string): { text: string; emoji: string } {
  const hour = new Date().getHours();
  
  if (hour >= 5 && hour < 12) {
    return { text: `Good morning, ${name}`, emoji: "☀️" };
  } else if (hour >= 12 && hour < 17) {
    return { text: `Good afternoon, ${name}`, emoji: "🌤️" };
  } else if (hour >= 17 && hour < 22) {
    return { text: `Good evening, ${name}`, emoji: "🌙" };
  } else {
    return { text: `Good night, ${name}`, emoji: "⭐" };
  }
}

// Format user name from email or full name
export function formatUserName(identifier: string): string {
  // If it's an email, extract the local part
  if (identifier.includes("@")) {
    const localPart = identifier.split("@")[0];
    // Convert camelCase or snake_case to readable
    return localPart
      .replace(/([a-z])([A-Z])/g, "$1 $2")
      .replace(/[_-]/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
  
  // If it's already a name, just ensure proper capitalization
  return identifier.replace(/\b\w/g, (c) => c.toUpperCase());
}

// Create CSS variables for theme
export function generateThemeCSS(mode: ThemeMode): string {
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
      --brand-primary-light: ${hsl(colors.brand.primaryLight)};
      --brand-primary-dark: ${hsl(colors.brand.primaryDark)};
      --brand-accent: ${hsl(colors.brand.accent)};
      
      --semantic-success: ${hsl(colors.semantic.success)};
      --semantic-warning: ${hsl(colors.semantic.warning)};
      --semantic-error: ${hsl(colors.semantic.error)};
      --semantic-info: ${hsl(colors.semantic.info)};
      
      --shadow-card: ${colors.shadows.card};
      --shadow-elevated: ${colors.shadows.elevated};
      --shadow-glow: ${colors.shadows.glow};
      
      --transition-fast: ${colors.transitions.fast};
      --transition-normal: ${colors.transitions.normal};
      --transition-slow: ${colors.transitions.slow};
    }
  `;
}

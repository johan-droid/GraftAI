/**
 * Material Design 3 (M3) Design Tokens
 * 
 * Following Google's Material Design 3 specification for:
 * - Color system (primary, secondary, tertiary, error, surface)
 * - Typography scale (display, headline, title, body, label)
 * - Elevation (surface levels, shadows)
 * - Shape (corner radius)
 * - State (hover, focus, pressed, dragged)
 * 
 * @see https://m3.material.io/styles/color/the-color-system/tokens
 */

// ============================================================================
// COLOR TOKENS
// ============================================================================

export const m3Colors = {
  // Primary palette - Google Blue
  primary: {
    0: '#000000',
    10: '#001D35',
    20: '#003257',
    30: '#004878',
    40: '#1A73E8', // Primary
    50: '#5B9BD5',
    60: '#8AB4F8',
    70: '#AAC7FF',
    80: '#D3E3FD',
    90: '#E8F0FE',
    95: '#EEF4FF',
    99: '#FDFBFF',
    100: '#FFFFFF',
  },
  
  // Secondary palette - Teal
  secondary: {
    0: '#000000',
    10: '#00201F',
    20: '#003735',
    30: '#00504C',
    40: '#00BFA5', // Secondary
    50: '#00A693',
    60: '#00D9BB',
    70: '#00E5CD',
    80: '#00F2D8',
    90: '#B2DFDB',
    95: '#E0F2F1',
    99: '#F2FFFD',
    100: '#FFFFFF',
  },
  
  // Tertiary palette - Purple
  tertiary: {
    0: '#000000',
    10: '#311034',
    20: '#4E2552',
    30: '#693A6E',
    40: '#9334E6', // Tertiary
    50: '#B07AD4',
    60: '#CE93D8',
    70: '#E0B0E8',
    80: '#EDC7F2',
    90: '#F3E5F5',
    95: '#FAF0FB',
    99: '#FFFBFF',
    100: '#FFFFFF',
  },
  
  // Error palette - Red
  error: {
    0: '#000000',
    10: '#410002',
    20: '#690005',
    30: '#93000A',
    40: '#EA4335', // Error
    50: '#DE3730',
    60: '#FF5449',
    70: '#FF897D',
    80: '#FFB4AB',
    90: '#FFDAD6',
    95: '#FFEDEA',
    99: '#FFFBFF',
    100: '#FFFFFF',
  },
  
  // Neutral palette - Gray
  neutral: {
    0: '#000000',
    4: '#0F0F10',
    6: '#141415',
    10: '#1C1B1F',
    12: '#211F26',
    17: '#2B2930',
    20: '#313033',
    22: '#36343B',
    24: '#3B383E',
    30: '#484649',
    40: '#605D62',
    50: '#787579',
    60: '#939094',
    70: '#AEAAAE',
    80: '#C9C5CA',
    87: '#DEDBE0',
    90: '#E6E1E5',
    92: '#EBE6EB',
    94: '#F0EDF1',
    95: '#F2EFF4',
    96: '#F5F2F7',
    98: '#FAF8FD',
    99: '#FFFBFE',
    100: '#FFFFFF',
  },
  
  // Neutral variant - Slightly tinted gray
  neutralVariant: {
    0: '#000000',
    10: '#1D1A22',
    20: '#322F37',
    30: '#49454F',
    40: '#605D66',
    50: '#79747E',
    60: '#938F99',
    70: '#AEA9B4',
    80: '#CAC4D0',
    90: '#E7E0EC',
    95: '#F5EEFA',
    99: '#FFFBFE',
    100: '#FFFFFF',
  },
} as const;

// ============================================================================
// LIGHT THEME - M3 COLOR ROLES
// ============================================================================

export const m3LightTheme = {
  // Primary colors
  primary: m3Colors.primary[40],
  onPrimary: m3Colors.primary[100],
  primaryContainer: m3Colors.primary[90],
  onPrimaryContainer: m3Colors.primary[10],
  
  // Secondary colors
  secondary: m3Colors.secondary[40],
  onSecondary: m3Colors.secondary[100],
  secondaryContainer: m3Colors.secondary[90],
  onSecondaryContainer: m3Colors.secondary[10],
  
  // Tertiary colors
  tertiary: m3Colors.tertiary[40],
  onTertiary: m3Colors.tertiary[100],
  tertiaryContainer: m3Colors.tertiary[90],
  onTertiaryContainer: m3Colors.tertiary[10],
  
  // Error colors
  error: m3Colors.error[40],
  onError: m3Colors.error[100],
  errorContainer: m3Colors.error[90],
  onErrorContainer: m3Colors.error[10],
  
  // Surface colors with elevation levels
  surface: m3Colors.neutral[99],
  onSurface: m3Colors.neutral[10],
  surfaceVariant: m3Colors.neutralVariant[90],
  onSurfaceVariant: m3Colors.neutralVariant[30],
  
  // Surface containers (M3 elevation levels)
  surfaceContainerLowest: m3Colors.neutral[100],
  surfaceContainerLow: m3Colors.neutral[98],
  surfaceContainer: m3Colors.neutral[94],
  surfaceContainerHigh: m3Colors.neutral[92],
  surfaceContainerHighest: m3Colors.neutral[90],
  surfaceDim: m3Colors.neutral[87],
  surfaceBright: m3Colors.neutral[98],
  
  // Inverse colors
  inverseSurface: m3Colors.neutral[20],
  inverseOnSurface: m3Colors.neutral[95],
  inversePrimary: m3Colors.primary[80],
  
  // Outline
  outline: m3Colors.neutralVariant[50],
  outlineVariant: m3Colors.neutralVariant[80],
  
  // Scrim (modal backdrop)
  scrim: m3Colors.neutral[0],
  
  // Shadow
  shadow: m3Colors.neutral[0],
} as const;

// ============================================================================
// DARK THEME - M3 COLOR ROLES
// ============================================================================

export const m3DarkTheme = {
  // Primary colors (lighter in dark mode)
  primary: m3Colors.primary[80],
  onPrimary: m3Colors.primary[20],
  primaryContainer: m3Colors.primary[30],
  onPrimaryContainer: m3Colors.primary[90],
  
  // Secondary colors
  secondary: m3Colors.secondary[80],
  onSecondary: m3Colors.secondary[20],
  secondaryContainer: m3Colors.secondary[30],
  onSecondaryContainer: m3Colors.secondary[90],
  
  // Tertiary colors
  tertiary: m3Colors.tertiary[80],
  onTertiary: m3Colors.tertiary[20],
  tertiaryContainer: m3Colors.tertiary[30],
  onTertiaryContainer: m3Colors.tertiary[90],
  
  // Error colors
  error: m3Colors.error[80],
  onError: m3Colors.error[20],
  errorContainer: m3Colors.error[30],
  onErrorContainer: m3Colors.error[90],
  
  // Surface colors (darker in dark mode)
  surface: m3Colors.neutral[6],
  onSurface: m3Colors.neutral[90],
  surfaceVariant: m3Colors.neutralVariant[30],
  onSurfaceVariant: m3Colors.neutralVariant[80],
  
  // Surface containers
  surfaceContainerLowest: m3Colors.neutral[4],
  surfaceContainerLow: m3Colors.neutral[10],
  surfaceContainer: m3Colors.neutral[12],
  surfaceContainerHigh: m3Colors.neutral[17],
  surfaceContainerHighest: m3Colors.neutral[22],
  surfaceDim: m3Colors.neutral[6],
  surfaceBright: m3Colors.neutral[24],
  
  // Inverse colors
  inverseSurface: m3Colors.neutral[90],
  inverseOnSurface: m3Colors.neutral[20],
  inversePrimary: m3Colors.primary[40],
  
  // Outline
  outline: m3Colors.neutralVariant[60],
  outlineVariant: m3Colors.neutralVariant[30],
  
  // Scrim
  scrim: m3Colors.neutral[0],
  
  // Shadow
  shadow: m3Colors.neutral[0],
} as const;

// ============================================================================
// TYPOGRAPHY TOKENS
// ============================================================================

export const m3Typography = {
  // Font families
  fontFamily: {
    brand: '"Google Sans", "Plus Jakarta Sans", system-ui, sans-serif',
    plain: '"Roboto", "Plus Jakarta Sans", system-ui, sans-serif',
  },
  
  // Type scale
  scale: {
    // Display - Largest text, short content
    display: {
      large: { size: '57px', lineHeight: '64px', letterSpacing: '-0.25px', weight: 400 },
      medium: { size: '45px', lineHeight: '52px', letterSpacing: '0', weight: 400 },
      small: { size: '36px', lineHeight: '44px', letterSpacing: '0', weight: 400 },
    },
    
    // Headline - Medium-emphasis, long content
    headline: {
      large: { size: '32px', lineHeight: '40px', letterSpacing: '0', weight: 400 },
      medium: { size: '28px', lineHeight: '36px', letterSpacing: '0', weight: 400 },
      small: { size: '24px', lineHeight: '32px', letterSpacing: '0', weight: 400 },
    },
    
    // Title - Smaller than headline, medium emphasis
    title: {
      large: { size: '22px', lineHeight: '28px', letterSpacing: '0', weight: 400 },
      medium: { size: '16px', lineHeight: '24px', letterSpacing: '0.15px', weight: 500 },
      small: { size: '14px', lineHeight: '20px', letterSpacing: '0.1px', weight: 500 },
    },
    
    // Body - Long-form writing
    body: {
      large: { size: '16px', lineHeight: '24px', letterSpacing: '0.5px', weight: 400 },
      medium: { size: '14px', lineHeight: '20px', letterSpacing: '0.25px', weight: 400 },
      small: { size: '12px', lineHeight: '16px', letterSpacing: '0.4px', weight: 400 },
    },
    
    // Label - Buttons, captions, overlines
    label: {
      large: { size: '14px', lineHeight: '20px', letterSpacing: '0.1px', weight: 500 },
      medium: { size: '12px', lineHeight: '16px', letterSpacing: '0.5px', weight: 500 },
      small: { size: '11px', lineHeight: '16px', letterSpacing: '0.5px', weight: 500 },
    },
  },
} as const;

// ============================================================================
// SHAPE (CORNER RADIUS) TOKENS
// ============================================================================

export const m3Shape = {
  // Corner sizes
  corner: {
    none: '0px',
    extraSmall: '4px',
    small: '8px',
    medium: '12px',
    large: '16px',
    extraLarge: '28px',
    full: '50%',
  },
  
  // Component-specific shapes
  components: {
    // Small components
    chip: '8px',
    iconButton: '50%',
    checkbox: '2px',
    radioButton: '50%',
    switch: '50%',
    
    // Medium components
    button: '20px', // Pill shape for filled buttons
    card: '12px',
    textField: '4px',
    menu: '4px',
    tooltip: '4px',
    snackbar: '4px',
    
    // Large components
    dialog: '28px',
    bottomSheet: '28px 28px 0 0', // Top corners only
    navigationDrawer: '0px',
    navigationRail: '0px',
    
    // Full-screen
    fullScreenDialog: '0px',
    searchView: '0px',
    searchBar: '32px',
  },
} as const;

// ============================================================================
// ELEVATION & SHADOW TOKENS
// ============================================================================

export const m3Elevation = {
  // Surface tint (color overlay for elevation)
  surfaceTint: m3Colors.primary[40],
  
  // Shadow opacity values
  shadowOpacity: {
    umbra: 0.2,    // Key shadow
    penumbra: 0.14, // Ambient shadow
    ambient: 0.12,   // Ambient shadow
  },
  
  // DP levels with opacity multipliers
  levels: {
    level0: { dp: 0, opacity: 0 },
    level1: { dp: 1, opacity: 0.05 },
    level2: { dp: 3, opacity: 0.08 },
    level3: { dp: 6, opacity: 0.11 },
    level4: { dp: 8, opacity: 0.12 },
    level5: { dp: 12, opacity: 0.14 },
  },
  
  // Component elevations
  components: {
    appBar: 0,
    bottomNav: 3,
    bottomSheet: 1,
    card: 1,
    cardHovered: 3,
    dialog: 3,
    fab: 3,
    fabPressed: 6,
    menu: 2,
    navigationDrawer: 0,
    navigationRail: 0,
    searchBar: 0,
    snackbar: 3,
    switch: 1,
    tooltip: 2,
  },
} as const;

// ============================================================================
// STATE TOKENS (Opacity overlays)
// ============================================================================

export const m3State = {
  // Container opacity
  container: {
    hover: 0.08,
    focus: 0.12,
    pressed: 0.12,
    dragged: 0.16,
  },
  
  // Content opacity
  content: {
    hover: 0.08,
    focus: 1,
    pressed: 0.12,
    dragged: 0.16,
  },
  
  // Disabled state
  disabled: {
    container: 0.12,
    content: 0.38,
  },
  
  // Focus ring
  focusRing: {
    width: '2px',
    gap: '2px',
  },
} as const;

// ============================================================================
// MOTION TOKENS
// ============================================================================

export const m3Motion = {
  // Duration tokens
  duration: {
    instant: '0ms',
    fast: '150ms',
    medium: '300ms',
    slow: '500ms',
  },
  
  // Easing curves
  easing: {
    linear: 'linear',
    standard: 'cubic-bezier(0.2, 0.0, 0.0, 1.0)',
    decelerate: 'cubic-bezier(0.0, 0.0, 0.0, 1.0)',
    accelerate: 'cubic-bezier(0.3, 0.0, 0.8, 0.15)',
    emphasized: 'cubic-bezier(0.2, 0.0, 0.0, 1.0)',
    emphasizedDecelerate: 'cubic-bezier(0.05, 0.7, 0.1, 1.0)',
    emphasizedAccelerate: 'cubic-bezier(0.3, 0.0, 0.8, 0.15)',
  },
  
  // Component-specific transitions
  components: {
    // Navigation
    drawer: { duration: '300ms', easing: 'emphasized' },
    rail: { duration: '300ms', easing: 'emphasized' },
    bottomNav: { duration: '150ms', easing: 'standard' },
    
    // Surfaces
    dialog: { duration: '300ms', easing: 'emphasized' },
    bottomSheet: { duration: '300ms', easing: 'emphasized' },
    menu: { duration: '150ms', easing: 'standard' },
    snackbar: { duration: '150ms', easing: 'standard' },
    tooltip: { duration: '75ms', easing: 'standard' },
    
    // Selection
    chip: { duration: '100ms', easing: 'standard' },
    switch: { duration: '100ms', easing: 'standard' },
    checkbox: { duration: '100ms', easing: 'standard' },
    radio: { duration: '100ms', easing: 'standard' },
    
    // Feedback
    ripple: { duration: '300ms', easing: 'standard' },
    progress: { duration: '2000ms', easing: 'linear' },
  },
} as const;

// ============================================================================
// SPACING TOKENS
// ============================================================================

export const m3Spacing = {
  // Base grid
  grid: 8,
  
  // Spacing scale
  scale: {
    0: '0px',
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    5: '20px',
    6: '24px',
    7: '28px',
    8: '32px',
    9: '36px',
    10: '40px',
    11: '44px',
    12: '48px',
    13: '52px',
    14: '56px',
    15: '60px',
    16: '64px',
  },
  
  // Touch targets (minimum 48dp)
  touchTarget: {
    min: '48px',
    comfortable: '56px',
    spacious: '64px',
  },
  
  // Component padding
  padding: {
    small: '8px',
    medium: '16px',
    large: '24px',
  },
} as const;

// ============================================================================
// BREAKPOINTS
// ============================================================================

export const m3Breakpoints = {
  // Material Design 3 breakpoints
  compact: { min: 0, max: 599 },      // Mobile portrait
  medium: { min: 600, max: 839 },    // Mobile landscape/tablet
  expanded: { min: 840, max: 1199 }, // Tablet/desktop
  large: { min: 1200, max: 1599 },   // Large desktop
  extraLarge: { min: 1600, max: null }, // Extra large desktop
  
  // Common device sizes for reference
  mobile: { width: 360, height: 800 },
  mobileLarge: { width: 414, height: 896 },
  tablet: { width: 744, height: 1133 }, // iPad Mini
  tabletLarge: { width: 834, height: 1194 }, // iPad Pro 11"
  desktop: { width: 1440, height: 900 },
} as const;

// ============================================================================
// LAYOUT TOKENS
// ============================================================================

export const m3Layout = {
  // Margins by breakpoint
  margin: {
    compact: '16px',   // Mobile
    medium: '24px',    // Tablet
    expanded: '32px',  // Desktop
  },
  
  // Column count by breakpoint
  columns: {
    compact: 4,   // Mobile: 4-column grid
    medium: 8,    // Tablet: 8-column grid
    expanded: 12, // Desktop: 12-column grid
  },
  
  // Gutter width
  gutter: {
    compact: '16px',
    medium: '24px',
    expanded: '24px',
  },
  
  // Max content width
  maxWidth: {
    content: '1200px',
    text: '65ch', // Optimal reading width
  },
} as const;

// ============================================================================
// COMPONENT-SPECIFIC TOKENS
// ============================================================================

export const m3ComponentTokens = {
  // App Bar
  appBar: {
    height: {
      compact: '56px',   // Mobile
      medium: '64px',    // Desktop
      large: '80px',     // Extended
    },
  },
  
  // Bottom Navigation
  bottomNav: {
    height: '80px',
    itemMinWidth: '80px',
    itemMaxWidth: '168px',
    activeIndicatorHeight: '32px',
  },
  
  // Navigation Rail
  rail: {
    width: '80px',
    itemHeight: '56px',
  },
  
  // Navigation Drawer
  drawer: {
    width: '360px',
    modalWidth: '360px',
    standardWidth: '360px',
  },
  
  // FAB
  fab: {
    size: {
      small: '40px',
      default: '56px',
      large: '96px',
    },
    iconSize: {
      small: '24px',
      default: '24px',
      large: '36px',
    },
  },
  
  // Cards
  card: {
    padding: {
      small: '8px',
      medium: '16px',
    },
  },
  
  // Buttons
  button: {
    height: {
      small: '32px',
      medium: '40px',
      large: '48px',
    },
    minWidth: {
      small: '48px',
      medium: '64px',
      large: '80px',
    },
    iconSize: '18px',
  },
  
  // Chips
  chip: {
    height: '32px',
    iconSize: '18px',
    avatarSize: '24px',
  },
  
  // List
  list: {
    itemHeight: {
      oneLine: '48px',
      twoLine: '64px',
      threeLine: '88px',
    },
    iconSize: '24px',
    iconMargin: '16px',
  },
  
  // Dialog
  dialog: {
    minWidth: '280px',
    maxWidth: '560px',
    margin: '24px',
  },
  
  // Bottom Sheet
  bottomSheet: {
    minWidth: '0',
    maxWidth: '640px',
    handleHeight: '24px',
    handleWidth: '32px',
  },
  
  // Snackbar
  snackbar: {
    minWidth: '288px',
    maxWidth: '568px',
    height: '48px',
  },
  
  // Tooltip
  tooltip: {
    height: '24px',
    minWidth: '40px',
    maxWidth: '200px',
  },
  
  // Menu
  menu: {
    minWidth: '112px',
    maxWidth: '280px',
  },
} as const;

// ============================================================================
// EXPORT ALL TOKENS
// ============================================================================

export const m3Tokens = {
  colors: m3Colors,
  light: m3LightTheme,
  dark: m3DarkTheme,
  typography: m3Typography,
  shape: m3Shape,
  elevation: m3Elevation,
  state: m3State,
  motion: m3Motion,
  spacing: m3Spacing,
  breakpoints: m3Breakpoints,
  layout: m3Layout,
  components: m3ComponentTokens,
} as const;

export default m3Tokens;

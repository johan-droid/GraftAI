/**
 * Responsive Breakpoints Configuration
 * 
 * Material Design 3 breakpoints for adaptive layouts
 * @see https://m3.material.io/foundations/layout/applying-layout
 */

import { useEffect, useState } from 'react';

// ============================================================================
// M3 BREAKPOINT DEFINITIONS
// ============================================================================

export type Breakpoint = 'compact' | 'medium' | 'expanded' | 'large' | 'extraLarge';

export interface BreakpointRange {
  min: number;
  max: number | null;
}

export const breakpoints: Record<Breakpoint, BreakpointRange> = {
  // Mobile phones (portrait)
  compact: { min: 0, max: 599 },
  
  // Mobile phones (landscape) / Small tablets
  medium: { min: 600, max: 839 },
  
  // Tablets / Small laptops
  expanded: { min: 840, max: 1199 },
  
  // Desktops
  large: { min: 1200, max: 1599 },
  
  // Large desktops
  extraLarge: { min: 1600, max: null },
};

// ============================================================================
// LAYOUT CONFIGURATION BY BREAKPOINT
// ============================================================================

export interface LayoutConfig {
  // Navigation type
  navigation: 'bottom' | 'rail' | 'drawer';
  
  // Layout grid
  columns: number;
  margin: number;
  gutter: number;
  
  // Content constraints
  maxContentWidth: string;
  
  // Touch targets
  touchTargetSize: number;
  
  // Component adaptations
  showLabels: boolean;
  dense: boolean;
}

export const layoutConfigs: Record<Breakpoint, LayoutConfig> = {
  compact: {
    navigation: 'bottom',
    columns: 4,
    margin: 16,
    gutter: 16,
    maxContentWidth: '100%',
    touchTargetSize: 48,
    showLabels: true,
    dense: true,
  },
  
  medium: {
    navigation: 'rail',
    columns: 8,
    margin: 24,
    gutter: 24,
    maxContentWidth: '100%',
    touchTargetSize: 48,
    showLabels: true,
    dense: false,
  },
  
  expanded: {
    navigation: 'drawer',
    columns: 12,
    margin: 32,
    gutter: 24,
    maxContentWidth: '1200px',
    touchTargetSize: 48,
    showLabels: true,
    dense: false,
  },
  
  large: {
    navigation: 'drawer',
    columns: 12,
    margin: 200, // Centered content
    gutter: 24,
    maxContentWidth: '1200px',
    touchTargetSize: 48,
    showLabels: true,
    dense: false,
  },
  
  extraLarge: {
    navigation: 'drawer',
    columns: 12,
    margin: 200,
    gutter: 24,
    maxContentWidth: '1400px',
    touchTargetSize: 48,
    showLabels: true,
    dense: false,
  },
};

// ============================================================================
// REACTIVE HOOK
// ============================================================================

export function useBreakpoint(): Breakpoint {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>('compact');
  
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      
      if (width >= breakpoints.extraLarge.min) {
        setBreakpoint('extraLarge');
      } else if (width >= breakpoints.large.min) {
        setBreakpoint('large');
      } else if (width >= breakpoints.expanded.min) {
        setBreakpoint('expanded');
      } else if (width >= breakpoints.medium.min) {
        setBreakpoint('medium');
      } else {
        setBreakpoint('compact');
      }
    };
    
    // Initial check
    handleResize();
    
    // Listen for resize
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return breakpoint;
}

export function useLayoutConfig(): LayoutConfig {
  const breakpoint = useBreakpoint();
  return layoutConfigs[breakpoint];
}

// ============================================================================
// MEDIA QUERY HELPERS
// ============================================================================

export const mediaQueries = {
  compact: '(max-width: 599px)',
  medium: '(min-width: 600px) and (max-width: 839px)',
  expanded: '(min-width: 840px) and (max-width: 1199px)',
  large: '(min-width: 1200px) and (max-width: 1599px)',
  extraLarge: '(min-width: 1600px)',
  
  // Common groups
  mobile: '(max-width: 599px)',
  tablet: '(min-width: 600px) and (max-width: 839px)',
  desktop: '(min-width: 840px)',
  
  // Touch targets
  coarsePointer: '(pointer: coarse)',
  finePointer: '(pointer: fine)',
  
  // Reduced motion
  reducedMotion: '(prefers-reduced-motion: reduce)',
};

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);
  
  useEffect(() => {
    const media = window.matchMedia(query);
    
    const updateMatch = () => setMatches(media.matches);
    updateMatch();
    
    media.addEventListener('change', updateMatch);
    return () => media.removeEventListener('change', updateMatch);
  }, [query]);
  
  return matches;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export function isCompact(breakpoint: Breakpoint): boolean {
  return breakpoint === 'compact';
}

export function isMobile(breakpoint: Breakpoint): boolean {
  return breakpoint === 'compact' || breakpoint === 'medium';
}

export function isTablet(breakpoint: Breakpoint): boolean {
  return breakpoint === 'medium' || breakpoint === 'expanded';
}

export function isDesktop(breakpoint: Breakpoint): boolean {
  return breakpoint === 'expanded' || breakpoint === 'large' || breakpoint === 'extraLarge';
}

export function getColumns(breakpoint: Breakpoint): number {
  return layoutConfigs[breakpoint].columns;
}

export function getMargin(breakpoint: Breakpoint): number {
  return layoutConfigs[breakpoint].margin;
}

export function getGutter(breakpoint: Breakpoint): number {
  return layoutConfigs[breakpoint].gutter;
}

// ============================================================================
// CSS CUSTOM PROPERTIES GENERATOR
// ============================================================================

export function generateCSSVariables(breakpoint: Breakpoint): Record<string, string> {
  const config = layoutConfigs[breakpoint];
  
  return {
    '--m3-breakpoint': breakpoint,
    '--m3-columns': String(config.columns),
    '--m3-margin': `${config.margin}px`,
    '--m3-gutter': `${config.gutter}px`,
    '--m3-max-content-width': config.maxContentWidth,
    '--m3-touch-target': `${config.touchTargetSize}px`,
  };
}

// ============================================================================
// TAILWIND CONFIG EXTENSION
// ============================================================================

export const tailwindBreakpointConfig = {
  screens: {
    // M3 breakpoints
    'compact': { 'max': '599px' },
    'medium': { 'min': '600px', 'max': '839px' },
    'expanded': { 'min': '840px', 'max': '1199px' },
    'large': { 'min': '1200px', 'max': '1599px' },
    'extra-large': { 'min': '1600px' },
    
    // Common groupings
    'mobile': { 'max': '599px' },
    'tablet': { 'min': '600px', 'max': '839px' },
    'desktop': { 'min': '840px' },
    
    // Legacy compatibility
    'sm': '600px',
    'md': '840px',
    'lg': '1200px',
    'xl': '1600px',
  },
};

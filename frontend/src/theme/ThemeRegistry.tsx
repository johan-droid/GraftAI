'use client';

import * as React from 'react';
import { useMemo } from 'react';
import { ThemeProvider as MuiThemeProvider, createTheme, alpha } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AppRouterCacheProvider } from '@mui/material-nextjs/v14-appRouter';
import { useTheme as useAppTheme } from '@/contexts/ThemeContext';

function createAppTheme(isDark: boolean) {
  const primary = isDark ? '#8AB4F8' : '#1A73E8';
  const surface = isDark ? '#17181C' : '#FFFFFF';
  const background = isDark ? '#0F1115' : '#F8F9FA';
  const textPrimary = isDark ? '#E8EAED' : '#202124';
  const textSecondary = isDark ? '#BDC1C6' : '#5F6368';
  const divider = isDark ? 'rgba(255,255,255,0.08)' : '#DADCE0';
  const hover = isDark ? 'rgba(255,255,255,0.06)' : '#F1F3F4';
  const selected = isDark ? alpha('#8AB4F8', 0.18) : '#E8F0FE';
  const selectedText = isDark ? '#8AB4F8' : '#1967D2';

  return createTheme({
    palette: {
      mode: isDark ? 'dark' : 'light',
      primary: {
        main: primary,
        light: isDark ? '#AECBFA' : '#4285F4',
        dark: isDark ? '#5E97F6' : '#1558B0',
        contrastText: isDark ? '#0F1115' : '#FFFFFF',
      },
      secondary: {
        main: isDark ? '#81C995' : '#34A853',
      },
      error: {
        main: isDark ? '#F28B82' : '#D93025',
      },
      warning: {
        main: isDark ? '#FDD663' : '#F9AB00',
      },
      success: {
        main: isDark ? '#81C995' : '#1E8E3E',
      },
      info: {
        main: isDark ? '#8AB4F8' : '#1A73E8',
      },
      background: {
        default: background,
        paper: surface,
      },
      text: {
        primary: textPrimary,
        secondary: textSecondary,
      },
      divider,
    },
    typography: {
      fontFamily: '"Plus Jakarta Sans", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: {
        fontWeight: 700,
        fontSize: '3rem',
        letterSpacing: '-0.03em',
      },
      h2: {
        fontWeight: 700,
        fontSize: '2.25rem',
        letterSpacing: '-0.03em',
      },
      h3: {
        fontWeight: 600,
        fontSize: '1.875rem',
        letterSpacing: '-0.02em',
      },
      h4: {
        fontWeight: 600,
        fontSize: '1.5rem',
      },
      h5: {
        fontWeight: 600,
        fontSize: '1.25rem',
      },
      h6: {
        fontWeight: 600,
        fontSize: '1rem',
      },
      button: {
        fontWeight: 600,
        textTransform: 'none',
      },
    },
    shape: {
      borderRadius: 20,
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: background,
            color: textPrimary,
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            border: `1px solid ${divider}`,
            boxShadow: isDark
              ? '0 18px 40px -28px rgba(0,0,0,0.6)'
              : '0 18px 50px -35px rgba(32, 33, 36, 0.28)',
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: 28,
            border: `1px solid ${divider}`,
            backgroundImage: 'none',
            boxShadow: isDark
              ? '0 32px 60px -24px rgba(0,0,0,0.75)'
              : '0 24px 60px -36px rgba(32,33,36,0.35)',
          },
        },
      },
      MuiBackdrop: {
        styleOverrides: {
          root: {
            backgroundColor: isDark ? 'rgba(15,17,21,0.68)' : 'rgba(60,64,67,0.32)',
            backdropFilter: 'blur(3px)',
          },
        },
      },
      MuiDialogTitle: {
        styleOverrides: {
          root: {
            padding: '24px 24px 16px',
            fontWeight: 700,
            letterSpacing: '-0.02em',
            color: textPrimary,
          },
        },
      },
      MuiDialogContent: {
        styleOverrides: {
          root: {
            padding: '0 24px 24px',
            color: textPrimary,
          },
        },
      },
      MuiDialogActions: {
        styleOverrides: {
          root: {
            padding: '0 24px 24px',
            gap: 12,
          },
        },
      },
      MuiMenu: {
        styleOverrides: {
          paper: {
            marginTop: 8,
            borderRadius: 20,
            border: `1px solid ${divider}`,
            boxShadow: isDark
              ? '0 22px 40px -24px rgba(0,0,0,0.65)'
              : '0 24px 60px -38px rgba(32,33,36,0.28)',
            padding: 6,
            backgroundImage: 'none',
          },
          list: {
            padding: 0,
          },
        },
      },
      MuiPopover: {
        styleOverrides: {
          paper: {
            borderRadius: 20,
            border: `1px solid ${divider}`,
            boxShadow: isDark
              ? '0 22px 40px -24px rgba(0,0,0,0.65)'
              : '0 24px 60px -38px rgba(32,33,36,0.28)',
            backgroundImage: 'none',
          },
        },
      },
      MuiMenuItem: {
        styleOverrides: {
          root: {
            minHeight: 44,
            borderRadius: 12,
            margin: '2px 6px',
            transition: 'background-color 150ms ease, color 150ms ease',
            '&:hover': {
              backgroundColor: hover,
            },
            '&.Mui-selected': {
              backgroundColor: selected,
              color: selectedText,
              '&:hover': {
                backgroundColor: selected,
              },
            },
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            backgroundColor: surface,
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: divider,
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: isDark ? '#8AB4F8' : '#BDC1C6',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: primary,
              borderWidth: 1.5,
            },
          },
          input: {
            padding: '12px 14px',
            color: textPrimary,
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiInputLabel-root': {
              color: textSecondary,
            },
            '& .MuiInputLabel-root.Mui-focused': {
              color: primary,
            },
          },
        },
      },
      MuiSelect: {
        styleOverrides: {
          select: {
            paddingTop: 12,
            paddingBottom: 12,
          },
          icon: {
            color: textSecondary,
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 999,
            fontWeight: 600,
            textTransform: 'none',
          },
          contained: {
            boxShadow: isDark
              ? '0 8px 20px -10px rgba(0,0,0,0.45)'
              : '0 10px 24px -12px rgba(26,115,232,0.28)',
          },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            color: textSecondary,
            '&:hover': {
              backgroundColor: hover,
            },
          },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: '#3C4043',
            color: '#FFFFFF',
            borderRadius: 8,
            padding: '6px 10px',
            fontSize: 12,
            fontWeight: 500,
          },
          arrow: {
            color: '#3C4043',
          },
        },
      },
      MuiDivider: {
        styleOverrides: {
          root: {
            borderColor: divider,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 999,
          },
        },
      },
    },
  });
}

export default function ThemeRegistry({ children }: { children: React.ReactNode }) {
  const { isDark } = useAppTheme();
  const theme = useMemo(() => createAppTheme(isDark), [isDark]);

  return (
    <AppRouterCacheProvider>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </AppRouterCacheProvider>
  );
}

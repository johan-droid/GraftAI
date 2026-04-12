"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import type { ThemeMode } from "@/lib/theme";
import { getThemeColors, generateThemeCSS } from "@/lib/theme";

export type { ThemeMode };

interface ThemeContextType {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleTheme: () => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = "graftai-theme";

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>("dark");
  const [mounted, setMounted] = useState(false);

  // Initialize theme from localStorage or system preference
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
    if (stored && ["light", "dark", "auto"].includes(stored)) {
      setModeState(stored);
    } else {
      setModeState("dark"); // Default to dark
    }
    setMounted(true);
  }, []);

  // Apply theme changes
  useEffect(() => {
    if (!mounted) return;

    // Save to localStorage
    localStorage.setItem(STORAGE_KEY, mode);

    // Determine effective theme
    const isDark = mode === "dark" || 
      (mode === "auto" && window.matchMedia("(prefers-color-scheme: dark)").matches);

    // Apply CSS variables
    const css = generateThemeCSS(mode);
    
    // Remove old style tag if exists
    const oldStyle = document.getElementById("theme-styles");
    if (oldStyle) oldStyle.remove();

    // Add new style tag
    const style = document.createElement("style");
    style.id = "theme-styles";
    style.textContent = css;
    document.head.appendChild(style);

    // Apply data attribute for CSS selectors
    document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");

    // Add transition class for smooth theme changes
    document.body.style.transition = "background-color 0.3s ease, color 0.3s ease";
    
    return () => {
      document.body.style.transition = "";
    };
  }, [mode, mounted]);

  // Listen for system theme changes in auto mode
  useEffect(() => {
    if (mode !== "auto") return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      // Trigger re-render to apply new theme
      setModeState("auto");
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [mode]);

  const setMode = (newMode: ThemeMode) => {
    setModeState(newMode);
  };

  const toggleTheme = () => {
    if (mode === "light") setMode("dark");
    else if (mode === "dark") setMode("light");
    else {
      // If auto, switch to opposite of current system preference
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setMode(isDark ? "light" : "dark");
    }
  };

  const isDark = mode === "dark" || 
    (mode === "auto" && typeof window !== "undefined" && 
      window.matchMedia("(prefers-color-scheme: dark)").matches);

  // Provide the context even before mounting to prevent context errors in children
  return (
    <ThemeContext.Provider value={{ mode, setMode, toggleTheme, isDark }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}

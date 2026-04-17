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

function isThemeMode(value: string | null): value is ThemeMode {
  return value === "light" || value === "dark" || value === "auto";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    if (typeof window === "undefined") {
      return "light";
    }

    const stored = window.localStorage.getItem(STORAGE_KEY);
    return isThemeMode(stored) ? stored : "light";
  });

  // Apply theme changes
  useEffect(() => {
    if (typeof window === "undefined") return;

    const applyTheme = (themeMode: ThemeMode) => {
      const themeColors = getThemeColors(themeMode);

      localStorage.setItem(STORAGE_KEY, themeMode);

      const css = generateThemeCSS(themeMode);

      const oldStyle = document.getElementById("theme-styles");
      if (oldStyle) oldStyle.remove();

      const style = document.createElement("style");
      style.id = "theme-styles";
      style.textContent = css;
      document.head.appendChild(style);

      document.documentElement.setAttribute("data-theme", themeColors.isDark ? "dark" : "light");
      document.body.style.transition = "background-color 0.3s ease, color 0.3s ease";
    };

    applyTheme(mode);

    if (mode !== "auto") {
      return () => {
        document.body.style.transition = "";
      };
    }

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      applyTheme("auto");
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => {
      mediaQuery.removeEventListener("change", handleChange);
      document.body.style.transition = "";
    };
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

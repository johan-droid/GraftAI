"use client";

import React, { createContext, useContext, useState } from "react";

interface DashboardContextType {
  isPrivacyMode: boolean;
  togglePrivacyMode: () => void;
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [isPrivacyMode, setIsPrivacyMode] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("graftai_privacy_mode") === "true";
  });

  const togglePrivacyMode = () => {
    setIsPrivacyMode((prev) => {
      const next = !prev;
      localStorage.setItem("graftai_privacy_mode", String(next));
      return next;
    });
  };

  return (
    <DashboardContext.Provider value={{ isPrivacyMode, togglePrivacyMode }}>
      <div className={isPrivacyMode ? "privacy-mode-active" : ""}>
        {children}
      </div>
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (context === undefined) {
    throw new Error("useDashboard must be used within a DashboardProvider");
  }
  return context;
}

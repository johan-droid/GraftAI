"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

interface OnboardingState {
  completedSteps: string[];
  currentStep: string;
}

interface OnboardingContextValue extends OnboardingState {
  markStepComplete: (step: string) => void;
  setCurrentStep: (step: string) => void;
  resetOnboarding: () => void;
}

const STORAGE_KEY = "graftai_onboarding_state";

const defaultState: OnboardingState = {
  completedSteps: [],
  currentStep: "profile",
};

const OnboardingContext = createContext<OnboardingContextValue | undefined>(undefined);

export function OnboardingProvider({ children }: { children: React.ReactNode }) {
  const [completedSteps, setCompletedSteps] = useState<string[]>(() => {
    if (typeof window === "undefined") {
      return defaultState.completedSteps;
    }

    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState.completedSteps;
      const stored = JSON.parse(raw) as Partial<OnboardingState>;
      return Array.isArray(stored.completedSteps) ? stored.completedSteps : defaultState.completedSteps;
    } catch {
      return defaultState.completedSteps;
    }
  });
  const [currentStep, setCurrentStep] = useState<string>(() => {
    if (typeof window === "undefined") {
      return defaultState.currentStep;
    }

    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState.currentStep;
      const stored = JSON.parse(raw) as Partial<OnboardingState>;
      return typeof stored.currentStep === "string" ? stored.currentStep : defaultState.currentStep;
    } catch {
      return defaultState.currentStep;
    }
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ completedSteps, currentStep })
    );
  }, [completedSteps, currentStep]);

  const markStepComplete = (step: string) => {
    setCompletedSteps((prev) => Array.from(new Set([...prev, step])));
  };

  const resetOnboarding = () => {
    setCompletedSteps(defaultState.completedSteps);
    setCurrentStep(defaultState.currentStep);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  };

  const value = useMemo(
    () => ({ completedSteps, currentStep, markStepComplete, setCurrentStep, resetOnboarding }),
    [completedSteps, currentStep]
  );

  return <OnboardingContext.Provider value={value}>{children}</OnboardingContext.Provider>;
}

export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error("useOnboarding must be used within OnboardingProvider");
  }
  return context;
}

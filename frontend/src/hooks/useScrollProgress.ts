"use client";

import { useEffect, useState } from "react";

export function useScrollProgress(): number {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const updateProgress = () => {
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrolled = window.scrollY;
      const progress = scrollHeight > 0 ? scrolled / scrollHeight : 0;
      setProgress(Math.min(1, Math.max(0, progress)));
    };

    window.addEventListener("scroll", updateProgress, { passive: true });
    updateProgress();

    return () => window.removeEventListener("scroll", updateProgress);
  }, []);

  return progress;
}

import { useEffect, useRef, useState } from "react";

export function useScrollDirection(): "up" | "down" | null {
  const [direction, setDirection] = useState<"up" | "down" | null>(null);
  const lastScrollY = useRef(0);

  useEffect(() => {
    const updateDirection = () => {
      const scrollY = window.scrollY;
      if (scrollY > lastScrollY.current && scrollY > 100) {
        setDirection("down");
      } else if (scrollY < lastScrollY.current) {
        setDirection("up");
      }
      lastScrollY.current = scrollY;
    };

    window.addEventListener("scroll", updateDirection, { passive: true });
    return () => window.removeEventListener("scroll", updateDirection);
  }, []);

  return direction;
}

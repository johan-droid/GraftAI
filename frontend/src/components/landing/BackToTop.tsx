"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowUp } from "lucide-react";
import { IconButton } from "@mui/material";

export function BackToTop() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const toggleVisibility = () => {
      if (window.scrollY > 500) {
        setIsVisible(true);
      } else {
        setIsVisible(false);
      }
    };

    window.addEventListener("scroll", toggleVisibility, { passive: true });
    return () => window.removeEventListener("scroll", toggleVisibility);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ duration: 0.2 }}
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            zIndex: 1000,
          }}
        >
          <IconButton
            onClick={scrollToTop}
            sx={{
              width: 48,
              height: 48,
              background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
              color: "white",
              boxShadow: "0 4px 20px rgba(99, 102, 241, 0.4)",
              "&:hover": {
                background: "linear-gradient(135deg, #5558e0 0%, #d63d8a 100%)",
                transform: "scale(1.1)",
              },
              transition: "all 0.3s ease",
            }}
          >
            <ArrowUp size={24} />
          </IconButton>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

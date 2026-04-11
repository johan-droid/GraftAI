"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Paper, Typography, Button, Box } from "@mui/material";
import { Cookie } from "lucide-react";
import Link from "next/link";

export function CookieConsent() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem("cookieConsent");
    if (!consent) {
      // Show after a short delay
      const timer = setTimeout(() => setIsVisible(true), 2000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem("cookieConsent", "accepted");
    setIsVisible(false);
  };

  const handleDecline = () => {
    localStorage.setItem("cookieConsent", "declined");
    setIsVisible(false);
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          style={{
            position: "fixed",
            bottom: 16,
            left: 16,
            right: 16,
            zIndex: 9998,
            maxWidth: 500,
            margin: "0 auto",
          }}
        >
          <Paper
            elevation={0}
            sx={{
              p: 3,
              background: "rgba(26, 26, 46, 0.95)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(99, 102, 241, 0.3)",
              borderRadius: 3,
              boxShadow: "0 20px 40px -20px rgba(0, 0, 0, 0.5)",
            }}
          >
            <Box sx={{ display: "flex", gap: 2, alignItems: "flex-start" }}>
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: 2,
                  background: "rgba(99, 102, 241, 0.2)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <Cookie size={20} style={{ color: "#6366f1" }} />
              </Box>

              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                  We value your privacy
                </Typography>
                <Typography variant="body2" sx={{ color: "#94a3b8", mb: 2, fontSize: "0.875rem" }}>
                  We use cookies to enhance your browsing experience, serve personalized content, and analyze our traffic.{" "}
                  <Link href="/cookies" style={{ color: "#6366f1", textDecoration: "none" }}>
                    Learn more
                  </Link>
                </Typography>

                <Box sx={{ display: "flex", gap: 1.5 }}>
                  <Button
                    variant="contained"
                    onClick={handleAccept}
                    sx={{
                      background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
                      textTransform: "none",
                      fontWeight: 600,
                      borderRadius: "8px",
                      "&:hover": {
                        background: "linear-gradient(135deg, #5558e0 0%, #d63d8a 100%)",
                      },
                    }}
                  >
                    Accept All
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={handleDecline}
                    sx={{
                      borderColor: "rgba(99, 102, 241, 0.3)",
                      color: "#94a3b8",
                      textTransform: "none",
                      borderRadius: "8px",
                      "&:hover": {
                        borderColor: "rgba(99, 102, 241, 0.5)",
                        background: "rgba(99, 102, 241, 0.05)",
                      },
                    }}
                  >
                    Essential Only
                  </Button>
                </Box>
              </Box>
            </Box>
          </Paper>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

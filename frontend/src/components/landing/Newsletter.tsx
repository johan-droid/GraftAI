"use client";

import { useEffect, useRef, useState } from "react";
import { Box, Typography, TextField, InputAdornment, Alert } from "@mui/material";
import { motion } from "framer-motion";
import { Mail, Send, CheckCircle } from "lucide-react";
import { GradientButton } from "@/components/ui/GradientButton";

export function Newsletter() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const timeoutRef = useRef<number | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (timeoutRef.current) {
      window.clearTimeout(timeoutRef.current);
    }

    setStatus("success");
    setEmail("");
    timeoutRef.current = window.setTimeout(() => {
      setStatus("idle");
      timeoutRef.current = null;
    }, 5000);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <Box
      sx={{
        py: { xs: 8, md: 12 },
        background: "linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(236, 72, 153, 0.05) 100%)",
        borderTop: "1px solid rgba(99, 102, 241, 0.1)",
        borderBottom: "1px solid rgba(99, 102, 241, 0.1)",
      }}
    >
      <Box sx={{ maxWidth: 600, mx: "auto", px: 3, textAlign: "center" }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
        >
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: 2,
              background: "linear-gradient(135deg, #6366f1 0%, #ec4899 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              mx: "auto",
              mb: 3,
            }}
          >
            <Mail size={28} color="white" />
          </Box>

          <Typography variant="h4" sx={{ fontWeight: 700, mb: 2 }}>
            Stay in the Loop
          </Typography>
          <Typography variant="body1" sx={{ color: "#94a3b8", mb: 4 }}>
            Get the latest updates on AI scheduling, productivity tips, and exclusive offers.
          </Typography>

          {status === "success" ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              <Alert
                severity="success"
                icon={<CheckCircle size={24} />}
                sx={{
                  background: "rgba(16, 185, 129, 0.1)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  color: "#10b981",
                  borderRadius: 2,
                }}
              >
                Thanks for subscribing! Check your inbox for confirmation.
              </Alert>
            </motion.div>
          ) : (
            <form onSubmit={handleSubmit}>
              <Box sx={{ display: "flex", gap: 2, flexDirection: { xs: "column", sm: "row" } }}>
                <TextField
                  fullWidth
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  required
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      background: "rgba(26, 26, 46, 0.8)",
                      borderRadius: "12px",
                      border: "1px solid rgba(99, 102, 241, 0.2)",
                      color: "#f8fafc",
                      "& fieldset": { border: "none" },
                      "&:hover": { borderColor: "rgba(99, 102, 241, 0.4)" },
                      "&.Mui-focused": { borderColor: "#6366f1" },
                    },
                    "& .MuiInputBase-input::placeholder": { color: "#64748b" },
                  }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Mail size={20} style={{ color: "#64748b" }} />
                      </InputAdornment>
                    ),
                  }}
                />
                <GradientButton
                  type="submit"
                  gradientVariant="primary"
                  size="large"
                  sx={{ minWidth: { sm: 160 }, whiteSpace: "nowrap" }}
                >
                  Subscribe
                  <Send size={18} style={{ marginLeft: 8 }} />
                </GradientButton>
              </Box>
            </form>
          )}

          <Typography variant="caption" sx={{ color: "#64748b", mt: 2, display: "block" }}>
            No spam, unsubscribe anytime. Read our{" "}
            <Box
              component="a"
              href="/privacy"
              sx={{ color: "#a5b4fc", textDecoration: "none", "&:hover": { textDecoration: "underline" } }}
            >
              Privacy Policy
            </Box>
            .
          </Typography>
        </motion.div>
      </Box>
    </Box>
  );
}

"use client";

import { Box, LinearProgress, Typography } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X } from "lucide-react";

interface PasswordStrengthProps {
  password: string;
}

interface Requirement {
  label: string;
  test: (pwd: string) => boolean;
}

const requirements: Requirement[] = [
  { label: "At least 8 characters", test: (pwd) => pwd.length >= 8 },
  { label: "One uppercase letter", test: (pwd) => /[A-Z]/.test(pwd) },
  { label: "One lowercase letter", test: (pwd) => /[a-z]/.test(pwd) },
  { label: "One number", test: (pwd) => /\d/.test(pwd) },
  { label: "One special character", test: (pwd) => /[!@#$%^&*(),.?":{}|<>]/.test(pwd) },
];

function calculateStrength(password: string): number {
  if (!password) return 0;

  let score = 0;
  requirements.forEach((req) => {
    if (req.test(password)) score++;
  });

  return (score / requirements.length) * 100;
}

function getStrengthLabel(strength: number): { label: string; color: string } {
  if (strength === 0) return { label: "Enter password", color: "hsl(215, 16%, 40%)" };
  if (strength <= 20) return { label: "Very weak", color: "hsl(346, 84%, 61%)" };
  if (strength <= 40) return { label: "Weak", color: "hsl(0, 84%, 60%)" };
  if (strength <= 60) return { label: "Fair", color: "hsl(38, 92%, 50%)" };
  if (strength <= 80) return { label: "Good", color: "hsl(160, 84%, 39%)" };
  return { label: "Strong", color: "hsl(145, 63%, 42%)" };
}

export function PasswordStrength({ password }: PasswordStrengthProps) {
  const strength = calculateStrength(password);
  const { label, color } = getStrengthLabel(strength);
  const metRequirements = requirements.filter((req) => req.test(password));

  if (!password) {
    return (
      <Box sx={{ mt: 2 }}>
        <Typography sx={{ fontSize: "0.75rem", color: "hsl(215, 16%, 40%)", mb: 1 }}>
          Password must contain:
        </Typography>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
          {requirements.map((req) => (
            <Box key={req.label} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: "50%",
                  border: "1px solid hsl(215, 16%, 30%)",
                }}
              />
              <Typography sx={{ fontSize: "0.75rem", color: "hsl(215, 16%, 40%)" }}>
                {req.label}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 2 }}>
      {/* Strength Bar */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
        <Box sx={{ flex: 1 }}>
          <LinearProgress
            variant="determinate"
            value={strength}
            sx={{
              height: 4,
              borderRadius: 2,
              backgroundColor: "hsl(240, 24%, 18%)",
              "& .MuiLinearProgress-bar": {
                backgroundColor: color,
                borderRadius: 2,
                transition: "all 0.3s ease",
              },
            }}
          />
        </Box>
        <Typography
          sx={{
            fontSize: "0.75rem",
            color,
            fontWeight: 600,
            minWidth: 70,
            textAlign: "right",
          }}
        >
          {label}
        </Typography>
      </Box>

      {/* Requirements List */}
      <AnimatePresence>
        {password.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 1 }}>
              {requirements.map((req) => {
                const isMet = req.test(password);
                return (
                  <Box
                    key={req.label}
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 0.5,
                      px: 1.5,
                      py: 0.5,
                      background: isMet ? "hsla(160, 84%, 39%, 0.1)" : "hsl(240, 24%, 18%)",
                      border: `1px solid ${isMet ? "hsla(160, 84%, 39%, 0.3)" : "hsl(240, 24%, 22%)"}`,
                      borderRadius: 1,
                      transition: "all 0.2s ease",
                    }}
                  >
                    {isMet ? (
                      <Check size={10} style={{ color: "hsl(160, 84%, 39%)" }} />
                    ) : (
                      <X size={10} style={{ color: "hsl(215, 16%, 40%)" }} />
                    )}
                    <Typography
                      sx={{
                        fontSize: "0.6875rem",
                        color: isMet ? "hsl(160, 84%, 39%)" : "hsl(215, 16%, 40%)",
                        fontWeight: isMet ? 500 : 400,
                      }}
                    >
                      {req.label}
                    </Typography>
                  </Box>
                );
              })}
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
}

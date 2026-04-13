"use client";

import { Box, Button } from "@mui/material";
import { motion } from "framer-motion";
import { signIn } from "next-auth/react";
import { toast } from "@/components/ui/Toast";

// Custom SVG icons for OAuth providers
const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
  </svg>
);

const MicrosoftIcon = () => (
  <svg width="20" height="20" viewBox="0 0 21 21">
    <rect x="1" y="1" width="9" height="9" fill="#f25022" />
    <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
    <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
    <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
  </svg>
);

const providers = [
  { id: "google", name: "Google", icon: GoogleIcon, color: "#4285F4" },
  { id: "microsoft-entra-id", name: "Microsoft", icon: MicrosoftIcon, color: "#00A4EF" },
];

interface OAuthButtonsProps {
  callbackURL?: string;
}

export function OAuthButtons({ callbackURL = "/dashboard" }: OAuthButtonsProps) {
  const handleOAuth = async (provider: string) => {
    try {
      await signIn(provider, { callbackUrl: callbackURL });
    } catch (error) {
      console.error(`OAuth error for ${provider}:`, error);
      toast.error(
        `Unable to sign in with ${provider}. ${
          error instanceof Error ? error.message : String(error)
        }`
      );
    }
  };

  return (
    <Box>
      {/* OAuth Buttons */}
      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {providers.map((provider, index) => (
          <motion.div
            key={provider.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1, duration: 0.2 }}
            whileHover={{ x: 4 }}
            whileTap={{ scale: 0.99 }}
          >
            <Button
              onClick={() => handleOAuth(provider.id)}
              fullWidth
              sx={{
                py: 2,
                px: 3,
                background: "var(--bg-elevated)",
                border: "1px dashed var(--border-subtle)",
                borderRadius: 0,
                color: "var(--text-primary)",
                textTransform: "uppercase",
                fontFamily: "var(--font-mono)",
                fontSize: "11px",
                fontWeight: 900,
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-start",
                gap: 2.5,
                transition: "all 0.15s ease",
                letterSpacing: "0.15em",
                "&:hover": {
                  background: "var(--primary)",
                  borderColor: "var(--primary)",
                  color: "black",
                  "& svg": {
                    filter: "brightness(0) saturate(100%)",
                    opacity: 1,
                  }
                },
                "& svg": {
                  filter: "grayscale(100%) brightness(0.8)",
                  opacity: 0.6,
                  transition: "all 0.3s ease",
                }
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", minWidth: 24 }}>
                <provider.icon />
              </Box>
              AUTH_NODE_VIA_{provider.name.toUpperCase()}
            </Button>
          </motion.div>
        ))}
      </Box>
    </Box>
  );
}

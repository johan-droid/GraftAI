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
      {/* Divider */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
        <Box sx={{ flex: 1, height: 1, background: "hsla(239, 84%, 67%, 0.1)" }} />
        <Box
          component="span"
          sx={{
            fontSize: "0.875rem",
            color: "hsl(215, 16%, 40%)",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
          }}
        >
          Or continue with
        </Box>
        <Box sx={{ flex: 1, height: 1, background: "hsla(239, 84%, 67%, 0.1)" }} />
      </Box>

      {/* OAuth Buttons */}
      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {providers.map((provider, index) => (
          <motion.div
            key={provider.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1, duration: 0.3 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Button
              onClick={() => handleOAuth(provider.id)}
              fullWidth
              sx={{
                py: 1.5,
                background: "hsl(240, 24%, 14%)",
                border: "1px solid hsla(239, 84%, 67%, 0.15)",
                borderRadius: "12px",
                color: "hsl(220, 20%, 98%)",
                textTransform: "none",
                fontSize: "0.9375rem",
                fontWeight: 500,
                display: "flex",
                alignItems: "center",
                gap: 2,
                transition: "all 0.2s ease",
                "&:hover": {
                  background: "hsl(240, 24%, 18%)",
                  borderColor: "hsla(239, 84%, 67%, 0.3)",
                  boxShadow: `0 0 20px ${provider.color}20`,
                },
              }}
            >
              <provider.icon />
              Continue with {provider.name}
            </Button>
          </motion.div>
        ))}
      </Box>
    </Box>
  );
}

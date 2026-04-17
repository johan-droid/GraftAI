"use client";

import { Box, Button } from "@mui/material";
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
  { id: "google", name: "Google", icon: GoogleIcon },
  { id: "microsoft-entra-id", name: "Microsoft", icon: MicrosoftIcon },
];

interface OAuthButtonsProps {
  callbackURL?: string;
  actionText?: "Sign in" | "Sign up";
}

export function OAuthButtons({ callbackURL = "/dashboard", actionText = "Sign in" }: OAuthButtonsProps) {
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
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {providers.map((provider) => (
        <Button
          key={provider.id}
          onClick={() => handleOAuth(provider.id)}
          fullWidth
          variant="outlined"
          startIcon={<provider.icon />}
          sx={{
            minHeight: 48,
            py: { xs: 1.4, sm: 1.5 },
            px: { xs: 2.5, sm: 3 },
            borderRadius: "18px",
            textTransform: "none",
            color: "var(--text-primary, #1f1f1f)",
            borderColor: "rgba(95, 99, 104, 0.18)",
            background: "linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,249,250,0.92) 100%)",
            boxShadow: "0 12px 28px -18px rgba(32, 33, 36, 0.2)",
            fontFamily: "var(--font-sans, 'Google Sans', Roboto, sans-serif)",
            fontSize: { xs: "0.93rem", sm: "0.875rem" },
            fontWeight: 600,
            justifyContent: "center",
            gap: 1,
            transition: "transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background 160ms ease",
            "&:hover": {
              backgroundColor: "rgba(255,255,255,0.98)",
              borderColor: "rgba(26, 115, 232, 0.28)",
              boxShadow: "0 16px 36px -22px rgba(26, 115, 232, 0.32)",
              transform: "translateY(-1px)",
            },
            "& .MuiButton-startIcon": {
              marginRight: "8px",
              marginLeft: "-4px",
            },
          }}
        >
          {actionText} with {provider.name}
        </Button>
      ))}
    </Box>
  );
}

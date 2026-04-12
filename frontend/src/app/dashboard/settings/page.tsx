"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Avatar,
  Switch,
  Divider,
  Chip,
  Grid,
} from "@mui/material";
import { motion } from "framer-motion";
import {
  User,
  Shield,
  Bell,
  Eye,
  Loader2,
  Check,
  LogOut,
  KeyRound,
  Trash2,
  AlertTriangle,
  Palette,
  Moon,
  Sun,
  Monitor,
} from "lucide-react";
import { toast } from "@/components/ui/Toast";
import { useTheme, ThemeMode } from "@/contexts/ThemeContext";
import { useAuthContext } from "@/app/providers/auth-provider";
import { setConsent } from "@/lib/api";
import { MobileSidebar } from "@/components/dashboard/MobileSidebar";
import { BottomNav } from "@/components/dashboard/BottomNav";
import { Header } from "@/components/dashboard/Header";

const CONSENT_CONFIG = [
  {
    key: "analytics",
    label: "Analytics & Usage Data",
    description: "Share anonymized usage data to help improve GraftAI. No personal content is shared.",
    icon: Eye,
    defaultEnabled: true,
  },
  {
    key: "notifications",
    label: "Email Notifications",
    description: "Receive booking reminders, meeting summaries, and AI insights via email.",
    icon: Bell,
    defaultEnabled: true,
  },
  {
    key: "ai_training",
    label: "AI Model Training",
    description: "Allow anonymized interaction patterns to improve AI scheduling accuracy. Opt out anytime.",
    icon: Shield,
    defaultEnabled: false,
  },
] as const;

type ConsentKey = (typeof CONSENT_CONFIG)[number]["key"];

export default function SettingsPage() {
  const router = useRouter();
  const { user, logout, isAuthenticated, loading: authLoading } = useAuthContext();
  const { mode, setMode, isDark } = useTheme();

  const [consents, setConsents] = useState<Record<ConsentKey, boolean>>({
    analytics: true,
    notifications: true,
    ai_training: false,
  });
  const [savingKey, setSavingKey] = useState<ConsentKey | null>(null);
  const [savedKey, setSavedKey] = useState<ConsentKey | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [changingPw, setChangingPw] = useState(false);
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "" });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    fetch("/api/user/preferences", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        if (data && data.consents) {
          setConsents(data.consents);
        }
      })
      .catch((err) => {
        console.error("Failed to load preferences:", err);
      });
  }, []);

  async function handleToggle(key: ConsentKey) {
    const next = !consents[key];
    setSavingKey(key);
    try {
      await setConsent(key, next);
      setConsents((prev) => ({ ...prev, [key]: next }));
      setSavedKey(key);
      setTimeout(() => setSavedKey(null), 2200);
      toast.success(`${next ? "Enabled" : "Disabled"} ${key} preference.`);
    } catch {
      toast.error("Failed to update preference. Please try again.");
    } finally {
      setSavingKey(null);
    }
  }

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    if (pwForm.next !== pwForm.confirm) {
      toast.error("Passwords don't match.");
      return;
    }
    if (pwForm.next.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    setChangingPw(true);
    try {
      const res = await fetch("/api/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          current_password: pwForm.current,
          new_password: pwForm.next
        }),
      });
      if (!res.ok) throw new Error("Failed to update password.");
      setPwForm({ current: "", next: "", confirm: "" });
      toast.success("Password updated successfully.");
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setChangingPw(false);
    }
  }

  const themeOptions: { value: ThemeMode; label: string; icon: typeof Sun }[] = [
    { value: "light", label: "Light", icon: Sun },
    { value: "dark", label: "Dark", icon: Moon },
    { value: "auto", label: "System", icon: Monitor },
  ];

  if (authLoading) {
    return (
      <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          style={{
            width: 40,
            height: 40,
            borderRadius: "50%",
            border: "3px solid hsla(239, 84%, 67%, 0.2)",
            borderTopColor: "hsl(239, 84%, 67%)",
          }}
        />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: isDark ? "hsl(240, 24%, 7%)" : "hsl(220, 14%, 96%)",
        pb: { xs: 10, md: 4 },
      }}
    >
      <MobileSidebar />

      <Container maxWidth="lg" sx={{ px: { xs: 2, md: 4 }, py: { xs: 2, md: 4 } }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Header */}
          <Header
            userName={(user as any)?.name}
            userEmail={user?.email}
            userAvatar={(user as any)?.avatar}
            notificationCount={0}
          />

          {/* Page Title */}
          <Box sx={{ mb: 4 }}>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                mb: 1,
              }}
            >
              Settings
            </Typography>
            <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
              Manage your account preferences and privacy
            </Typography>
          </Box>

          <Grid container spacing={3}>
            {/* Left Column */}
            <Grid item xs={12} lg={8}>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                {/* Profile Card */}
                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    background: isDark
                      ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                      : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                    border: "1px solid hsla(239, 84%, 67%, 0.15)",
                    borderRadius: "16px",
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
                    <Box
                      sx={{
                        width: 40,
                        height: 40,
                        borderRadius: "10px",
                        background: "hsla(239, 84%, 67%, 0.15)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        border: "1px solid hsla(239, 84%, 67%, 0.3)",
                      }}
                    >
                      <User size={20} style={{ color: "hsl(239, 84%, 67%)" }} />
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                      Profile
                    </Typography>
                  </Box>

                  <Box sx={{ display: "flex", alignItems: "center", gap: 3, mb: 4 }}>
                    <Avatar
                      src={(user as any)?.avatar}
                      sx={{
                        width: 80,
                        height: 80,
                        background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                        fontSize: "1.5rem",
                        fontWeight: 700,
                      }}
                    >
                      {(user as any)?.name?.charAt(0) || (user as any)?.email?.charAt(0) || "U"}
                    </Avatar>
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 700, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                        {(user as any)?.name || "User"}
                      </Typography>
                      <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                        {user?.email}
                      </Typography>
                      <Chip
                        label="Pro Plan"
                        size="small"
                        sx={{
                          mt: 1,
                          background: "hsla(239, 84%, 67%, 0.15)",
                          color: "hsl(239, 84%, 67%)",
                          fontWeight: 600,
                          fontSize: "0.75rem",
                        }}
                      />
                    </Box>
                  </Box>

                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Full Name"
                        value={(user as any)?.name || ""}
                        InputProps={{ readOnly: true }}
                        sx={{
                          "& .MuiOutlinedInput-root": {
                            background: isDark ? "hsla(239, 84%, 67%, 0.05)" : "hsla(239, 84%, 67%, 0.03)",
                            borderRadius: "10px",
                            color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                            "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.2)" },
                          },
                          "& .MuiInputLabel-root": { color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" },
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Email Address"
                        value={user?.email || ""}
                        InputProps={{ readOnly: true }}
                        sx={{
                          "& .MuiOutlinedInput-root": {
                            background: isDark ? "hsla(239, 84%, 67%, 0.05)" : "hsla(239, 84%, 67%, 0.03)",
                            borderRadius: "10px",
                            color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                            "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.2)" },
                          },
                          "& .MuiInputLabel-root": { color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" },
                        }}
                      />
                    </Grid>
                  </Grid>
                </Paper>

                {/* Change Password */}
                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    background: isDark
                      ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                      : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                    border: "1px solid hsla(239, 84%, 67%, 0.15)",
                    borderRadius: "16px",
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
                    <Box
                      sx={{
                        width: 40,
                        height: 40,
                        borderRadius: "10px",
                        background: "hsla(239, 84%, 67%, 0.15)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        border: "1px solid hsla(239, 84%, 67%, 0.3)",
                      }}
                    >
                      <KeyRound size={20} style={{ color: "hsl(239, 84%, 67%)" }} />
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                      Change Password
                    </Typography>
                  </Box>

                  <Box component="form" onSubmit={handleChangePassword} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    <TextField
                      fullWidth
                      type="password"
                      label="Current Password"
                      placeholder="••••••••"
                      value={pwForm.current}
                      onChange={(e) => setPwForm((p) => ({ ...p, current: e.target.value }))}
                      sx={{
                        "& .MuiOutlinedInput-root": {
                          background: "transparent",
                          borderRadius: "10px",
                          color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                          "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.3)" },
                          "&:hover fieldset": { borderColor: "hsla(239, 84%, 67%, 0.5)" },
                        },
                        "& .MuiInputLabel-root": { color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" },
                      }}
                    />
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          type="password"
                          label="New Password"
                          placeholder="Min. 8 characters"
                          value={pwForm.next}
                          onChange={(e) => setPwForm((p) => ({ ...p, next: e.target.value }))}
                          sx={{
                            "& .MuiOutlinedInput-root": {
                              background: "transparent",
                              borderRadius: "10px",
                              color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                              "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.3)" },
                            },
                            "& .MuiInputLabel-root": { color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" },
                          }}
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          type="password"
                          label="Confirm Password"
                          placeholder="Repeat password"
                          value={pwForm.confirm}
                          onChange={(e) => setPwForm((p) => ({ ...p, confirm: e.target.value }))}
                          sx={{
                            "& .MuiOutlinedInput-root": {
                              background: "transparent",
                              borderRadius: "10px",
                              color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                              "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.3)" },
                            },
                            "& .MuiInputLabel-root": { color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" },
                          }}
                        />
                      </Grid>
                    </Grid>
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={changingPw || !pwForm.current || !pwForm.next}
                      sx={{
                        alignSelf: "flex-start",
                        mt: 1,
                        background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                        textTransform: "none",
                        fontWeight: 600,
                        borderRadius: "10px",
                        px: 3,
                        py: 1,
                        "&:hover": {
                          background: "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                        },
                        "&:disabled": {
                          background: isDark ? "hsl(240, 24%, 22%)" : "hsl(220, 14%, 90%)",
                        },
                      }}
                    >
                      {changingPw ? "Updating..." : "Update Password"}
                    </Button>
                  </Box>
                </Paper>

                {/* Privacy & Consent */}
                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    background: isDark
                      ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                      : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                    border: "1px solid hsla(239, 84%, 67%, 0.15)",
                    borderRadius: "16px",
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
                    <Box
                      sx={{
                        width: 40,
                        height: 40,
                        borderRadius: "10px",
                        background: "hsla(239, 84%, 67%, 0.15)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        border: "1px solid hsla(239, 84%, 67%, 0.3)",
                      }}
                    >
                      <Shield size={20} style={{ color: "hsl(239, 84%, 67%)" }} />
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                      Privacy & Consent
                    </Typography>
                  </Box>

                  <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    {CONSENT_CONFIG.map((item) => {
                      const isSaving = savingKey === item.key;
                      const isSaved = savedKey === item.key;
                      const enabled = consents[item.key];

                      return (
                        <Paper
                          key={item.key}
                          elevation={0}
                          sx={{
                            p: 2,
                            display: "flex",
                            alignItems: "center",
                            gap: 2,
                            background: isDark ? "hsla(239, 84%, 67%, 0.05)" : "hsla(239, 84%, 67%, 0.03)",
                            border: "1px solid hsla(239, 84%, 67%, 0.1)",
                            borderRadius: "12px",
                          }}
                        >
                          <Box
                            sx={{
                              width: 40,
                              height: 40,
                              borderRadius: "10px",
                              background: isDark ? "hsla(239, 84%, 67%, 0.1)" : "hsla(239, 84%, 67%, 0.05)",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              flexShrink: 0,
                            }}
                          >
                            <item.icon size={18} style={{ color: "hsl(239, 84%, 67%)" }} />
                          </Box>
                          <Box sx={{ flex: 1 }}>
                            <Typography sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                              {item.label}
                            </Typography>
                            <Typography sx={{ fontSize: "0.875rem", color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                              {item.description}
                            </Typography>
                          </Box>
                          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                            {isSaved && (
                              <Check size={16} style={{ color: "hsl(160, 84%, 39%)" }} />
                            )}
                            <Switch
                              checked={enabled}
                              onChange={() => handleToggle(item.key)}
                              disabled={isSaving}
                              sx={{
                                "& .MuiSwitch-switchBase.Mui-checked": {
                                  color: "hsl(239, 84%, 67%)",
                                },
                                "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
                                  backgroundColor: "hsl(239, 84%, 67%)",
                                },
                              }}
                            />
                          </Box>
                        </Paper>
                      );
                    })}
                  </Box>
                </Paper>

                {/* Danger Zone */}
                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    background: isDark
                      ? "linear-gradient(135deg, hsla(346, 84%, 61%, 0.1) 0%, hsla(346, 84%, 61%, 0.05) 100%)"
                      : "linear-gradient(135deg, hsla(346, 84%, 61%, 0.05) 0%, hsla(346, 84%, 61%, 0.02) 100%)",
                    border: "1px solid hsla(346, 84%, 61%, 0.3)",
                    borderRadius: "16px",
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
                    <AlertTriangle size={20} style={{ color: "hsl(346, 84%, 61%)" }} />
                    <Typography variant="h6" sx={{ fontWeight: 600, color: "hsl(346, 84%, 61%)" }}>
                      Danger Zone
                    </Typography>
                  </Box>

                  <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    <Box
                      sx={{
                        display: "flex",
                        flexDirection: { xs: "column", sm: "row" },
                        alignItems: { xs: "flex-start", sm: "center" },
                        justifyContent: "space-between",
                        gap: 2,
                        py: 2,
                        borderBottom: "1px solid hsla(346, 84%, 61%, 0.1)",
                      }}
                    >
                      <Box>
                        <Typography sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                          Sign Out
                        </Typography>
                        <Typography sx={{ fontSize: "0.875rem", color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                          End your current session securely.
                        </Typography>
                      </Box>
                      <Button
                        onClick={logout}
                        variant="outlined"
                        startIcon={<LogOut size={16} />}
                        sx={{
                          borderColor: "hsla(346, 84%, 61%, 0.5)",
                          color: "hsl(346, 84%, 61%)",
                          textTransform: "none",
                          fontWeight: 600,
                          borderRadius: "10px",
                          "&:hover": {
                            borderColor: "hsl(346, 84%, 61%)",
                            background: "hsla(346, 84%, 61%, 0.1)",
                          },
                        }}
                      >
                        Sign Out
                      </Button>
                    </Box>

                    <Box
                      sx={{
                        display: "flex",
                        flexDirection: { xs: "column", sm: "row" },
                        alignItems: { xs: "flex-start", sm: "center" },
                        justifyContent: "space-between",
                        gap: 2,
                        py: 2,
                      }}
                    >
                      <Box>
                        <Typography sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                          Delete Account
                        </Typography>
                        <Typography sx={{ fontSize: "0.875rem", color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                          Permanently delete your account and all data. This cannot be undone.
                        </Typography>
                      </Box>
                      {!deleteConfirm ? (
                        <Button
                          onClick={() => setDeleteConfirm(true)}
                          variant="contained"
                          startIcon={<Trash2 size={16} />}
                          sx={{
                            background: "hsl(346, 84%, 61%)",
                            textTransform: "none",
                            fontWeight: 600,
                            borderRadius: "10px",
                            "&:hover": {
                              background: "hsl(346, 84%, 51%)",
                            },
                          }}
                        >
                          Delete
                        </Button>
                      ) : (
                        <Box sx={{ display: "flex", gap: 1 }}>
                          <Button
                            onClick={async () => {
                              try {
                                const res = await fetch("/api/users/me", {
                                  method: "DELETE",
                                  credentials: "include",
                                });
                                if (res.ok) {
                                  toast.success("Account deleted successfully");
                                  router.push("/login");
                                } else {
                                  throw new Error("Failed to delete account");
                                }
                              } catch (error) {
                                toast.error(error instanceof Error ? error.message : "Failed to delete account");
                              } finally {
                                setDeleteConfirm(false);
                              }
                            }}
                            variant="contained"
                            sx={{
                              background: "hsl(346, 84%, 61%)",
                              color: "white",
                              textTransform: "none",
                              fontWeight: 600,
                              borderRadius: "8px",
                              "&:hover": {
                                background: "hsl(346, 84%, 51%)",
                              },
                            }}
                          >
                            Confirm
                          </Button>
                          <Button
                            onClick={() => setDeleteConfirm(false)}
                            variant="outlined"
                            sx={{
                              borderColor: "hsla(346, 84%, 61%, 0.5)",
                              color: "hsl(346, 84%, 61%)",
                              textTransform: "none",
                              fontWeight: 600,
                              borderRadius: "8px",
                            }}
                          >
                            Cancel
                          </Button>
                        </Box>
                      )}
                    </Box>
                  </Box>
                </Paper>
              </Box>
            </Grid>

            {/* Right Column - Theme & Quick Links */}
            <Grid item xs={12} lg={4}>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                {/* Theme Settings */}
                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    background: isDark
                      ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                      : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                    border: "1px solid hsla(239, 84%, 67%, 0.15)",
                    borderRadius: "16px",
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
                    <Box
                      sx={{
                        width: 40,
                        height: 40,
                        borderRadius: "10px",
                        background: "hsla(239, 84%, 67%, 0.15)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        border: "1px solid hsla(239, 84%, 67%, 0.3)",
                      }}
                    >
                      <Palette size={20} style={{ color: "hsl(239, 84%, 67%)" }} />
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                      Appearance
                    </Typography>
                  </Box>

                  <Typography sx={{ mb: 2, color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                    Choose your preferred theme
                  </Typography>

                  <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                    {themeOptions.map((option) => (
                      <Paper
                        key={option.value}
                        onClick={() => setMode(option.value)}
                        elevation={0}
                        sx={{
                          p: 2,
                          display: "flex",
                          alignItems: "center",
                          gap: 2,
                          cursor: "pointer",
                          background: mode === option.value ? "hsla(239, 84%, 67%, 0.15)" : "transparent",
                          border: `1px solid ${mode === option.value ? "hsla(239, 84%, 67%, 0.5)" : "hsla(239, 84%, 67%, 0.1)"}`,
                          borderRadius: "10px",
                          transition: "all 0.2s ease",
                          "&:hover": {
                            background: "hsla(239, 84%, 67%, 0.1)",
                            borderColor: "hsla(239, 84%, 67%, 0.3)",
                          },
                        }}
                      >
                        <option.icon
                          size={20}
                          style={{
                            color: mode === option.value ? "hsl(239, 84%, 67%)" : isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                          }}
                        />
                        <Typography
                          sx={{
                            flex: 1,
                            fontWeight: mode === option.value ? 600 : 400,
                            color: mode === option.value ? "hsl(239, 84%, 67%)" : isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                          }}
                        >
                          {option.label}
                        </Typography>
                        {mode === option.value && <Check size={18} style={{ color: "hsl(239, 84%, 67%)" }} />}
                      </Paper>
                    ))}
                  </Box>
                </Paper>

                {/* Quick Links */}
                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    background: isDark
                      ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                      : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                    border: "1px solid hsla(239, 84%, 67%, 0.15)",
                    borderRadius: "16px",
                  }}
                >
                  <Typography variant="h6" sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)", mb: 2 }}>
                    Quick Links
                  </Typography>

                  <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                    {[
                      { label: "Billing & Subscription", href: "/dashboard/settings/billing" },
                      { label: "Connected Integrations", href: "/dashboard/settings/integrations" },
                      { label: "API Keys", href: "/dashboard/settings/api-keys" },
                    ].map((link) => (
                      <Box
                        key={link.href}
                        component="a"
                        href={link.href}
                        sx={{
                          p: 1.5,
                          borderRadius: "10px",
                          color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)",
                          textDecoration: "none",
                          transition: "all 0.2s ease",
                          "&:hover": {
                            background: isDark ? "hsla(239, 84%, 67%, 0.1)" : "hsla(239, 84%, 67%, 0.05)",
                            color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                          },
                        }}
                      >
                        {link.label}
                      </Box>
                    ))}
                  </Box>
                </Paper>

                {/* Version Info */}
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    background: "transparent",
                    border: "1px solid hsla(239, 84%, 67%, 0.1)",
                    borderRadius: "10px",
                    textAlign: "center",
                  }}
                >
                  <Typography sx={{ fontSize: "0.875rem", color: isDark ? "hsl(215, 16%, 40%)" : "hsl(215, 16%, 60%)" }}>
                    GraftAI v1.0.0
                  </Typography>
                </Paper>
              </Box>
            </Grid>
          </Grid>
        </motion.div>
      </Container>

      <BottomNav />
    </Box>
  );
}

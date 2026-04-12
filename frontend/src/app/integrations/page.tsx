"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Grid,
  Chip,
  Switch,
  IconButton,
  Tooltip,
  CircularProgress,
  Skeleton,
} from "@mui/material";
import { motion } from "framer-motion";
import {
  Plug,
  Check,
  X,
  RefreshCw,
  ExternalLink,
  Calendar,
  MessageSquare,
  Video,
  Mail,
  Cloud,
  Settings,
  Zap,
  Shield,
} from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
  import { useAuthContext } from "@/app/providers/auth-provider";
import { MobileSidebar } from "@/components/dashboard/MobileSidebar";
import { BottomNav } from "@/components/dashboard/BottomNav";
import { Header } from "@/components/dashboard/Header";
import { toast } from "@/components/ui/Toast";
import { useQuery } from "@/hooks/useQuery";

interface Integration {
  id: string;
  provider: string;
  name: string;
  description: string;
  icon: typeof Calendar;
  color: string;
  connected: boolean;
  is_active: boolean;
  category: "calendar" | "communication" | "productivity" | "storage";
  features: string[];
  loading?: boolean;
}

// Integration metadata for display (static)
const integrationMetadata: Record<string, { icon: typeof Calendar; color: string; category: Integration["category"]; features: string[]; description: string }> = {
  "google-calendar": { icon: Calendar, color: "#4285F4", category: "calendar", features: ["Event sync", "Availability check", "Auto-scheduling"], description: "Sync your Google Calendar events and availability" },
  "microsoft-365": { icon: Cloud, color: "#0078D4", category: "calendar", features: ["Outlook sync", "Teams integration", "Office 365 calendar"], description: "Connect Outlook Calendar and Teams" },
  "slack": { icon: MessageSquare, color: "#4A154B", category: "communication", features: ["Meeting reminders", "Daily digests", "Direct messages"], description: "Get meeting notifications in your Slack channels" },
  "zoom": { icon: Video, color: "#2D8CFF", category: "communication", features: ["Auto-create links", "Join from calendar", "Recording sync"], description: "Automatically generate Zoom meeting links" },
  "teams": { icon: Video, color: "#6264A7", category: "communication", features: ["Teams meetings", "Channel posts", "Screen sharing"], description: "Create Teams meetings for virtual events" },
  "gmail": { icon: Mail, color: "#EA4335", category: "productivity", features: ["Send invites", "Email templates", "RSVP tracking"], description: "Send meeting invites via Gmail" },
  "notion": { icon: Cloud, color: "#000000", category: "productivity", features: ["Meeting notes", "Action items", "Database sync"], description: "Export meeting notes to Notion" },
  "drive": { icon: Cloud, color: "#0F9D58", category: "storage", features: ["File attachments", "Meeting recordings", "Agenda docs"], description: "Attach files from Google Drive to meetings" },
};

const categories = [
  { id: "all", label: "All Integrations" },
  { id: "calendar", label: "Calendar" },
  { id: "communication", label: "Communication" },
  { id: "productivity", label: "Productivity" },
  { id: "storage", label: "Storage" },
];

export default function IntegrationsPage() {
  const router = useRouter();
  const { user, isAuthenticated, loading: authLoading } = useAuthContext();
  const { isDark } = useTheme();

  const [activeCategory, setActiveCategory] = useState("all");
  const [showOnlyConnected, setShowOnlyConnected] = useState(false);
  const [localIntegrations, setLocalIntegrations] = useState<Record<string, boolean>>({});

  // Fetch integrations from API
  const { data: apiIntegrations, isLoading: integrationsLoading, error: integrationsError, refetch: refetchIntegrations } = useQuery<
    Array<{
      id: string;
      provider: string;
      name: string;
      is_active: boolean;
      created_at: string;
    }>
  >(isAuthenticated ? "/api/integrations" : null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  // Build display integrations from metadata + API data
  const integrations: Integration[] = Object.entries(integrationMetadata).map(([provider, meta]) => {
    const apiIntegration = apiIntegrations?.find(i => i.provider === provider);
    const isConnected = apiIntegration?.is_active || localIntegrations[provider] || false;
    
    return {
      id: apiIntegration?.id || provider,
      provider: provider,
      name: meta.description.split(" ")[0] || provider,
      description: meta.description,
      icon: meta.icon,
      color: meta.color,
      connected: isConnected,
      is_active: apiIntegration?.is_active || false,
      category: meta.category,
      features: meta.features,
    };
  });

  const filteredIntegrations = integrations.filter((integration) => {
    if (activeCategory !== "all" && integration.category !== activeCategory) return false;
    if (showOnlyConnected && !integration.connected) return false;
    return true;
  });

  const connectedCount = integrations.filter((i) => i.connected).length;

  const handleConnect = async (id: string, provider: string) => {
    // Find the integration
    const integration = integrations.find((i) => i.id === id);
    if (!integration) return;

    const isCurrentlyConnected = integration.connected;
    
    try {
      if (isCurrentlyConnected) {
        // Disconnect - delete the integration
        const response = await fetch(`/api/integrations/${id}`, {
          method: "DELETE",
          credentials: "include",
        });

        if (!response.ok) {
          throw new Error("Failed to disconnect");
        }

        // Update local state
        setLocalIntegrations(prev => ({ ...prev, [provider]: false }));
        toast.success(`Disconnected from ${integration.name}`);
      } else {
        // Connect - would normally redirect to OAuth flow
        // For now, simulate by creating a placeholder integration
        const response = await fetch("/api/integrations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            provider: provider,
            name: integration.name,
            events: ["booking.created", "booking.updated"],
            is_active: true,
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to connect");
        }

        // Update local state
        setLocalIntegrations(prev => ({ ...prev, [provider]: true }));
        toast.success(`Connected to ${integration.name}!`);
        
        // Refetch integrations to get the new ID
        refetchIntegrations();
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update connection");
    }
  };

  const handleSync = async (id: string) => {
    try {
      const response = await fetch(`/api/integrations/${id}/sync`, {
        method: "POST",
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error("Sync failed");
      }

      toast.success("Sync completed!");
      refetchIntegrations();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Sync failed");
    }
  };

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

      <Container maxWidth="xl" sx={{ px: { xs: 2, md: 4 }, py: { xs: 2, md: 4 } }}>
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
                display: "flex",
                alignItems: "center",
                gap: 1,
              }}
            >
              <Plug size={28} style={{ color: "hsl(239, 84%, 67%)" }} />
              Integrations
            </Typography>
            <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
              Connect your favorite tools to supercharge your scheduling
            </Typography>
          </Box>

          {/* Stats Bar */}
          <Paper
            elevation={0}
            sx={{
              p: 3,
              mb: 3,
              background: isDark
                ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
              border: "1px solid hsla(239, 84%, 67%, 0.15)",
              borderRadius: "16px",
              display: "flex",
              flexWrap: "wrap",
              gap: 3,
              alignItems: "center",
            }}
          >
            <Box>
              <Typography sx={{ fontSize: "0.875rem", color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                Connected Apps
              </Typography>
              <Typography
                variant="h4"
                sx={{ fontWeight: 700, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}
              >
                {connectedCount}{" "}
                <Typography component="span" sx={{ fontSize: "1rem", color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                  / {integrations.length}
                </Typography>
              </Typography>
            </Box>

            <Box sx={{ flex: 1 }} />

            <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
              <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                Show connected only
              </Typography>
              <Switch
                checked={showOnlyConnected}
                onChange={(e) => setShowOnlyConnected(e.target.checked)}
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

          {/* Category Filter */}
          <Box sx={{ display: "flex", gap: 1, mb: 3, flexWrap: "wrap" }}>
            {categories.map((category) => (
              <Button
                key={category.id}
                onClick={() => setActiveCategory(category.id)}
                variant={activeCategory === category.id ? "contained" : "outlined"}
                sx={{
                  textTransform: "none",
                  fontWeight: 600,
                  borderRadius: "10px",
                  px: 2,
                  ...(activeCategory === category.id
                    ? {
                        background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                        color: "white",
                      }
                    : {
                        borderColor: "hsla(239, 84%, 67%, 0.3)",
                        color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                      }),
                }}
              >
                {category.label}
              </Button>
            ))}
          </Box>

          {/* Integrations Grid */}
          {integrationsLoading ? (
            <Grid container spacing={3}>
              {Array.from({ length: 6 }).map((_, index) => (
                <Grid item xs={12} sm={6} lg={4} key={index}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 3,
                      height: "100%",
                      background: isDark
                        ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                        : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                      borderRadius: "16px",
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
                      <Skeleton variant="circular" width={48} height={48} />
                      <Box sx={{ flex: 1 }}>
                        <Skeleton variant="text" width="60%" />
                        <Skeleton variant="text" width="40%" />
                      </Box>
                    </Box>
                    <Skeleton variant="text" width="100%" />
                    <Skeleton variant="text" width="80%" />
                  </Paper>
                </Grid>
              ))}
            </Grid>
          ) : integrationsError ? (
            <Paper
              elevation={0}
              sx={{
                p: 4,
                textAlign: "center",
                background: isDark
                  ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                  : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                border: "1px solid hsla(346, 84%, 61%, 0.3)",
                borderRadius: "16px",
              }}
            >
              <Typography sx={{ color: "hsl(346, 84%, 61%)", mb: 2, fontWeight: 600 }}>
                Failed to load integrations
              </Typography>
              <Button
                onClick={() => refetchIntegrations()}
                variant="outlined"
                sx={{
                  textTransform: "none",
                  borderColor: "hsla(239, 84%, 67%, 0.5)",
                  color: "hsl(239, 84%, 67%)",
                  borderRadius: "8px",
                }}
              >
                Retry
              </Button>
            </Paper>
          ) : (
          <Grid container spacing={3}>
            {filteredIntegrations.map((integration, index) => (
              <Grid item xs={12} sm={6} lg={4} key={integration.id}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Paper
                    elevation={0}
                    sx={{
                      p: 3,
                      height: "100%",
                      background: isDark
                        ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                        : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                      border: `1px solid ${
                        integration.connected
                          ? "hsla(160, 84%, 39%, 0.3)"
                          : "hsla(239, 84%, 67%, 0.15)"
                      }`,
                      borderRadius: "16px",
                      transition: "all 0.3s ease",
                      "&:hover": {
                        borderColor: integration.connected
                          ? "hsla(160, 84%, 39%, 0.5)"
                          : "hsla(239, 84%, 67%, 0.3)",
                        transform: "translateY(-4px)",
                        boxShadow: isDark
                          ? "0 20px 40px -10px hsla(239, 84%, 67%, 0.2)"
                          : "0 20px 40px -10px hsla(239, 84%, 67%, 0.15)",
                      },
                    }}
                  >
                    {/* Header */}
                    <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", mb: 2 }}>
                      <Box
                        sx={{
                          width: 48,
                          height: 48,
                          borderRadius: "12px",
                          background: integration.color + "20",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        <integration.icon size={24} style={{ color: integration.color }} />
                      </Box>

                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        {integration.connected && (
                          <Tooltip title="Connected">
                            <Box
                              sx={{
                                width: 24,
                                height: 24,
                                borderRadius: "50%",
                                background: "hsla(160, 84%, 39%, 0.2)",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                              }}
                            >
                              <Check size={14} style={{ color: "hsl(160, 84%, 39%)" }} />
                            </Box>
                          </Tooltip>
                        )}

                        <Chip
                          label={integration.category}
                          size="small"
                          sx={{
                            textTransform: "capitalize",
                            background: isDark ? "hsla(239, 84%, 67%, 0.1)" : "hsla(239, 84%, 67%, 0.05)",
                            color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)",
                            fontSize: "0.75rem",
                          }}
                        />
                      </Box>
                    </Box>

                    {/* Content */}
                    <Typography
                      variant="h6"
                      sx={{
                        fontWeight: 600,
                        color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                        mb: 1,
                      }}
                    >
                      {integration.name}
                    </Typography>

                    <Typography
                      sx={{
                        fontSize: "0.875rem",
                        color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                        mb: 2,
                      }}
                    >
                      {integration.description}
                    </Typography>

                    {/* Features */}
                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mb: 3 }}>
                      {integration.features.map((feature, i) => (
                        <Chip
                          key={i}
                          label={feature}
                          size="small"
                          sx={{
                            background: isDark ? "hsla(239, 84%, 67%, 0.1)" : "hsla(239, 84%, 67%, 0.05)",
                            color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)",
                            fontSize: "0.6875rem",
                            height: 24,
                          }}
                        />
                      ))}
                    </Box>

                    {/* Actions */}
                    <Box sx={{ display: "flex", gap: 1 }}>
                      {integration.connected ? (
                        <>
                          <Button
                            onClick={() => handleSync(integration.id)}
                            variant="outlined"
                            size="small"
                            startIcon={<RefreshCw size={14} />}
                            sx={{
                              flex: 1,
                              borderColor: "hsla(239, 84%, 67%, 0.3)",
                              color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                              textTransform: "none",
                              fontWeight: 600,
                              borderRadius: "8px",
                              "&:hover": {
                                borderColor: "hsla(239, 84%, 67%, 0.5)",
                                background: "hsla(239, 84%, 67%, 0.05)",
                              },
                            }}
                          >
                            Sync
                          </Button>
                          <Button
                            onClick={() => handleConnect(integration.id, integration.provider)}
                            variant="outlined"
                            size="small"
                            disabled={integration.loading}
                            sx={{
                              borderColor: "hsla(346, 84%, 61%, 0.5)",
                              color: "hsl(346, 84%, 61%)",
                              textTransform: "none",
                              fontWeight: 600,
                              borderRadius: "8px",
                              "&:hover": {
                                borderColor: "hsl(346, 84%, 61%)",
                                background: "hsla(346, 84%, 61%, 0.1)",
                              },
                            }}
                          >
                            {integration.loading ? "..." : "Disconnect"}
                          </Button>
                        </>
                      ) : (
                        <Button
                          onClick={() => handleConnect(integration.id, integration.provider)}
                          variant="contained"
                          fullWidth
                          disabled={integration.loading}
                          sx={{
                            background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                            textTransform: "none",
                            fontWeight: 600,
                            borderRadius: "8px",
                            "&:hover": {
                              background: "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                            },
                          }}
                        >
                          {integration.loading ? "Connecting..." : "Connect"}
                        </Button>
                      )}
                    </Box>
                  </Paper>
                </motion.div>
              </Grid>
            ))}
          </Grid>
          )}

          {filteredIntegrations.length === 0 && !integrationsLoading && !integrationsError && (
            <Paper
              elevation={0}
              sx={{
                p: 6,
                textAlign: "center",
                background: isDark
                  ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                  : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                border: "1px solid hsla(239, 84%, 67%, 0.15)",
                borderRadius: "16px",
              }}
            >
              <Plug size={48} style={{ color: isDark ? "hsl(215, 16%, 40%)" : "hsl(215, 16%, 60%)", marginBottom: 16 }} />
              <Typography variant="h6" sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                No integrations found
              </Typography>
              <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                Try adjusting your filters or search for something else
              </Typography>
            </Paper>
          )}

          {/* API Section */}
          <Paper
            elevation={0}
            sx={{
              mt: 4,
              p: 3,
              background: isDark
                ? "linear-gradient(135deg, hsla(239, 84%, 67%, 0.1) 0%, hsla(330, 81%, 60%, 0.05) 100%)"
                : "linear-gradient(135deg, hsla(239, 84%, 67%, 0.05) 0%, hsla(330, 81%, 60%, 0.02) 100%)",
              border: "1px solid hsla(239, 84%, 67%, 0.2)",
              borderRadius: "16px",
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
              <Zap size={24} style={{ color: "hsl(239, 84%, 67%)" }} />
              <Typography variant="h6" sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                Developer API
              </Typography>
            </Box>
            <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)", mb: 2 }}>
              Build custom integrations using our REST API and webhooks.
            </Typography>
            <Button
              variant="outlined"
              endIcon={<ExternalLink size={16} />}
              sx={{
                borderColor: "hsla(239, 84%, 67%, 0.5)",
                color: "hsl(239, 84%, 67%)",
                textTransform: "none",
                fontWeight: 600,
                borderRadius: "10px",
                "&:hover": {
                  borderColor: "hsl(239, 84%, 67%)",
                  background: "hsla(239, 84%, 67%, 0.1)",
                },
              }}
            >
              View API Documentation
            </Button>
          </Paper>
        </motion.div>
      </Container>

      <BottomNav />
    </Box>
  );
}

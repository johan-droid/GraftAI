"use client";

import { Box, Button, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { LucideIcon, Plus, Calendar, Mail, Bell, Search, FolderOpen, Users, Zap } from "lucide-react";
import Link from "next/link";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
  secondaryAction?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  secondaryAction,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          p: { xs: 4, md: 6 },
          background: "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)",
          border: "1px solid hsla(239, 84%, 67%, 0.15)",
          borderRadius: 3,
        }}
      >
        {/* Icon Container */}
        <Box
          sx={{
            width: 80,
            height: 80,
            borderRadius: "24px",
            background: "linear-gradient(135deg, hsla(239, 84%, 67%, 0.15) 0%, hsla(330, 81%, 60%, 0.1) 100%)",
            border: "1px solid hsla(239, 84%, 67%, 0.2)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            mb: 3,
          }}
        >
          <Icon size={36} style={{ color: "hsl(239, 84%, 67%)" }} />
        </Box>

        {/* Title */}
        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            color: "hsl(220, 20%, 98%)",
            mb: 1,
            letterSpacing: "-0.01em",
          }}
        >
          {title}
        </Typography>

        {/* Description */}
        <Typography
          sx={{
            color: "hsl(215, 16%, 55%)",
            mb: 3,
            maxWidth: 400,
            lineHeight: 1.6,
          }}
        >
          {description}
        </Typography>

        {/* Actions */}
        <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", justifyContent: "center" }}>
          {action && (
            <>
              {action.href ? (
                <Link href={action.href} passHref legacyBehavior>
                  <Button
                    variant="contained"
                    sx={{
                      background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                      borderRadius: "12px",
                      textTransform: "none",
                      fontWeight: 600,
                      px: 3,
                      py: 1.5,
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      "&:hover": {
                        background: "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                      },
                    }}
                  >
                    <Plus size={18} />
                    {action.label}
                  </Button>
                </Link>
              ) : (
                <Button
                  variant="contained"
                  onClick={action.onClick}
                  sx={{
                    background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                    borderRadius: "12px",
                    textTransform: "none",
                    fontWeight: 600,
                    px: 3,
                    py: 1.5,
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    "&:hover": {
                      background: "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                    },
                  }}
                >
                  <Plus size={18} />
                  {action.label}
                </Button>
              )}
            </>
          )}

          {secondaryAction && (
            <>
              {secondaryAction.href ? (
                <Link href={secondaryAction.href} passHref legacyBehavior>
                  <Button
                    variant="outlined"
                    sx={{
                      borderColor: "hsla(239, 84%, 67%, 0.3)",
                      color: "hsl(220, 20%, 98%)",
                      borderRadius: "12px",
                      textTransform: "none",
                      fontWeight: 600,
                      px: 3,
                      py: 1.5,
                      "&:hover": {
                        borderColor: "hsla(239, 84%, 67%, 0.5)",
                        background: "hsla(239, 84%, 67%, 0.05)",
                      },
                    }}
                  >
                    {secondaryAction.label}
                  </Button>
                </Link>
              ) : (
                <Button
                  variant="outlined"
                  onClick={secondaryAction.onClick}
                  sx={{
                    borderColor: "hsla(239, 84%, 67%, 0.3)",
                    color: "hsl(220, 20%, 98%)",
                    borderRadius: "12px",
                    textTransform: "none",
                    fontWeight: 600,
                    px: 3,
                    py: 1.5,
                    "&:hover": {
                      borderColor: "hsla(239, 84%, 67%, 0.5)",
                      background: "hsla(239, 84%, 67%, 0.05)",
                    },
                  }}
                >
                  {secondaryAction.label}
                </Button>
              )}
            </>
          )}
        </Box>
      </Box>
    </motion.div>
  );
}

// Pre-built empty states for common scenarios
export function EmptyMeetings() {
  return (
    <EmptyState
      icon={Calendar}
      title="No meetings scheduled"
      description="You're all caught up! Schedule your next meeting to get started with AI-powered coordination."
      action={{ label: "Schedule Meeting", href: "/meetings/new" }}
    />
  );
}

export function EmptyNotifications() {
  return (
    <EmptyState
      icon={Bell}
      title="No new notifications"
      description="You're all caught up! We'll notify you when something important happens."
    />
  );
}

export function EmptySearch({ query }: { query: string }) {
  return (
    <EmptyState
      icon={Search}
      title="No results found"
      description={`We couldn't find anything matching "${query}". Try different keywords or filters.`}
    />
  );
}

export function EmptyEmails() {
  return (
    <EmptyState
      icon={Mail}
      title="No connected emails"
      description="Connect your email accounts to enable smart scheduling and automated follow-ups."
      action={{ label: "Connect Email", href: "/settings/integrations" }}
    />
  );
}

export function EmptyTeam() {
  return (
    <EmptyState
      icon={Users}
      title="No team members yet"
      description="Invite your colleagues to collaborate and coordinate schedules seamlessly."
      action={{ label: "Invite Members", href: "/team/invite" }}
      secondaryAction={{ label: "Learn More", href: "/docs/team" }}
    />
  );
}

export function EmptyIntegrations() {
  return (
    <EmptyState
      icon={Zap}
      title="No integrations connected"
      description="Connect your favorite tools to supercharge your scheduling workflow."
      action={{ label: "Browse Integrations", href: "/integrations" }}
    />
  );
}

export function EmptyFiles() {
  return (
    <EmptyState
      icon={FolderOpen}
      title="No files uploaded"
      description="Upload meeting recordings, transcripts, or documents to keep everything organized."
      action={{ label: "Upload Files", onClick: () => {} }}
    />
  );
}

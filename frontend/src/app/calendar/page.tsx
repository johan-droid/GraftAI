"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Box, Container, Paper, Typography, Button, IconButton, Grid, Chip } from "@mui/material";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  Plus,
  Clock,
  MapPin,
  Users,
  Video,
} from "lucide-react";
import Link from "next/link";
import { useTheme } from "@/contexts/ThemeContext";
import { useAuth } from "@/app/providers/auth-provider";
import { useQuery } from "@/hooks/useQuery";
import { MobileSidebar } from "@/components/dashboard/MobileSidebar";
import { BottomNav } from "@/components/dashboard/BottomNav";
import { Greeting } from "@/components/dashboard/Greeting";
import { Header } from "@/components/dashboard/Header";
import { SkeletonText } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";

// Calendar view types
type ViewType = "month" | "week" | "day";

// Event type
interface CalendarEvent {
  id: number;
  title: string;
  start_time: string;
  end_time?: string;
  category?: string;
  location?: string;
  is_virtual?: boolean;
  attendees?: number;
  description?: string;
}

// Events are fetched from /api/events endpoint
// No mock data - all real calendar data

export default function CalendarPage() {
  const router = useRouter();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const { isDark } = useTheme();
  
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewType, setViewType] = useState<ViewType>("month");
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

  // Fetch events
  const { data: events, isLoading: eventsLoading, error: eventsError } = useQuery<CalendarEvent[]>(
    isAuthenticated ? "/api/events" : null
  );

  // Use real events only - no mock fallback
  const displayEvents = events || [];

  // Global auth errors are handled by AuthProvider.


  // Calendar navigation
  const navigateCalendar = (direction: "prev" | "next") => {
    const newDate = new Date(currentDate);
    if (viewType === "month") {
      newDate.setMonth(newDate.getMonth() + (direction === "next" ? 1 : -1));
    } else if (viewType === "week") {
      newDate.setDate(newDate.getDate() + (direction === "next" ? 7 : -7));
    } else {
      newDate.setDate(newDate.getDate() + (direction === "next" ? 1 : -1));
    }
    setCurrentDate(newDate);
  };

  const goToToday = () => setCurrentDate(new Date());

  // Generate calendar days
  const getCalendarDays = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    const days = [];
    for (let i = 0; i < 42; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);
      days.push(date);
    }
    return days;
  };

  // Get events for a specific date
  const getEventsForDate = (date: Date) => {
    return displayEvents.filter((event) => {
      const eventDate = new Date(event.start_time);
      return (
        eventDate.getDate() === date.getDate() &&
        eventDate.getMonth() === date.getMonth() &&
        eventDate.getFullYear() === date.getFullYear()
      );
    });
  };

  // Format date display
  const formatMonthYear = (date: Date) => {
    return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
  };

  const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

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
              }}
            >
              Calendar
            </Typography>
            <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
              Manage your meetings and schedule
            </Typography>
          </Box>

          {/* Calendar Controls */}
          <Paper
            elevation={0}
            sx={{
              p: 2,
              mb: 3,
              background: isDark
                ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
              border: "1px solid hsla(239, 84%, 67%, 0.15)",
              borderRadius: "16px",
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              gap: 2,
            }}
          >
            {/* Navigation */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <IconButton
                onClick={() => navigateCalendar("prev")}
                sx={{
                  color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                  background: isDark ? "hsla(239, 84%, 67%, 0.1)" : "hsla(239, 84%, 67%, 0.05)",
                  "&:hover": { background: "hsla(239, 84%, 67%, 0.2)" },
                }}
              >
                <ChevronLeft size={20} />
              </IconButton>
              <Typography
                sx={{
                  fontWeight: 600,
                  fontSize: "1.125rem",
                  color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                  minWidth: 180,
                  textAlign: "center",
                }}
              >
                {formatMonthYear(currentDate)}
              </Typography>
              <IconButton
                onClick={() => navigateCalendar("next")}
                sx={{
                  color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                  background: isDark ? "hsla(239, 84%, 67%, 0.1)" : "hsla(239, 84%, 67%, 0.05)",
                  "&:hover": { background: "hsla(239, 84%, 67%, 0.2)" },
                }}
              >
                <ChevronRight size={20} />
              </IconButton>
            </Box>

            <Box sx={{ flex: 1 }} />

            {/* Today Button */}
            <Button
              onClick={goToToday}
              variant="outlined"
              sx={{
                borderColor: "hsla(239, 84%, 67%, 0.3)",
                color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                textTransform: "none",
                fontWeight: 600,
                borderRadius: "10px",
                "&:hover": {
                  borderColor: "hsla(239, 84%, 67%, 0.5)",
                  background: "hsla(239, 84%, 67%, 0.05)",
                },
              }}
            >
              Today
            </Button>

            {/* View Toggle */}
            <Box sx={{ display: "flex", gap: 0.5 }}>
              {(["month", "week", "day"] as ViewType[]).map((view) => (
                <Button
                  key={view}
                  onClick={() => setViewType(view)}
                  variant={viewType === view ? "contained" : "outlined"}
                  sx={{
                    textTransform: "capitalize",
                    fontWeight: 600,
                    borderRadius: "10px",
                    ...(viewType === view
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
                  {view}
                </Button>
              ))}
            </Box>

            {/* New Event */}
            <Button
              component={Link}
              href="/book"
              variant="contained"
              startIcon={<Plus size={18} />}
              sx={{
                background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                textTransform: "none",
                fontWeight: 600,
                borderRadius: "10px",
                "&:hover": {
                  background: "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                },
              }}
            >
              New Event
            </Button>
          </Paper>

          {/* Calendar Grid */}
          {eventsLoading ? (
            <SkeletonText lines={10} />
          ) : eventsError ? (
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
                Failed to load calendar events
              </Typography>
              <Button
                onClick={() => window.location.reload()}
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
          ) : displayEvents.length === 0 ? (
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
              <Box sx={{ mb: 3 }}>
                <CalendarIcon size={48} style={{ color: "hsl(239, 84%, 67%)", opacity: 0.5 }} />
              </Box>
              <Typography variant="h5" sx={{ mb: 2, fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                No meetings scheduled yet
              </Typography>
              <Typography sx={{ mb: 3, color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)", maxWidth: 400, mx: "auto" }}>
                Your calendar is ready to go! Here's how to get booked:
              </Typography>
              <Box sx={{ textAlign: "left", maxWidth: 400, mx: "auto", mb: 3, pl: 2 }}>
                <Typography sx={{ mb: 1, color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)", fontSize: "0.875rem" }}>
                  1. Create your scheduling link
                </Typography>
                <Typography sx={{ mb: 1, color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)", fontSize: "0.875rem" }}>
                  2. Share it in your email signature
                </Typography>
                <Typography sx={{ mb: 1, color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)", fontSize: "0.875rem" }}>
                  3. Post on LinkedIn or Twitter
                </Typography>
              </Box>
              <Button
                component={Link}
                href="/book"
                variant="contained"
                sx={{
                  background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                  textTransform: "none",
                  fontWeight: 600,
                  borderRadius: "8px",
                  px: 3,
                }}
              >
                Schedule Your First Meeting
              </Button>
            </Paper>
          ) : (
            <Paper
              elevation={0}
              sx={{
                background: isDark
                  ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                  : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                border: "1px solid hsla(239, 84%, 67%, 0.15)",
                borderRadius: "16px",
                overflow: "hidden",
              }}
            >
              {/* Week Day Headers */}
              <Grid container sx={{ borderBottom: "1px solid hsla(239, 84%, 67%, 0.1)" }}>
                {weekDays.map((day) => (
                  <Grid
                    key={day}
                    item
                    xs
                    sx={{
                      p: 2,
                      textAlign: "center",
                      fontWeight: 600,
                      color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                      fontSize: "0.875rem",
                    }}
                  >
                    {day}
                  </Grid>
                ))}
              </Grid>

              {/* Calendar Days */}
              <Grid container>
                {getCalendarDays().map((date, index) => {
                  const isCurrentMonth = date.getMonth() === currentDate.getMonth();
                  const isToday =
                    date.getDate() === new Date().getDate() &&
                    date.getMonth() === new Date().getMonth() &&
                    date.getFullYear() === new Date().getFullYear();
                  const dayEvents = getEventsForDate(date);

                  return (
                    <Grid
                      key={index}
                      item
                      xs
                      sx={{
                        minHeight: 120,
                        p: 1,
                        borderRight:
                          (index + 1) % 7 !== 0 ? "1px solid hsla(239, 84%, 67%, 0.1)" : "none",
                        borderBottom: "1px solid hsla(239, 84%, 67%, 0.1)",
                        background: isToday
                          ? isDark
                            ? "hsla(239, 84%, 67%, 0.1)"
                            : "hsla(239, 84%, 67%, 0.05)"
                          : "transparent",
                        opacity: isCurrentMonth ? 1 : 0.5,
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                        "&:hover": {
                          background: isDark
                            ? "hsla(239, 84%, 67%, 0.1)"
                            : "hsla(239, 84%, 67%, 0.05)",
                        },
                      }}
                    >
                      <Typography
                        sx={{
                          fontWeight: isToday ? 700 : 500,
                          color: isToday
                            ? "hsl(239, 84%, 67%)"
                            : isDark
                            ? "hsl(220, 20%, 98%)"
                            : "hsl(222, 47%, 11%)",
                          fontSize: "0.875rem",
                          mb: 1,
                          width: 28,
                          height: 28,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          borderRadius: "50%",
                          background: isToday ? "hsla(239, 84%, 67%, 0.2)" : "transparent",
                        }}
                      >
                        {date.getDate()}
                      </Typography>

                      {/* Events */}
                      <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                        {dayEvents.slice(0, 3).map((event) => (
                          <Box
                            key={event.id}
                            onClick={() => setSelectedEvent(event)}
                            sx={{
                              p: 0.5,
                              px: 1,
                              borderRadius: "6px",
                              fontSize: "0.6875rem",
                              fontWeight: 500,
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              cursor: "pointer",
                              background:
                                event.category === "work"
                                  ? "hsla(239, 84%, 67%, 0.2)"
                                  : event.category === "meeting"
                                  ? "hsla(25, 95%, 53%, 0.2)"
                                  : "hsla(160, 84%, 39%, 0.2)",
                              color:
                                event.category === "work"
                                  ? "hsl(239, 84%, 67%)"
                                  : event.category === "meeting"
                                  ? "hsl(25, 95%, 53%)"
                                  : "hsl(160, 84%, 39%)",
                              border: `1px solid ${
                                event.category === "work"
                                  ? "hsla(239, 84%, 67%, 0.3)"
                                  : event.category === "meeting"
                                  ? "hsla(25, 95%, 53%, 0.3)"
                                  : "hsla(160, 84%, 67%, 0.3)"
                              }`,
                              "&:hover": {
                                filter: "brightness(1.2)",
                              },
                            }}
                          >
                            {event.title}
                          </Box>
                        ))}
                        {dayEvents.length > 3 && (
                          <Typography
                            sx={{
                              fontSize: "0.6875rem",
                              color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                            }}
                          >
                            +{dayEvents.length - 3} more
                          </Typography>
                        )}
                      </Box>
                    </Grid>
                  );
                })}
              </Grid>
            </Paper>
          )}
        </motion.div>
      </Container>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <Box
          onClick={() => setSelectedEvent(null)}
          sx={{
            position: "fixed",
            inset: 0,
            background: "hsla(240, 24%, 7%, 0.8)",
            backdropFilter: "blur(4px)",
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            p: 2,
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            onClick={(e) => e.stopPropagation()}
          >
            <Paper
              sx={{
                p: 3,
                maxWidth: 400,
                width: "100%",
                background: isDark
                  ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                  : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
                border: "1px solid hsla(239, 84%, 67%, 0.2)",
                borderRadius: "16px",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
                <CalendarIcon size={20} style={{ color: "hsl(239, 84%, 67%)" }} />
                <Typography variant="h6" sx={{ fontWeight: 700, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                  {selectedEvent.title}
                </Typography>
              </Box>

              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                  <Clock size={16} style={{ color: "hsl(215, 16%, 55%)" }} />
                  <Typography sx={{ color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)" }}>
                    {new Date(selectedEvent.start_time).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                    {selectedEvent.end_time &&
                      ` - ${new Date(selectedEvent.end_time).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}`}
                  </Typography>
                </Box>

                {selectedEvent.location && (
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                    <MapPin size={16} style={{ color: "hsl(215, 16%, 55%)" }} />
                    <Typography sx={{ color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)" }}>
                      {selectedEvent.location}
                    </Typography>
                  </Box>
                )}

                {selectedEvent.is_virtual && (
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                    <Video size={16} style={{ color: "hsl(239, 84%, 67%)" }} />
                    <Typography sx={{ color: "hsl(239, 84%, 67%)" }}>Virtual Meeting</Typography>
                  </Box>
                )}

                {selectedEvent.attendees && (
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                    <Users size={16} style={{ color: "hsl(215, 16%, 55%)" }} />
                    <Typography sx={{ color: isDark ? "hsl(215, 16%, 70%)" : "hsl(215, 16%, 47%)" }}>
                      {selectedEvent.attendees} attendees
                    </Typography>
                  </Box>
                )}

                {selectedEvent.description && (
                  <Typography
                    sx={{
                      color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                      fontSize: "0.875rem",
                      mt: 1,
                    }}
                  >
                    {selectedEvent.description}
                  </Typography>
                )}

                <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
                  <Button
                    variant="contained"
                    fullWidth
                    sx={{
                      background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                      textTransform: "none",
                      fontWeight: 600,
                      borderRadius: "10px",
                    }}
                  >
                    Join Meeting
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => setSelectedEvent(null)}
                    sx={{
                      borderColor: "hsla(239, 84%, 67%, 0.3)",
                      color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                      textTransform: "none",
                      fontWeight: 600,
                      borderRadius: "10px",
                    }}
                  >
                    Close
                  </Button>
                </Box>
              </Box>
            </Paper>
          </motion.div>
        </Box>
      )}

      <BottomNav />
    </Box>
  );
}

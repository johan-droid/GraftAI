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
  Grid,
  Chip,
  Stepper,
  Step,
  StepLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
} from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import {
  Calendar,
  Clock,
  Users,
  Video,
  MapPin,
  ArrowRight,
  ArrowLeft,
  Plus,
  Check,
  Sparkles,
} from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { useAuth } from "@/app/providers/auth-provider";
import { MobileSidebar } from "@/components/dashboard/MobileSidebar";
import { BottomNav } from "@/components/dashboard/BottomNav";
import { Header } from "@/components/dashboard/Header";
import { toast } from "@/components/ui/Toast";
import { SuccessCelebration } from "@/components/ui/SuccessCelebration";

const steps = ["Meeting Details", "Date & Time", "Invitees", "Review"];

const durationOptions = [
  { value: 15, label: "15 minutes" },
  { value: 30, label: "30 minutes" },
  { value: 45, label: "45 minutes" },
  { value: 60, label: "1 hour" },
  { value: 90, label: "1.5 hours" },
  { value: 120, label: "2 hours" },
];

export default function BookMeetingPage() {
  const router = useRouter();
  const { user: authUser, isAuthenticated, loading: authLoading } = useAuth();
  const { isDark } = useTheme();

  const userName = authUser?.name ?? "";
  const userEmail = authUser?.email ?? "";
  const userAvatar = authUser?.avatar ?? "";

  const [activeStep, setActiveStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [createdMeeting, setCreatedMeeting] = useState<{
    title: string;
    date: string;
    time: string;
    duration: number;
  } | null>(null);

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("virtual");
  const [duration, setDuration] = useState(30);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [selectedTime, setSelectedTime] = useState<string>("");
  const [invitees, setInvitees] = useState<string[]>([]);
  const [newInvitee, setNewInvitee] = useState("");
  const [useAICopilot, setUseAICopilot] = useState(true);

  // Availability state from API
  const [timeSlots, setTimeSlots] = useState<{ time: string; available: boolean; reason?: string }[]>([]);
  const [availabilityLoading, setAvailabilityLoading] = useState(false);
  const [availabilityError, setAvailabilityError] = useState<string | null>(null);

  // Generate available dates (next 14 days)
  const availableDates = Array.from({ length: 14 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() + i);
    return date.toISOString().split("T")[0];
  });

  // Fetch availability when date or duration changes
  useEffect(() => {
    if (!isAuthenticated || !selectedDate) {
      setTimeSlots([]);
      return;
    }

    const fetchAvailability = async () => {
      setAvailabilityLoading(true);
      setAvailabilityError(null);
      try {
        const response = await fetch(
          `/api/calendar/availability/free-slots?date=${selectedDate}&duration=${duration}`,
          { credentials: "include" }
        );
        if (!response.ok) {
          throw new Error("Failed to fetch availability");
        }
        const data = await response.json();
        setTimeSlots(data.slots || []);
      } catch (error) {
        setAvailabilityError(error instanceof Error ? error.message : "Failed to load availability");
        // Fallback to empty slots - user can retry
        setTimeSlots([]);
      } finally {
        setAvailabilityLoading(false);
      }
    };

    fetchAvailability();
  }, [selectedDate, duration, isAuthenticated]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  const handleNext = () => {
    if (validateStep()) {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const validateStep = () => {
    switch (activeStep) {
      case 0:
        if (!title.trim()) {
          toast.error("Please enter a meeting title");
          return false;
        }
        return true;
      case 1:
        if (!selectedDate || !selectedTime) {
          toast.error("Please select a date and time");
          return false;
        }
        return true;
      case 2:
        return true;
      case 3:
        return true;
      default:
        return true;
    }
  };

  const addInvitee = () => {
    if (newInvitee && !invitees.includes(newInvitee) && newInvitee.includes("@")) {
      setInvitees([...invitees, newInvitee]);
      setNewInvitee("");
    } else if (newInvitee && !newInvitee.includes("@")) {
      toast.error("Please enter a valid email address");
    }
  };

  const removeInvitee = (email: string) => {
    setInvitees(invitees.filter((e) => e !== email));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      // Create event using real API
      if (!selectedDate || !selectedTime) {
        toast.error("Please select a date and time for your meeting");
        return;
      }

      // Parse the date and time to create start_time
      const [hours, minutes] = selectedTime.split(":").map(Number);
      const startDateTime = new Date(selectedDate);
      startDateTime.setHours(hours, minutes, 0, 0);
      
      // Calculate end time based on duration
      const endDateTime = new Date(startDateTime.getTime() + duration * 60000);

      const response = await fetch("/api/calendar/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          title: title,
          start_time: startDateTime.toISOString(),
          end_time: endDateTime.toISOString(),
          description: description,
          location: location,
          is_meeting: true,
          attendees: invitees,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to schedule meeting");
      }

      // Show success celebration instead of immediate redirect
      setCreatedMeeting({
        title: title,
        date: selectedDate,
        time: selectedTime,
        duration: duration,
      });
      setShowSuccess(true);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to schedule meeting. Please try again.");
    } finally {
      setIsSubmitting(false);
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

      <Container maxWidth="md" sx={{ px: { xs: 2, md: 4 }, py: { xs: 2, md: 4 } }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Header */}
          <Header
            userName={userName}
            userEmail={userEmail}
            userAvatar={userAvatar}
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
              <Calendar size={28} style={{ color: "hsl(239, 84%, 67%)" }} />
              Book a Meeting
            </Typography>
            <Typography sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
              Schedule a new meeting with AI-powered suggestions
            </Typography>
          </Box>

          {/* Stepper */}
          <Paper
            elevation={0}
            sx={{
              p: { xs: 2, md: 3 },
              mb: 3,
              background: isDark
                ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
              border: "1px solid hsla(239, 84%, 67%, 0.15)",
              borderRadius: "16px",
            }}
          >
            <Stepper activeStep={activeStep} alternativeLabel>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel
                    sx={{
                      "& .MuiStepLabel-label": {
                        color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                        fontSize: { xs: "0.75rem", md: "0.875rem" },
                      },
                      "& .Mui-active .MuiStepLabel-label": {
                        color: "hsl(239, 84%, 67%) !important",
                        fontWeight: 600,
                      },
                      "& .Mui-completed .MuiStepLabel-label": {
                        color: isDark ? "hsl(160, 84%, 39%)" : "hsl(160, 84%, 39%)",
                      },
                    }}
                  >
                    {label}
                  </StepLabel>
                </Step>
              ))}
            </Stepper>
          </Paper>

          {/* Form Content */}
          <Paper
            elevation={0}
            sx={{
              p: { xs: 2, md: 4 },
              background: isDark
                ? "linear-gradient(135deg, hsl(240, 24%, 14%) 0%, hsl(240, 24%, 10%) 100%)"
                : "linear-gradient(135deg, hsl(0, 0%, 100%) 0%, hsl(220, 14%, 96%) 100%)",
              border: "1px solid hsla(239, 84%, 67%, 0.15)",
              borderRadius: "16px",
            }}
          >
            <AnimatePresence mode="wait">
              {activeStep === 0 && (
                <motion.div
                  key="step0"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <Typography variant="h6" sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)", mb: 3 }}>
                    Meeting Details
                  </Typography>

                  <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                    <TextField
                      fullWidth
                      label="Meeting Title"
                      placeholder="e.g., Weekly Team Sync"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
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

                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      label="Description (Optional)"
                      placeholder="Add meeting agenda or notes..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
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

                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <FormControl fullWidth>
                          <InputLabel sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                            Location
                          </InputLabel>
                          <Select
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            sx={{
                              borderRadius: "10px",
                              color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                              "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.3)" },
                            }}
                          >
                            <MenuItem value="virtual">
                              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                                <Video size={16} />
                                Virtual (Zoom/Teams)
                              </Box>
                            </MenuItem>
                            <MenuItem value="in-person">
                              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                                <MapPin size={16} />
                                In-Person
                              </Box>
                            </MenuItem>
                            <MenuItem value="phone">
                              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                                <Users size={16} />
                                Phone Call
                              </Box>
                            </MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <FormControl fullWidth>
                          <InputLabel sx={{ color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                            Duration
                          </InputLabel>
                          <Select
                            value={duration}
                            onChange={(e) => setDuration(Number(e.target.value))}
                            sx={{
                              borderRadius: "10px",
                              color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                              "& fieldset": { borderColor: "hsla(239, 84%, 67%, 0.3)" },
                            }}
                          >
                            {durationOptions.map((opt) => (
                              <MenuItem key={opt.value} value={opt.value}>
                                {opt.label}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>
                    </Grid>
                  </Box>
                </motion.div>
              )}

              {activeStep === 1 && (
                <motion.div
                  key="step1"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <Typography variant="h6" sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)", mb: 3 }}>
                    Select Date & Time
                  </Typography>

                  <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                    <Box>
                      <Typography sx={{ mb: 2, color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                        Available Dates
                      </Typography>
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                        {availableDates.map((date) => {
                          const isSelected = selectedDate === date;
                          const dateObj = new Date(date);
                          const dayName = dateObj.toLocaleDateString("en-US", { weekday: "short" });
                          const dayNum = dateObj.getDate();

                          return (
                            <Paper
                              key={date}
                              onClick={() => setSelectedDate(date)}
                              elevation={0}
                              sx={{
                                p: 1.5,
                                minWidth: 60,
                                textAlign: "center",
                                cursor: "pointer",
                                background: isSelected
                                  ? "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)"
                                  : isDark
                                  ? "hsla(239, 84%, 67%, 0.1)"
                                  : "hsla(239, 84%, 67%, 0.05)",
                                border: `1px solid ${isSelected ? "transparent" : "hsla(239, 84%, 67%, 0.2)"}`,
                                borderRadius: "10px",
                                transition: "all 0.2s ease",
                                "&:hover": {
                                  background: isSelected
                                    ? "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)"
                                    : "hsla(239, 84%, 67%, 0.15)",
                                },
                              }}
                            >
                              <Typography
                                sx={{
                                  fontSize: "0.75rem",
                                  color: isSelected ? "white" : isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)",
                                }}
                              >
                                {dayName}
                              </Typography>
                              <Typography
                                sx={{
                                  fontSize: "1.25rem",
                                  fontWeight: 700,
                                  color: isSelected ? "white" : isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)",
                                }}
                              >
                                {dayNum}
                              </Typography>
                            </Paper>
                          );
                        })}
                      </Box>
                    </Box>

                    {selectedDate && (
                      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                        <Typography sx={{ mb: 2, color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
                          Available Times
                          {availabilityLoading && (
                            <Typography component="span" sx={{ ml: 1, fontSize: "0.75rem", color: "text.secondary" }}>
                              (Loading...)
                            </Typography>
                          )}
                        </Typography>

                        {availabilityError && (
                          <Box sx={{ mb: 2, p: 2, background: "hsla(346, 84%, 61%, 0.1)", borderRadius: "8px" }}>
                            <Typography sx={{ color: "hsl(346, 84%, 61%)", fontSize: "0.875rem" }}>
                              {availabilityError}
                            </Typography>
                          </Box>
                        )}

                        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                          {timeSlots.map((slot) => {
                            const isSelected = selectedTime === slot.time;
                            const isAvailable = slot.available;
                            return (
                              <Chip
                                key={slot.time}
                                label={slot.time}
                                onClick={() => isAvailable && setSelectedTime(slot.time)}
                                disabled={!isAvailable || availabilityLoading}
                                sx={{
                                  px: 1,
                                  background: isSelected
                                    ? "hsl(239, 84%, 67%)"
                                    : !isAvailable
                                    ? isDark
                                      ? "hsla(0, 0%, 30%, 0.2)"
                                      : "hsla(0, 0%, 80%, 0.3)"
                                    : isDark
                                    ? "hsla(239, 84%, 67%, 0.1)"
                                    : "hsla(239, 84%, 67%, 0.05)",
                                  color: isSelected
                                    ? "white"
                                    : !isAvailable
                                    ? isDark
                                      ? "hsla(0, 0%, 60%, 0.5)"
                                      : "hsla(0, 0%, 50%, 0.5)"
                                    : isDark
                                    ? "hsl(220, 20%, 98%)"
                                    : "hsl(222, 47%, 11%)",
                                  border: `1px solid ${
                                    isSelected ? "transparent" : !isAvailable ? "transparent" : "hsla(239, 84%, 67%, 0.2)"
                                  }`,
                                  borderRadius: "8px",
                                  fontWeight: isSelected ? 600 : 400,
                                  cursor: isAvailable ? "pointer" : "not-allowed",
                                  textDecoration: !isAvailable ? "line-through" : "none",
                                  "&:hover": isAvailable
                                    ? {
                                        background: isSelected
                                          ? "hsl(239, 84%, 57%)"
                                          : isDark
                                          ? "hsla(239, 84%, 67%, 0.2)"
                                          : "hsla(239, 84%, 67%, 0.15)",
                                      }
                                    : {},
                                }}
                              />
                            );
                          })}
                        </Box>
                      </motion.div>
                    )}

                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={useAICopilot}
                          onChange={(e) => setUseAICopilot(e.target.checked)}
                          sx={{
                            color: "hsla(239, 84%, 67%, 0.5)",
                            "&.Mui-checked": { color: "hsl(239, 84%, 67%)" },
                          }}
                        />
                      }
                      label={
                        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                          <Sparkles size={16} style={{ color: "hsl(239, 84%, 67%)" }} />
                          <Typography sx={{ color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)" }}>
                            Use AI Copilot to optimize this meeting
                          </Typography>
                        </Box>
                      }
                    />
                  </Box>
                </motion.div>
              )}

              {activeStep === 2 && (
                <motion.div
                  key="step2"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <Typography variant="h6" sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)", mb: 3 }}>
                    Invite Attendees
                  </Typography>

                  <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                    <Box sx={{ display: "flex", gap: 1 }}>
                      <TextField
                        fullWidth
                        label="Email Address"
                        placeholder="colleague@company.com"
                        value={newInvitee}
                        onChange={(e) => setNewInvitee(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addInvitee();
                          }
                        }}
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
                      <Button
                        onClick={addInvitee}
                        variant="contained"
                        sx={{
                          minWidth: 48,
                          background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                          borderRadius: "10px",
                          "&:hover": {
                            background: "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                          },
                        }}
                      >
                        <Plus size={20} />
                      </Button>
                    </Box>

                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                      {invitees.map((email) => (
                        <Chip
                          key={email}
                          label={email}
                          onDelete={() => removeInvitee(email)}
                          sx={{
                            background: "hsla(239, 84%, 67%, 0.15)",
                            color: "hsl(239, 84%, 67%)",
                            borderRadius: "8px",
                            fontWeight: 500,
                            "& .MuiChip-deleteIcon": {
                              color: "hsl(239, 84%, 67%)",
                              "&:hover": { color: "hsl(346, 84%, 61%)" },
                            },
                          }}
                        />
                      ))}
                    </Box>

                    {invitees.length === 0 && (
                      <Typography sx={{ textAlign: "center", color: isDark ? "hsl(215, 16%, 40%)" : "hsl(215, 16%, 60%)" }}>
                        No invitees added yet. You can add them later.
                      </Typography>
                    )}
                  </Box>
                </motion.div>
              )}

              {activeStep === 3 && (
                <motion.div
                  key="step3"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <Typography variant="h6" sx={{ fontWeight: 600, color: isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)", mb: 3 }}>
                    Review & Confirm
                  </Typography>

                  <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                    <ReviewItem label="Title" value={title} icon={Calendar} />
                    <ReviewItem label="Description" value={description || "No description"} />
                    <ReviewItem
                      label="When"
                      value={`${selectedDate} at ${selectedTime} (${duration} min)`}
                      icon={Clock}
                    />
                    <ReviewItem
                      label="Where"
                      value={location === "virtual" ? "Virtual Meeting" : location === "in-person" ? "In-Person" : "Phone Call"}
                      icon={location === "virtual" ? Video : location === "in-person" ? MapPin : Users}
                    />
                    <ReviewItem
                      label="Attendees"
                      value={invitees.length > 0 ? `${invitees.length} invitee${invitees.length > 1 ? "s" : ""}` : "Just you"}
                      icon={Users}
                    />
                    <ReviewItem
                      label="AI Copilot"
                      value={useAICopilot ? "Enabled" : "Disabled"}
                      icon={Sparkles}
                      valueColor={useAICopilot ? "hsl(239, 84%, 67%)" : undefined}
                    />
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>

      {/* Success Celebration Modal */}
      <SuccessCelebration
        isOpen={showSuccess}
        onClose={() => {
          setShowSuccess(false);
          // Reset form for another booking
          setActiveStep(0);
          setTitle("");
          setDescription("");
          setLocation("virtual");
          setSelectedDate("");
          setSelectedTime("");
          setInvitees([]);
          setCreatedMeeting(null);
        }}
        meetingDetails={createdMeeting || {
          title: title,
          date: selectedDate,
          time: selectedTime,
          duration: duration,
        }}
        onViewCalendar={() => {
          setShowSuccess(false);
          router.push("/calendar");
        }}
      />
      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2, flexWrap: "wrap", mt: 4 }}>
        <Button
          onClick={handleBack}
          disabled={activeStep === 0}
          startIcon={<ArrowLeft size={18} />}
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
            "&:disabled": {
              borderColor: "transparent",
              color: isDark ? "hsl(215, 16%, 30%)" : "hsl(215, 16%, 70%)",
            },
          }}
        >
          Back
        </Button>

              {activeStep === steps.length - 1 ? (
                <Button
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  variant="contained"
                  endIcon={isSubmitting ? undefined : <Check size={18} />}
                  sx={{
                    background: "linear-gradient(135deg, hsl(239, 84%, 67%) 0%, hsl(330, 81%, 60%) 100%)",
                    textTransform: "none",
                    fontWeight: 600,
                    borderRadius: "10px",
                    px: 4,
                    "&:hover": {
                      background: "linear-gradient(135deg, hsl(239, 84%, 57%) 0%, hsl(330, 81%, 50%) 100%)",
                    },
                  }}
                >
                  {isSubmitting ? "Scheduling..." : "Schedule Meeting"}
                </Button>
              ) : (
                <Button
                  onClick={handleNext}
                  variant="contained"
                  endIcon={<ArrowRight size={18} />}
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
                  Continue
                </Button>
              )}
            </Box>
          </Paper>
        </motion.div>
      </Container>

      <BottomNav />
    </Box>
  );
}

function ReviewItem({
  label,
  value,
  icon: Icon,
  valueColor,
}: {
  label: string;
  value: string;
  icon?: typeof Calendar;
  valueColor?: string;
}) {
  const { isDark } = useTheme();

  return (
    <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2, p: 2, borderRadius: "10px", background: isDark ? "hsla(239, 84%, 67%, 0.05)" : "hsla(239, 84%, 67%, 0.03)" }}>
      {Icon && <Icon size={20} style={{ color: "hsl(239, 84%, 67%)", marginTop: 2 }} />}
      <Box>
        <Typography sx={{ fontSize: "0.875rem", color: isDark ? "hsl(215, 16%, 55%)" : "hsl(215, 16%, 47%)" }}>
          {label}
        </Typography>
        <Typography sx={{ fontWeight: 600, color: valueColor || (isDark ? "hsl(220, 20%, 98%)" : "hsl(222, 47%, 11%)") }}>
          {value}
        </Typography>
      </Box>
    </Box>
  );
}

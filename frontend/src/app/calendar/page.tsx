"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Box, Container, Typography, Button, IconButton, Grid, Stack } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  Plus,
  Clock,
  MapPin,
  Users,
  Video,
  Activity,
  Terminal,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/app/providers/auth-provider";
import { useQuery } from "@/hooks/useQuery";
import { MobileSidebar } from "@/components/dashboard/MobileSidebar";
import { BottomNav } from "@/components/dashboard/BottomNav";
import { Header } from "@/components/dashboard/Header";
import { SkeletonText } from "@/components/ui/Skeleton";

// Calendar view types
type ViewType = "MONTH" | "WEEK" | "DAY";

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

export default function CalendarPage() {
  const router = useRouter();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewType, setViewType] = useState<ViewType>("MONTH");
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

  // Fetch events
  const { data: events, isLoading: eventsLoading, error: eventsError } = useQuery<CalendarEvent[]>(
    isAuthenticated ? "/api/events" : null
  );

  const displayEvents = events || [];

  // Calendar navigation
  const navigateCalendar = (direction: "prev" | "next") => {
    const newDate = new Date(currentDate);
    if (viewType === "MONTH") {
      newDate.setMonth(newDate.getMonth() + (direction === "next" ? 1 : -1));
    } else if (viewType === "WEEK") {
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

  const formatMonthYear = (date: Date) => {
    return date.toLocaleDateString("en-US", { month: "long", year: "numeric" }).toUpperCase();
  };

  const weekDays = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

  if (authLoading) {
    return (
      <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg-base)" }}>
        <div className="flex flex-col items-center gap-4">
           <div className="w-8 h-8 border-2 border-[var(--primary)] border-t-transparent animate-spin" />
           <div className="text-[10px] font-black text-[var(--primary)] font-mono tracking-widest uppercase">BOOTING_CALENDAR...</div>
        </div>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: "100vh", background: "var(--bg-surface)", pb: { xs: 12, md: 4 } }}>
      <MobileSidebar />
      <Box className="scanline" sx={{ display: "none" }} />

      <Container maxWidth="xl" sx={{ px: { xs: 2.5, md: 4 }, py: { xs: 2.5, md: 6 } }}>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          
          <Header
            userName={user?.name}
            userEmail={user?.email}
            userAvatar={user?.avatar}
            notificationCount={0}
          />

          {/* Controller Section */}
          <Box sx={{ mb: 4, mt: 4 }}>
             <Typography variant="h4" sx={{ fontWeight: 600, color: "var(--text-primary)", fontFamily: "var(--font-outfit)", letterSpacing: "-0.02em" }}>
                {formatMonthYear(currentDate)}
             </Typography>
          </Box>

          <Box sx={{ display: "flex", flexDirection: { xs: "column", lg: "row" }, gap: 4 }}>
            
            {/* Left Column: Grid Controls */}
            <Box sx={{ flex: 1 }}>
              <Box sx={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: 3, p: 0, overflow: "hidden", boxShadow: "0 4px 20px rgba(0,0,0,0.03)" }}>
                {/* Grid Header Controls */}
                <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", p: 2, borderBottom: "1px solid var(--border-subtle)", background: "var(--bg-hover)" }}>
                   <Stack direction="row" spacing={1}>
                     <IconButton onClick={() => navigateCalendar("prev")} sx={{ color: "var(--text-secondary)", border: "1px solid var(--border-subtle)", p: 1 }}>
                        <ChevronLeft size={20} />
                     </IconButton>
                     <IconButton onClick={() => navigateCalendar("next")} sx={{ color: "var(--text-secondary)", border: "1px solid var(--border-subtle)", p: 1 }}>
                        <ChevronRight size={20} />
                     </IconButton>
                   </Stack>

                   <Stack direction="row" spacing={1}>
                     {(["MONTH", "WEEK", "DAY"] as ViewType[]).map((v) => (
                       <Button
                         key={v}
                         variant={viewType === v ? "contained" : "text"}
                         onClick={() => setViewType(v)}
                         disableElevation
                         sx={{
                           minWidth: 0,
                           fontSize: "0.8rem",
                           fontWeight: 600,
                           px: 2,
                           color: viewType === v ? "#fff" : "var(--text-secondary)",
                           bgcolor: viewType === v ? "var(--primary)" : "transparent",
                           "&:hover": {
                             bgcolor: viewType === v ? "var(--primary-hover)" : "var(--bg-hover)",
                           }
                         }}
                       >
                         {v}
                       </Button>
                     ))}
                     <Button 
                       onClick={goToToday}
                       variant="outlined"
                       sx={{
                         fontSize: "0.8rem",
                         fontWeight: 600,
                         px: 2,
                         borderColor: "var(--border-subtle)",
                         color: "var(--text-primary)",
                       }}
                     >
                       TODAY
                     </Button>
                   </Stack>
                </Box>

                {/* Main Grid */}
                {eventsLoading ? (
                  <Box sx={{ p: 4 }}><SkeletonText lines={15} /></Box>
                ) : (
                  <Box sx={{ p: 0 }}>
                    {/* Week Header */}
                    <Grid container sx={{ borderBottom: "1px solid var(--border-subtle)" }}>
                      {weekDays.map((day) => (
                        <Grid item xs={12 / 7} key={day} sx={{ p: 1.5, textAlign: "center", borderRight: day !== "SAT" ? "1px solid var(--border-subtle)" : "none" }}>
                          <Typography sx={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)" }}>{day}</Typography>
                        </Grid>
                      ))}
                    </Grid>

                    {/* Days Grid */}
                    <Grid container sx={{ flexWrap: "wrap" }}>
                      {getCalendarDays().map((date, idx) => {
                        const isCurrentMonth = date.getMonth() === currentDate.getMonth();
                        const isToday = date.toDateString() === new Date().toDateString();
                        const dayEvents = getEventsForDate(date);
                        
                        return (
                          <Grid
                            item
                            xs={12 / 7}
                            key={idx}
                            sx={{
                              minHeight: { xs: 100, md: 140 },
                              p: 1.5,
                              borderRight: (idx + 1) % 7 !== 0 ? "1px solid var(--border-subtle)" : "none",
                              borderBottom: idx < 35 ? "1px solid var(--border-subtle)" : "none",
                              opacity: isCurrentMonth ? 1 : 0.4,
                              background: isToday ? "rgba(26, 115, 232, 0.04)" : "transparent",
                              transition: "all 0.2s",
                              cursor: "pointer",
                              "&:hover": { background: "var(--bg-hover)" }
                            }}
                          >
                            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 1 }}>
                               <Typography 
                                 sx={{ 
                                   fontSize: "0.85rem", 
                                   fontWeight: isToday ? 700 : 500, 
                                   color: isToday ? "var(--primary)" : "var(--text-primary)",
                                   width: 24,
                                   height: 24,
                                   display: "flex",
                                   alignItems: "center",
                                   justifyContent: "center",
                                   borderRadius: "50%",
                                   bgcolor: isToday ? "rgba(26, 115, 232, 0.1)" : "transparent"
                                 }}
                               >
                                  {date.getDate()}
                               </Typography>
                            </Box>

                            <Stack spacing={0.5}>
                               {dayEvents.slice(0, 3).map((e) => (
                                 <Box
                                   key={e.id}
                                   onClick={(ev) => { ev.stopPropagation(); setSelectedEvent(e); }}
                                   sx={{
                                     fontSize: "0.7rem",
                                     px: 1,
                                     py: 0.25,
                                     borderRadius: 1,
                                     bgcolor: "var(--primary-glow)",
                                     color: "var(--primary)",
                                     overflow: "hidden",
                                     textOverflow: "ellipsis",
                                     whiteSpace: "nowrap",
                                     "&:hover": { bgcolor: "rgba(26, 115, 232, 0.15)" }
                                   }}
                                 >
                                   {e.title}
                                 </Box>
                               ))}
                               {dayEvents.length > 3 && (
                                 <Typography sx={{ fontSize: "0.65rem", fontWeight: 600, color: "var(--text-muted)", mt: 0.5 }}>
                                   + {dayEvents.length - 3} more
                                 </Typography>
                               )}
                            </Stack>
                          </Grid>
                        );
                      })}
                    </Grid>
                  </Box>
                )}
              </Box>
            </Box>

            {/* Right Column: Information Panel */}
            <Box sx={{ width: { xs: "100%", lg: 320 } }}>
               <Box sx={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: 3, p: 3, mb: 4, boxShadow: "0 4px 20px rgba(0,0,0,0.03)" }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3, pb: 2, borderBottom: "1px solid var(--border-subtle)" }}>
                     <CalendarIcon size={18} className="text-[#1a73e8]" />
                     <Typography sx={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)" }}>Schedule Meetings</Typography>
                  </Box>
                  <Typography sx={{ color: "var(--text-secondary)", fontSize: "0.9rem", mb: 4, lineHeight: 1.6 }}>
                     Create and manage your upcoming events. Copilot can automatically find the best times for you and your team.
                  </Typography>
                  <Button
                    component={Link}
                    href="/dashboard/book"
                    variant="contained"
                    fullWidth
                    disableElevation
                    sx={{
                      bgcolor: "var(--primary)",
                      color: "#fff",
                      fontWeight: 500,
                      py: 1.2,
                      borderRadius: 1.5,
                      textTransform: "none",
                      "&:hover": { bgcolor: "var(--primary-hover, rgba(26,115,232,0.9))" }
                    }}
                  >
                    Create Event
                  </Button>
               </Box>

               <Box sx={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)", borderRadius: 3, p: 3, boxShadow: "0 4px 20px rgba(0,0,0,0.03)" }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3, pb: 2, borderBottom: "1px solid var(--border-subtle)" }}>
                     <Activity size={18} className="text-[var(--text-secondary)]" />
                     <Typography sx={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)" }}>Calendar Sync</Typography>
                  </Box>
                  <Stack spacing={2}>
                     {[
                       { label: "Status", val: "Connected", color: "var(--success)" },
                       { label: "Events Synced", val: displayEvents.length.toString(), color: "var(--text-primary)" },
                       { label: "Last Update", val: "Just now", color: "var(--text-primary)" },
                     ].map((l, i) => (
                       <Box key={i} sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <Typography sx={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{l.label}</Typography>
                          <Typography sx={{ fontSize: "0.85rem", fontWeight: 600, color: l.color }}>{l.val}</Typography>
                       </Box>
                     ))}
                  </Stack>
               </Box>
            </Box>

          </Box>
        </motion.div>
      </Container>

      {/* Global Event Modal Overlay */}
      <AnimatePresence>
         {selectedEvent && (
           <Box
             component={motion.div}
             initial={{ opacity: 0 }}
             animate={{ opacity: 1 }}
             exit={{ opacity: 0 }}
             onClick={() => setSelectedEvent(null)}
             sx={{
               position: "fixed",
               inset: 0,
               background: "rgba(0,0,0,0.4)",
               backdropFilter: "none",
               zIndex: 2000,
               display: "flex",
               alignItems: "center",
               justifyContent: "center",
               p: 2.5
             }}
           >
             <Box
               component={motion.div}
               initial={{ scale: 0.95, y: 20 }}
               animate={{ scale: 1, y: 0 }}
               exit={{ scale: 0.95, y: 20 }}
               onClick={(e) => e.stopPropagation()}
               sx={{
                 width: "100%",
                 maxWidth: 400,
                 background: "var(--bg-card)",
                 border: "1px solid var(--border-subtle)",
                 borderRadius: 3,
                 p: 3,
                 position: "relative",
                 boxShadow: "0 12px 40px rgba(0,0,0,0.12)"
               }}
             >
                <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3, pb: 2, borderBottom: "1px solid var(--border-subtle)" }}>
                   <CalendarIcon size={20} className="text-[#1a73e8]" />
                   <Typography sx={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary)" }}>
                      Event Details
                   </Typography>
                </Box>

                <Stack spacing={3}>
                   <Box>
                      <Typography sx={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", mb: 0.5 }}>Title</Typography>
                      <Typography sx={{ fontSize: "1.15rem", fontWeight: 600, color: "var(--text-primary)", lineHeight: 1.3 }}>{selectedEvent.title}</Typography>
                   </Box>

                   <Grid container spacing={2}>
                      <Grid item xs={6}>
                         <Typography sx={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", mb: 0.5 }}>Time</Typography>
                         <Box sx={{ display: "flex", alignItems: "center", gap: 1, color: "var(--text-primary)" }}>
                            <Clock size={16} className="text-[#1a73e8]" />
                            <Typography sx={{ fontSize: "0.9rem", fontWeight: 500 }}>
                               {new Date(selectedEvent.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </Typography>
                         </Box>
                      </Grid>
                      <Grid item xs={6}>
                         <Typography sx={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", mb: 0.5 }}>Location</Typography>
                         <Box sx={{ display: "flex", alignItems: "center", gap: 1, color: "var(--text-primary)" }}>
                            <MapPin size={16} className="text-[#1a73e8]" />
                            <Typography sx={{ fontSize: "0.9rem", fontWeight: 500 }}>
                               {selectedEvent.location || "N/A"}
                            </Typography>
                         </Box>
                      </Grid>
                   </Grid>

                   {selectedEvent.description && (
                     <Box>
                        <Typography sx={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", mb: 0.5 }}>Description</Typography>
                        <Box sx={{ p: 2, bgcolor: "var(--bg-hover)", borderRadius: 2, borderLeft: "2px solid #1a73e8" }}>
                           <Typography sx={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                              {selectedEvent.description}
                           </Typography>
                        </Box>
                     </Box>
                   )}

                   <Box sx={{ display: "flex", gap: 2, pt: 2 }}>
                     <Button 
                        variant="contained" 
                        fullWidth 
                        disableElevation
                        sx={{ bgcolor: "var(--primary)", color: "#fff", textTransform: "none", fontWeight: 500, borderRadius: 2 }}
                     >
                        Join Meeting
                     </Button>
                     <Button 
                        onClick={() => setSelectedEvent(null)} 
                        variant="outlined" 
                        fullWidth
                        sx={{ borderColor: "var(--border-subtle)", color: "var(--text-primary)", textTransform: "none", fontWeight: 500, borderRadius: 2 }}
                     >
                        Close
                     </Button>
                   </Box>
                </Stack>
             </Box>
           </Box>
         )}
      </AnimatePresence>

      <BottomNav />
    </Box>
  );
}

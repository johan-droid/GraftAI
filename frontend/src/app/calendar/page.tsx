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
    <Box sx={{ minHeight: "100vh", background: "var(--bg-base)", pb: { xs: 12, md: 4 } }}>
      <MobileSidebar />
      <Box className="scanline" sx={{ opacity: 0.05 }} />

      <Container maxWidth="xl" sx={{ px: { xs: 2.5, md: 4 }, py: { xs: 2.5, md: 6 } }}>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          
          <Header
            userName={user?.name}
            userEmail={user?.email}
            userAvatar={user?.avatar}
            notificationCount={0}
          />

          {/* Controller Section */}
          <Box sx={{ mb: 6, mt: 4 }}>
             <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-[1px] bg-[var(--primary)]" />
                <span className="text-[9px] font-black text-[var(--primary)] tracking-[.4em] uppercase font-mono">Kernel_Scheduling_Node</span>
             </div>
             <Typography variant="h4" sx={{ fontWeight: 900, color: "white", fontFamily: "var(--font-mono)", textTransform: "uppercase", letterSpacing: "-0.04em" }}>
                Active_Protocol: <Box component="span" sx={{ color: "var(--primary)" }}>{formatMonthYear(currentDate)}</Box>
             </Typography>
          </Box>

          <Box sx={{ display: "flex", flexDirection: { xs: "column", lg: "row" }, gap: 4 }}>
            
            {/* Left Column: Grid Controls */}
            <Box sx={{ flex: 1 }}>
              <Box sx={{ background: "#050505", border: "1px dashed var(--border-subtle)", p: 0 }}>
                {/* Grid Header Controls */}
                <Box sx={{ display: "flex", alignItems: "center", justifyBetween: "between", p: 2.5, borderBottom: "1px dashed var(--border-subtle)", background: "rgba(255,255,255,0.02)" }}>
                   <Stack direction="row" spacing={1} sx={{ mr: "auto" }}>
                     <IconButton onClick={() => navigateCalendar("prev")} sx={{ color: "var(--text-primary)", border: "1px solid var(--border-subtle)", borderRadius: 0, p: 1 }}>
                        <ChevronLeft size={16} />
                     </IconButton>
                     <IconButton onClick={() => navigateCalendar("next")} sx={{ color: "var(--text-primary)", border: "1px solid var(--border-subtle)", borderRadius: 0, p: 1 }}>
                        <ChevronRight size={16} />
                     </IconButton>
                   </Stack>

                   <Stack direction="row" spacing={2} sx={{ ml: "auto" }}>
                     {(["MONTH", "WEEK", "DAY"] as ViewType[]).map((v) => (
                       <button
                         key={v}
                         onClick={() => setViewType(v)}
                         className={`text-[9px] font-black font-mono tracking-widest px-4 py-1.5 transition-all ${viewType === v ? "bg-[var(--primary)] text-black" : "text-[var(--text-faint)] hover:text-white"}`}
                       >
                         {v}
                       </button>
                     ))}
                     <button onClick={goToToday} className="text-[9px] font-black font-mono tracking-widest px-4 py-1.5 border border-dashed border-[var(--border-subtle)] text-[var(--primary)] hover:bg-[var(--primary)] hover:text-black transition-all">
                       TODAY
                     </button>
                   </Stack>
                </Box>

                {/* Main Grid */}
                {eventsLoading ? (
                  <Box sx={{ p: 4 }}><SkeletonText lines={15} /></Box>
                ) : (
                  <Box sx={{ p: 0 }}>
                    {/* Week Header */}
                    <Grid container sx={{ borderBottom: "1px dashed var(--border-subtle)" }}>
                      {weekDays.map((day) => (
                        <Grid item xs={12 / 7} key={day} sx={{ p: 1.5, textAlign: "center", borderRight: day !== "SAT" ? "1px dashed var(--border-subtle)" : "none" }}>
                          <span className="text-[9px] font-black text-[var(--text-faint)] font-mono tracking-[0.2em]">{day}</span>
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
                              borderRight: (idx + 1) % 7 !== 0 ? "1px dashed var(--border-subtle)" : "none",
                              borderBottom: idx < 35 ? "1px dashed var(--border-subtle)" : "none",
                              opacity: isCurrentMonth ? 1 : 0.25,
                              background: isToday ? "rgba(0, 255, 156, 0.03)" : "transparent",
                              transition: "all 0.1s",
                              cursor: "pointer",
                              "&:hover": { background: "rgba(255,255,255,0.02)" }
                            }}
                          >
                            <div className="flex justify-between items-start mb-2">
                               <span className={`text-[11px] font-black font-mono ${isToday ? "text-[var(--primary)]" : "text-[var(--text-muted)]"}`}>
                                  {date.getDate().toString().padStart(2, '0')}
                               </span>
                               {isToday && <div className="w-1 h-1 bg-[var(--primary)]" />}
                            </div>

                            <div className="space-y-1">
                               {dayEvents.slice(0, 3).map((e) => (
                                 <div
                                   key={e.id}
                                   onClick={(ev) => { ev.stopPropagation(); setSelectedEvent(e); }}
                                   className="text-[9px] font-mono px-2 py-0.5 border-l-2 border-[var(--primary)] bg-black/40 text-[var(--text-secondary)] truncate hover:bg-[var(--primary)] hover:text-black cursor-pointer uppercase font-black"
                                 >
                                   {e.title}
                                 </div>
                               ))}
                               {dayEvents.length > 3 && (
                                 <div className="text-[8px] font-bold text-[var(--text-faint)] font-mono uppercase mt-1">
                                   + {dayEvents.length - 3} MORE_NODES
                                 </div>
                               )}
                            </div>
                          </Grid>
                        );
                      })}
                    </Grid>
                  </Box>
                )}
              </Box>
            </Box>

            {/* Right Column: Mini Telemetry */}
            <Box sx={{ width: { xs: "100%", lg: 320 } }}>
               <Box sx={{ background: "#050505", border: "1px dashed var(--border-subtle)", p: 3, mb: 4 }}>
                  <div className="flex items-center gap-2 mb-6 pb-4 border-b border-dashed border-[var(--border-subtle)]">
                     <Plus size={14} className="text-[var(--primary)]" />
                     <h3 className="text-[10px] font-black text-white uppercase tracking-widest font-mono">INIT_EVENT_HOOK</h3>
                  </div>
                  <Typography sx={{ color: "var(--text-secondary)", fontSize: "11px", mb: 6, fontHTML: "var(--font-mono)", textTransform: "uppercase", lineHeight: 1.6 }}>
                     Inject a new scheduling protocol into the kernel. All events are vectorized and verified by the AI Cortex.
                  </Typography>
                  <Button
                    component={Link}
                    href="/book"
                    fullWidth
                    sx={{
                      background: "var(--primary)",
                      color: "black",
                      fontFamily: "var(--font-mono)",
                      fontSize: "10px",
                      fontWeight: 900,
                      p: 2,
                      borderRadius: 0,
                      letterSpacing: "0.2em",
                      "&:hover": { background: "white" }
                    }}
                  >
                    START_BOOKING_SEQUENCE
                  </Button>
               </Box>

               <Box sx={{ background: "#050505", border: "1px dashed var(--border-subtle)", p: 3 }}>
                  <div className="flex items-center gap-2 mb-6 pb-4 border-b border-dashed border-[var(--border-subtle)]">
                     <Activity size={14} className="text-[var(--secondary)]" />
                     <h3 className="text-[10px] font-black text-white uppercase tracking-widest font-mono">NODE_LOGS</h3>
                  </div>
                  <div className="space-y-4">
                     {[
                       { label: "SYNC_STATUS", val: "ESTABLISHED", color: "var(--primary)" },
                       { label: "VEC_DENSITY", val: "0.88_SCORE", color: "var(--text-faint)" },
                       { label: "CAL_BOUNDS", val: "CONNECTED", color: "var(--primary)" },
                     ].map((l, i) => (
                       <div key={i} className="flex justify-between font-mono text-[9px] uppercase">
                          <span className="text-[var(--text-faint)]">{l.label}</span>
                          <span className={l.color === "var(--primary)" ? "font-black text-[var(--primary)]" : "font-black text-[var(--text-faint)]"}>{l.val}</span>
                       </div>
                     ))}
                  </div>
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
               background: "rgba(0,0,0,0.9)",
               backdropFilter: "blur(10px)",
               zIndex: 2000,
               display: "flex",
               alignItems: "center",
               justifyContent: "center",
               p: 2.5
             }}
           >
             <Box
               component={motion.div}
               initial={{ scale: 0.9, y: 20 }}
               animate={{ scale: 1, y: 0 }}
               exit={{ scale: 0.9, y: 20 }}
               onClick={(e) => e.stopPropagation()}
               sx={{
                 width: "100%",
                 maxWidth: 480,
                 background: "#050505",
                 border: "1px dashed var(--border-subtle)",
                 p: 4,
                 position: "relative"
               }}
             >
                {/* Corner tags */}
                <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-[var(--primary)]" />
                <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-[var(--primary)]" />

                <div className="flex items-center gap-3 mb-8 pb-4 border-b border-dashed border-[var(--border-subtle)]">
                   <Terminal size={18} className="text-[var(--primary)]" />
                   <h2 className="text-[12px] font-black text-white uppercase tracking-tighter font-mono">
                      EVENT_MANIFEST // <Box component="span" sx={{ color: "var(--primary)" }}>{selectedEvent.id}</Box>
                   </h2>
                </div>

                <div className="space-y-6">
                   <div>
                      <div className="text-[9px] font-black text-[var(--text-faint)] uppercase mb-2 font-mono">TITLE_PROTO</div>
                      <div className="text-[18px] font-black text-white uppercase tracking-tight font-mono">{selectedEvent.title}</div>
                   </div>

                   <Grid container spacing={4}>
                      <Grid item xs={6}>
                         <div className="text-[9px] font-black text-[var(--text-faint)] uppercase mb-2 font-mono">TIMESTAMP</div>
                         <div className="flex items-center gap-2 text-white font-mono text-[11px] font-black">
                            <Clock size={12} className="text-[var(--primary)]" />
                            {new Date(selectedEvent.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }).toUpperCase()}
                         </div>
                      </Grid>
                      <Grid item xs={6}>
                         <div className="text-[9px] font-black text-[var(--text-faint)] uppercase mb-2 font-mono">LOCATION</div>
                         <div className="flex items-center gap-2 text-white font-mono text-[11px] font-black">
                            <MapPin size={12} className="text-[var(--primary)]" />
                            {selectedEvent.location?.toUpperCase() || "N/A"}
                         </div>
                      </Grid>
                   </Grid>

                   {selectedEvent.description && (
                     <div>
                        <div className="text-[9px] font-black text-[var(--text-faint)] uppercase mb-2 font-mono">CONTEXT_RAW</div>
                        <div className="p-4 bg-[var(--bg-hover)] border-l-2 border-[var(--primary)] font-mono text-[11px] text-[var(--text-muted)] italic leading-relaxed">
                           {'>'} {selectedEvent.description}
                        </div>
                     </div>
                   )}

                   <div className="flex gap-3 pt-6">
                     <button className="flex-1 py-3 bg-[var(--primary)] text-black text-[10px] font-black uppercase tracking-widest hover:bg-white transition-all font-mono">
                        JOIN_SESSION_V2
                     </button>
                     <button onClick={() => setSelectedEvent(null)} className="px-6 py-3 border border-dashed border-[var(--border-subtle)] text-[var(--text-muted)] text-[10px] font-black uppercase tracking-widest hover:text-white font-mono">
                        ABORT
                     </button>
                   </div>
                </div>
             </Box>
           </Box>
         )}
      </AnimatePresence>

      <BottomNav />
    </Box>
  );
}

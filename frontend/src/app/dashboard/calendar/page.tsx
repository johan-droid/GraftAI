"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ChevronLeft, 
  ChevronRight, 
  Plus, 
  Clock, 
  MapPin, 
  Trash2, 
  Edit3, 
  X, 
  CheckCircle2,
  CalendarCheck2,
  Loader2,
  Globe, 
  RefreshCw,
  Zap,
  Sparkles,
  Info,
  Mail
} from "lucide-react";
import { 
  getEvents, 
  createEvent, 
  updateEvent, 
  deleteEvent, 
  CalendarEvent as Event,
  manualSync,
} from "@/lib/api";
import Link from "next/link";
import { cn } from "@/lib/utils";

const CATEGORIES = {
  meeting: { label: "Meeting", color: "from-violet-500 to-fuchsia-500", dot: "bg-violet-500" },
  event: { label: "Event", color: "from-amber-400 to-orange-500", dot: "bg-amber-500" },
  birthday: { label: "Birthday", color: "from-pink-500 to-rose-500", dot: "bg-pink-500" },
  task: { label: "Task", color: "from-cyan-400 to-blue-500", dot: "bg-cyan-500" },
} as const;

type CalendarCategory = keyof typeof CATEGORIES;

export default function PremiumCalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSynced, setLastSynced] = useState<Date | null>(null);

  // Coordination State
  const [coordinationMode, setCoordinationMode] = useState(false);
  const [targetTimezone, setTargetTimezone] = useState("UTC");

  const { days } = useMemo(() => {
    const monthStartCalc = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const monthEndCalc = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    const startDateCalc = new Date(monthStartCalc);
    startDateCalc.setDate(startDateCalc.getDate() - monthStartCalc.getDay());
    const endDateCalc = new Date(monthEndCalc);
    endDateCalc.setDate(endDateCalc.getDate() + (6 - monthEndCalc.getDay()));

    const list = [] as Date[];
    const current = new Date(startDateCalc);
    while (current <= endDateCalc) {
      list.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }

    return { days: list };
  }, [currentDate]);

  const fetchEventsData = useCallback(async () => {
    setLoading(true);
    try {
      const monthStartCalc = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
      const monthEndCalc = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
      const startDateCalc = new Date(monthStartCalc);
      startDateCalc.setDate(startDateCalc.getDate() - monthStartCalc.getDay());
      const endDateCalc = new Date(monthEndCalc);
      endDateCalc.setDate(endDateCalc.getDate() + (6 - monthEndCalc.getDay()));

      const data = await getEvents(startDateCalc.toISOString(), endDateCalc.toISOString());
      setEvents(data);
      setLastSynced(new Date());
    } catch (err) {
      console.error("Failed to fetch events:", err);
    } finally {
      setLoading(false);
    }
  }, [currentDate]);

  useEffect(() => {
    fetchEventsData();
  }, [fetchEventsData]);

  const toggleMonth = (dir: "prev" | "next") => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + (dir === "next" ? 1 : -1), 1));
  };

  const getEventsForDay = (day: Date) => {
    return events.filter(e => {
      const d = new Date(e.start_time);
      return d.getDate() === day.getDate() && 
             d.getMonth() === day.getMonth() && 
             d.getFullYear() === day.getFullYear();
    });
  };

  const handleManualSync = async () => {
    setIsSyncing(true);
    try {
      await manualSync();
      await fetchEventsData();
    } catch (err) {
      console.error("Sync failed:", err);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleUpdateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingEvent) return;
    try {
      const updated = await updateEvent(editingEvent.id, editingEvent);
      setEvents(prev => prev.map(ev => ev.id === updated.id ? updated : ev));
      setEditingEvent(null);
    } catch (err) {
      console.error("Update failed:", err);
    }
  };

  const handleDeleteEvent = async (id: number) => {
     if(!confirm("Purge event from Sovereign Database and AI memory?")) return;
     try {
       await deleteEvent(id);
       setEvents(prev => prev.filter(e => e.id !== id));
       setEditingEvent(null);
     } catch (err) {
       console.error("Delete failed:", err);
     }
  };

  const handleCreateEvent = async () => {
    if(!selectedDate) return;
    const newEventData: Partial<Event> = {
      title: "New Sovereign Event",
      description: "Auto-synced with Google and indexed in AI Vector Memory.",
      category: "meeting",
      start_time: selectedDate.toISOString(),
      end_time: new Date(selectedDate.getTime() + 3600000).toISOString(),
      status: "confirmed",
    };
    try {
      const created = await createEvent(newEventData);
      setEvents(prev => [...prev, created]);
      setEditingEvent(created);
    } catch (err) {
      console.error("Create failed:", err);
    }
  };

  // UI Components
  const GlassCard = ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div className={cn("bg-slate-950/40 backdrop-blur-2xl border border-slate-800/50 rounded-[2rem] overflow-hidden shadow-2xl", className)}>
      {children}
    </div>
  );

  if (loading && events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-white space-y-4">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
        <p className="text-xs font-black uppercase tracking-[0.3em] text-slate-500">Recalibrating Timeline</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen space-y-6 md:space-y-10 pb-20 max-w-7xl mx-auto px-2 md:px-0">
      
      {/* Premium Header */}
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2 mb-2">
            <div className="px-2 py-0.5 rounded-md bg-primary/20 border border-primary/30 text-primary text-[10px] font-black uppercase tracking-tighter">
              BETA v2.4
            </div>
            {lastSynced && (
              <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest flex items-center gap-1.5">
                <div className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
                Synced {lastSynced.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            )}
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-white tracking-tighter leading-none">
            Sovereign <span className="bg-gradient-to-r from-primary to-fuchsia-500 bg-clip-text text-transparent">Calendar</span>
          </h1>
          <p className="text-sm text-slate-500 font-medium">Your universal schedule, upgraded with AI and Google Sync.</p>
        </div>

        <div className="flex items-center gap-3">
           <button 
             onClick={handleManualSync}
             disabled={isSyncing}
             className="group relative px-6 py-3 bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden active:scale-95 transition-all disabled:opacity-50"
           >
             <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
             <div className="relative flex items-center gap-2 text-sm font-bold text-slate-300">
               <RefreshCw className={cn("w-4 h-4", isSyncing && "animate-spin")} />
               {isSyncing ? "Syncing..." : "Sync Now"}
             </div>
           </button>
           <button 
             onClick={handleCreateEvent}
             className="px-6 py-3 bg-primary text-white rounded-2xl font-bold text-sm shadow-[0_8px_20px_rgba(79,70,229,0.3)] hover:shadow-[0_8px_30px_rgba(79,70,229,0.5)] active:scale-95 transition-all flex items-center gap-2"
           >
             <Plus className="w-4 h-4" /> New Event
           </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 md:gap-10">
        
        {/* Main Interface */}
        <main className="lg:col-span-8 space-y-6">
          <GlassCard className="p-4 md:p-8">
            {/* Calendar Navigation */}
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-4">
                <h2 className="text-2xl md:text-3xl font-black text-white tracking-tight">
                  {currentDate.toLocaleDateString("en-US", { month: "long" })}
                  <span className="text-slate-600 ml-2">{currentDate.getFullYear()}</span>
                </h2>
              </div>
              <div className="flex gap-2 p-1 bg-slate-900/80 rounded-xl border border-slate-800">
                <button onClick={() => toggleMonth("prev")} className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400">
                   <ChevronLeft className="w-5 h-5" />
                </button>
                <button onClick={() => toggleMonth("next")} className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400">
                   <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Grid Container */}
            <div className="space-y-4">
              <div className="grid grid-cols-7 border-b border-slate-800/50 pb-2">
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map(d => (
                  <div key={d} className="text-center text-[10px] font-black text-slate-600 uppercase tracking-[0.2em]">{d}</div>
                ))}
              </div>

              <div className="grid grid-cols-7 gap-1 md:gap-2">
                {days.map((day, idx) => {
                  const dayEvents = getEventsForDay(day);
                  const isSelected = selectedDate?.toDateString() === day.toDateString();
                  const isToday = day.toDateString() === new Date().toDateString();
                  const isCurrentMonth = day.getMonth() === currentDate.getMonth();

                  return (
                    <motion.div
                      key={idx}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => {
                        setSelectedDate(day);
                        if (!isCurrentMonth) {
                           setCurrentDate(new Date(day.getFullYear(), day.getMonth(), 1));
                        }
                      }}
                      className={cn(
                        "relative flex flex-col items-center justify-center aspect-square rounded-[1rem] md:rounded-[1.5rem] cursor-pointer transition-all border group",
                        isSelected ? "bg-primary border-primary shadow-[0_0_20px_rgba(79,70,229,0.3)] z-10" : 
                        isCurrentMonth ? "bg-slate-900/40 border-slate-800/40 hover:border-primary/40" : 
                        "bg-transparent border-transparent opacity-20 hover:opacity-40"
                      )}
                    >
                      <span className={cn(
                        "text-sm md:text-lg font-black transition-colors",
                        isSelected ? "text-white" : isToday ? "text-primary" : "text-slate-400 group-hover:text-white"
                      )}>
                        {day.getDate()}
                      </span>
                      
                      <div className="flex gap-1 mt-1 justify-center min-h-[4px]">
                        {dayEvents.slice(0, 3).map(e => (
                          <div key={e.id} className={cn("w-1 h-1 md:w-1.5 md:h-1.5 rounded-full ring-2 ring-transparent group-hover:ring-white/20", CATEGORIES[e.category as CalendarCategory]?.dot || "bg-slate-400")} />
                        ))}
                      </div>

                      {isToday && !isSelected && (
                         <div className="absolute top-2 right-2 w-1.5 h-1.5 bg-primary rounded-full shadow-[0_0_10px_rgba(79,70,229,1)]" />
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </GlassCard>

          {/* Targeted Agenda breakdown for the selected day */}
          <GlassCard className="p-6 md:p-10">
             <div className="flex items-center justify-between mb-8">
                <div>
                   <h3 className="text-xl font-black text-white flex items-center gap-2">
                     <Zap className="w-5 h-5 text-primary" /> Daily Agenda
                   </h3>
                   <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">
                     {selectedDate?.toLocaleDateString("en-US", { weekday: 'long', month: 'long', day: 'numeric' })}
                   </p>
                </div>
                <div className="flex items-center gap-1.5 bg-slate-900/60 p-1.5 rounded-xl border border-slate-800">
                   <div className="px-3 py-1 bg-primary text-white text-[10px] font-black rounded-lg">LIVE</div>
                   <div className="px-3 py-1 text-slate-500 text-[10px] font-black">HISTORIC</div>
                </div>
             </div>

             <div className="space-y-4">
                {selectedDate && getEventsForDay(selectedDate).length === 0 ? (
                  <div className="py-12 flex flex-col items-center justify-center border-2 border-dashed border-slate-800/50 rounded-[2rem] bg-slate-900/20">
                     <CalendarCheck2 className="w-12 h-12 text-slate-700 mb-4" />
                     <p className="text-slate-500 font-bold">No tasks scheduled for this block.</p>
                     <button onClick={handleCreateEvent} className="mt-4 text-xs font-black text-primary uppercase tracking-widest hover:underline">Draft Now</button>
                  </div>
                ) : (
                  selectedDate && getEventsForDay(selectedDate).map((evt, i) => (
                    <motion.div 
                      key={evt.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="group flex flex-col md:flex-row md:items-center gap-6 p-6 bg-slate-900/40 border border-slate-800/60 rounded-[2rem] hover:bg-slate-900/80 hover:border-primary/30 transition-all cursor-pointer"
                    >
                      <div className="flex md:flex-col items-center justify-between md:justify-center md:w-24 md:border-r md:border-slate-800 px-2">
                         <span className="text-xl font-black text-white">{new Date(evt.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                         <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Starts</span>
                      </div>

                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2 mb-1">
                          <div className={cn("px-2 py-0.5 rounded-md text-[9px] font-black uppercase tracking-widest bg-gradient-to-r text-white", CATEGORIES[evt.category as CalendarCategory]?.color)}>{evt.category}</div>
                          {evt.source === "google" && <Globe className="w-3 h-3 text-cyan-400" />}
                          <span className="text-[9px] text-slate-600 font-bold flex items-center gap-1 uppercase tracking-widest border border-slate-800 px-2 py-0.5 rounded-md">
                            <CheckCircle2 className="w-2.5 h-2.5 text-primary" /> AI INDEXED
                          </span>
                        </div>
                        <h4 className="text-lg font-bold text-white group-hover:text-primary transition-colors">{evt.title}</h4>
                        <p className="text-sm text-slate-500 line-clamp-1">{evt.description}</p>
                      </div>

                      <div className="flex items-center gap-2">
                        <button 
                          onClick={() => setEditingEvent(evt)}
                          className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-400 hover:text-white hover:border-primary transition-all active:scale-90"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                      </div>
                    </motion.div>
                  ))
                )}
             </div>
          </GlassCard>
        </main>

        {/* Sidebar Controls */}
        <aside className="lg:col-span-4 space-y-6">
           <GlassCard className="p-8">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-black text-white tracking-tight">Sync Status</h3>
                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Active Channels</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                </div>
              </div>

              <div className="space-y-4">
                 <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between">
                   <div className="flex items-center gap-3">
                     <div className="p-2 bg-red-500/10 rounded-lg"><Globe className="w-4 h-4 text-red-400" /></div>
                     <span className="text-sm font-bold text-white">Google Workspace</span>
                   </div>
                   <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
                 </div>
                 <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-between opacity-50 grayscale">
                   <div className="flex items-center gap-3">
                     <div className="p-2 bg-blue-500/10 rounded-lg"><Mail className="w-4 h-4 text-blue-400" /></div>
                     <span className="text-sm font-bold text-white">Outlook 365</span>
                   </div>
                   <span className="text-[9px] font-black uppercase text-slate-600">Locked</span>
                 </div>
              </div>

              <div className="mt-8 pt-8 border-t border-slate-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-black text-white uppercase tracking-widest">Cross-Country</h3>
                  <button 
                    onClick={() => setCoordinationMode(!coordinationMode)}
                    className={cn(
                      "w-12 h-6 rounded-full transition-all relative flex items-center px-1",
                      coordinationMode ? "bg-primary" : "bg-slate-800"
                    )}
                  >
                    <motion.div 
                      layout 
                      className="w-4 h-4 rounded-full bg-white shadow-lg"
                      animate={{ x: coordinationMode ? 24 : 0 }}
                    />
                  </button>
                </div>
                <AnimatePresence>
                  {coordinationMode && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="space-y-4 overflow-hidden"
                    >
                      <select 
                        value={targetTimezone}
                        onChange={(e) => setTargetTimezone(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-xs font-bold text-slate-400 appearance-none focus:border-primary outline-none"
                      >
                         <option value="UTC">Universal Time (UTC)</option>
                         <option value="America/New_York">New York (EST/EDT)</option>
                         <option value="Europe/London">London (GMT/BST)</option>
                         <option value="Asia/Tokyo">Tokyo (JST)</option>
                      </select>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div className="mt-8 p-6 bg-primary/5 border border-primary/20 rounded-[1.5rem] relative group cursor-help">
                <div className="absolute top-4 right-4 text-primary opacity-40 group-hover:opacity-100 transition-opacity">
                  <Info className="w-4 h-4" />
                </div>
                <h4 className="text-sm font-black text-white mb-2 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary" /> AI Context Switch
                </h4>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  Your agenda is actively being vectorized. The AI copilot will reference these slots to optimize your day.
                </p>
              </div>
           </GlassCard>

           <div className="p-1 px-8">
              <Link href="/dashboard/settings/integrations" className="text-xs font-black text-slate-600 uppercase tracking-widest hover:text-primary transition-colors flex items-center gap-2">
                Manage Hub <RefreshCw className="w-3 h-3" />
              </Link>
           </div>
        </aside>
      </div>

      {/* High-End Edit/Create Modal */}
      <AnimatePresence>
        {editingEvent && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-6 lg:p-8">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setEditingEvent(null)}
              className="absolute inset-0 bg-black/80 backdrop-blur-md"
            />
            <motion.div
              layoutId={`event-${editingEvent.id}`}
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-xl bg-[#0c0e10] border border-slate-800/80 rounded-[2.5rem] overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)]"
            >
              <form onSubmit={handleUpdateEvent} className="p-8 md:p-12 space-y-8">
                 <div className="flex items-center justify-between">
                    <h3 className="text-3xl font-black text-white tracking-tighter">Edit <span className="text-primary">Timeline</span></h3>
                    <button type="button" onClick={() => setEditingEvent(null)} className="p-2 bg-slate-900 border border-slate-800 rounded-full text-slate-500 hover:text-white transition-colors">
                      <X className="w-5 h-5" />
                    </button>
                 </div>

                 <div className="space-y-6">
                    <div className="space-y-2">
                       <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Universal Title</label>
                       <input 
                         type="text" 
                         value={editingEvent.title}
                         onChange={(e) => setEditingEvent({...editingEvent, title: e.target.value})}
                         className="w-full bg-[#121416] border border-[#333537]/40 rounded-2xl px-6 py-4 text-white font-bold outline-none focus:border-primary transition-all ring-0"
                         placeholder="Enter event title..."
                       />
                    </div>

                    <div className="space-y-2">
                       <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Strategic Description</label>
                       <textarea 
                         rows={2}
                         value={editingEvent.description}
                         onChange={(e) => setEditingEvent({...editingEvent, description: e.target.value})}
                         className="w-full bg-[#121416] border border-[#333537]/40 rounded-2xl px-6 py-4 text-white font-medium outline-none focus:border-primary transition-all resize-none ring-0"
                         placeholder="Context for AI reasoning..."
                       />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                       <div className="space-y-2">
                          <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Event Logic</label>
                          <select 
                            value={editingEvent.category}
                            onChange={(e) => setEditingEvent({...editingEvent, category: e.target.value as CalendarCategory})}
                            className="w-full bg-[#121416] border border-[#333537]/40 rounded-2xl px-6 py-4 text-white font-bold outline-none focus:border-primary appearance-none ring-0"
                          >
                             {Object.keys(CATEGORIES).map(c => <option key={c} value={c}>{c.toUpperCase()}</option>)}
                          </select>
                       </div>
                       <div className="space-y-2">
                          <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Visibility</label>
                          <div className="w-full bg-[#121416] border border-[#333537]/40 rounded-2xl px-6 py-4 text-emerald-400 font-black tracking-widest text-xs flex items-center justify-center gap-2">
                            <CheckCircle2 className="w-4 h-4" /> GLOBAL SYNC
                          </div>
                       </div>
                    </div>
                 </div>

                 <div className="pt-6 flex flex-col md:flex-row gap-4">
                    <button 
                      type="button"
                      onClick={() => handleDeleteEvent(editingEvent.id)}
                      className="px-6 py-4 bg-red-500/10 border border-red-500/30 text-red-500 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-red-500 hover:text-white transition-all flex items-center justify-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" /> Purge
                    </button>
                    <button 
                      type="submit"
                      className="flex-1 px-8 py-4 bg-primary text-white rounded-2xl font-black text-xs uppercase tracking-[0.2em] shadow-[0_8px_30px_rgba(79,70,229,0.4)] hover:shadow-[0_8px_40px_rgba(79,70,229,0.6)] active:scale-95 transition-all flex items-center justify-center gap-2"
                    >
                      Apply & Index <CheckCircle2 className="w-4 h-4" />
                    </button>
                 </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

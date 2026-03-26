"use client";

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ChevronLeft, 
  ChevronRight, 
  Plus, 
  Settings, 
  Calendar as CalendarIcon, 
  Clock, 
  MapPin, 
  Trash2, 
  Edit3, 
  X, 
  CheckCircle2,
  CalendarCheck2,
  Loader2
} from "lucide-react";
import { 
  getEvents, 
  createEvent, 
  updateEvent, 
  deleteEvent, 
  getAvailableSlots, 
  CalendarEvent as Event,
} from "@/lib/api";
import Link from "next/link";
import { cn } from "@/lib/utils";

const CATEGORIES = {
  meeting: { label: "Meeting", color: "#8A2BE2", dot: "bg-violet-500" },
  event: { label: "Event", color: "#FFD700", dot: "bg-yellow-500" },
  birthday: { label: "Birthday", color: "#FF69B4", dot: "bg-pink-500" },
  task: { label: "Task", color: "#00CED1", dot: "bg-cyan-500" },
} as const;

type CalendarCategory = keyof typeof CATEGORIES;


export default function PremiumCalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [isCreating, setIsCreating] = useState(false);
  const [recommendations, setRecommendations] = useState<{start: string, end: string, local_label?: string, guest_label?: string}[]>([]);

  // Coordination State
  const [coordinationMode, setCoordinationMode] = useState(false);
  const [targetTimezone, setTargetTimezone] = useState("UTC");

  const { days, startDate, endDate } = useMemo(() => {
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

    return {
      startDate: startDateCalc,
      endDate: endDateCalc,
      days: list,
    };
  }, [currentDate]);


  // Fetch events for current month range
  const fetchEventsData = async () => {
    setLoading(true);
    try {
      const startISO = startDate.toISOString();
      const endISO = endDate.toISOString();
      const data = await getEvents(startISO, endISO);
      setEvents(data);
    } catch (err) {
      console.error("Failed to fetch events:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEventsData();
  }, [currentDate]);

  // Fetch AI Recommendations (Available Slots)
  useEffect(() => {
    const fetchSlotsData = async () => {
      try {
        const dateISO = currentDate.toISOString();
        const data = await getAvailableSlots(
          dateISO, 
          60, 
          coordinationMode ? targetTimezone : undefined
        );
        setRecommendations(data.slice(0, 3)); // show top 3
      } catch (err) {
        console.error("Failed to fetch slots:", err);
      }
    };
    fetchSlotsData();
  }, [currentDate, coordinationMode, targetTimezone]);

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
     if(!confirm("Are you sure? This will also purge AI long-term memory for this event.")) return;
     try {
       const res = await deleteEvent(id);
       type DeleteEventResponse = { status?: string };
       const typedRes = res as DeleteEventResponse;
       if (typedRes.status !== 'error') {
         setEvents(prev => prev.filter(e => e.id !== id));
         setEditingEvent(null);
       }
     } catch (err) {
       console.error("Delete failed:", err);
     }
  };

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if(!selectedDate) return;

    setIsCreating(true);

    const newEventData: Partial<Event> = {
      title: "New AI Synced Meeting",
      description: "Auto-generated and fed into LLM vector memory.",
      category: "meeting",
      start_time: selectedDate.toISOString(),
      end_time: new Date(selectedDate.getTime() + 3600000).toISOString(),
      is_remote: true,
      status: "confirmed",
      metadata_payload: {}
    };

    try {
      const created = await createEvent(newEventData);
      setEvents(prev => [...prev, created]);
    } catch (err) {
      console.error("Create failed:", err);
    } finally {
      setIsCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen text-white">
        <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading your calendar...
      </div>
    );
  }

  return (
    <div className="min-h-screen space-y-8 pb-12">
      {/* Header with Dashboard Link */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white mb-2">
            Sovereign <span className="text-primary text-transparent bg-clip-text bg-gradient-to-r from-primary to-violet-400">Calendar</span>
          </h1>
          <p className="text-slate-400 font-medium">AI-Synchronized high-fidelity scheduling engine.</p>
        </div>
        <div className="flex items-center gap-4">
           <button className="p-3 bg-slate-900 border border-slate-800 rounded-full hover:bg-slate-800 transition-colors shadow-lg">
             <Settings className="w-5 h-5 text-slate-400" />
           </button>
           <Link href="/dashboard" className="px-8 py-3 bg-primary/10 border border-primary/20 text-primary rounded-full hover:bg-primary/20 transition-all font-bold flex items-center gap-2 shadow-sm">
             <CalendarCheck2 className="w-5 h-5" /> Dashboard
           </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Main Calendar View */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-slate-950/40 border border-slate-800/60 rounded-[2rem] p-8 backdrop-blur-xl shadow-2xl">
            {/* Calendar Controls */}
            <div className="flex items-center justify-between mb-10">
              <h2 className="text-2xl font-bold text-white capitalize">
                {currentDate.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
              </h2>
              <div className="flex gap-2 p-1 bg-slate-900/80 rounded-2xl border border-slate-800">
                <button onClick={() => toggleMonth("prev")} className="p-2 hover:bg-slate-800 rounded-xl transition-colors">
                   <ChevronLeft className="w-5 h-5 text-white" />
                </button>
                <div className="w-[1px] bg-slate-800 my-1 mx-1" />
                <button onClick={() => toggleMonth("next")} className="p-2 hover:bg-slate-800 rounded-xl transition-colors">
                   <ChevronRight className="w-5 h-5 text-white" />
                </button>
              </div>
            </div>

            {/* Weekdays Header */}
            <div className="grid grid-cols-7 mb-4">
              {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map(d => (
                <div key={d} className="text-center text-xs font-bold text-slate-500 uppercase tracking-widest py-2">
                  {d}
                </div>
              ))}
            </div>

            {/* Grid Layout */}
            <div className="grid grid-cols-7 gap-2">
              {days.map((day, idx) => {
                const dayEvents = getEventsForDay(day);
                const isSelected = selectedDate?.toDateString() === day.toDateString();
                const isToday = day.toDateString() === new Date().toDateString();
                const isCurrentMonth = day.getMonth() === currentDate.getMonth();

                return (
                  <motion.div
                    key={idx}
                    whileHover={{ scale: isCurrentMonth ? 1.05 : 1 }}
                    onClick={() => {
                      if(isCurrentMonth) {
                        setSelectedDate(day);
                        setIsModalOpen(true);
                      }
                    }}
                    className={`
                      relative flex flex-col items-center justify-center aspect-square rounded-[1.5rem] cursor-pointer transition-all border
                      ${isSelected ? "bg-primary border-primary shadow-[0_0_20px_rgba(138,43,226,0.3)]" : 
                        isCurrentMonth ? "bg-slate-900/30 border-slate-800/40 hover:bg-slate-800/50 hover:border-slate-700" : 
                        "bg-transparent border-transparent opacity-20"}
                    `}
                  >
                    <span className={`text-lg font-bold ${isSelected ? "text-white" : isToday ? "text-primary" : "text-slate-300"}`}>
                      {day.getDate()}
                    </span>
                    
                    {/* Event Dots Under Dates */}
                    <div className="flex gap-1 mt-1 justify-center min-h-[6px]">
                      {dayEvents.slice(0, 3).map(e => (
                        <div key={e.id} className={`w-1.5 h-1.5 rounded-full ${CATEGORIES[e.category]?.dot || "bg-slate-400"}`} />
                      ))}
                    </div>

                    {isToday && !isSelected && (
                       <div className="absolute top-2 right-3 w-1.5 h-1.5 bg-primary rounded-full" />
                    )}
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Categories Sidebar */}
        <div className="lg:col-span-4 space-y-6">
           <div className="bg-white/40 dark:bg-slate-950/40 border border-slate-200/60 dark:border-slate-800/60 rounded-[2.5rem] p-8 backdrop-blur-xl h-full shadow-2xl">
             
             {/* Coordination Controls */}
             <div className="mb-8 p-6 bg-primary/10 border border-primary/20 rounded-[2rem] shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-primary uppercase tracking-widest">Cross-Country</h3>
                  <button 
                    onClick={() => setCoordinationMode(!coordinationMode)}
                    className={cn(
                      "w-12 h-6 rounded-full transition-all relative shadow-inner",
                      coordinationMode ? "bg-primary" : "bg-slate-300 dark:bg-slate-700"
                    )}
                  >
                    <div className={cn(
                      "absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-all",
                      coordinationMode ? "translate-x-6" : "translate-x-0"
                    )} />
                  </button>
                </div>
                
                <AnimatePresence>
                  {coordinationMode && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="space-y-3 overflow-hidden"
                    >
                      <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Guest Timezone</label>
                      <select 
                        value={targetTimezone}
                        onChange={(e) => setTargetTimezone(e.target.value)}
                        className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all appearance-none"
                      >
                        <option value="UTC">Universal Coordinated Time (UTC)</option>
                        <option value="America/New_York">New York (EST/EDT)</option>
                        <option value="Europe/London">London (GMT/BST)</option>
                        <option value="Asia/Tokyo">Tokyo (JST)</option>
                        <option value="Australia/Sydney">Sydney (AEST/AEDT)</option>
                        <option value="Asia/Dubai">Dubai (GST)</option>
                      </select>
                    </motion.div>
                  )}
                </AnimatePresence>
             </div>

             <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-6">AI Recommendations</h3>
             <div className="space-y-4">
                {recommendations.length > 0 ? recommendations.map((slot, i) => (
                  <div key={i} className="p-5 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-[1.5rem] shadow-sm hover:shadow-md transition-all group overflow-hidden relative">
                     <div className="absolute top-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Plus className="w-4 h-4 text-primary cursor-pointer" />
                     </div>
                     <div className="flex items-center gap-2 mb-3">
                       <Clock className="w-4 h-4 text-primary" />
                       <span className="text-xs font-bold text-slate-700 dark:text-slate-200">Optimal Overlap</span>
                     </div>
                     
                     <div className="flex flex-col gap-2">
                        <div className="flex items-center justify-between">
                           <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Local</span>
                           <span className="text-xs font-mono text-slate-800 dark:text-slate-100 font-bold">
                              {slot.local_label || `${new Date(slot.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
                           </span>
                        </div>
                        {slot.guest_label && (
                          <div className="flex items-center justify-between pt-2 border-t border-slate-50 dark:border-slate-800">
                             <span className="text-[10px] text-primary/60 font-bold uppercase tracking-wider">Guest</span>
                             <span className="text-xs font-mono text-primary font-bold">
                                {slot.guest_label}
                             </span>
                          </div>
                        )}
                     </div>
                  </div>
                )) : (
                  <div className="py-8 text-center bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800">
                    <p className="text-sm text-slate-400 font-medium italic">No premium slots available</p>
                  </div>
                )}
             </div>

             <div className="mt-8 pt-8 border-t border-slate-200 dark:border-slate-800">
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-6">Categories</h3>
                <div className="space-y-3">
                    {Object.entries(CATEGORIES).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900/40 rounded-2xl border border-slate-100 dark:border-slate-800 group transition-all hover:bg-white dark:hover:bg-slate-800">
                        <div className="flex items-center gap-3">
                          <div className={`w-3 h-3 rounded-full ${value.dot} ring-4 ring-${value.dot.replace('bg-', '')}/10`} />
                          <span className="text-sm font-bold text-slate-600 dark:text-slate-400">{value.label}</span>
                        </div>
                        <span className="text-xs text-slate-400 font-mono font-bold">
                          {events.filter(e => e.category === key).length}
                        </span>
                      </div>
                    ))}
                </div>
             </div>

             <div className="mt-8 p-6 bg-gradient-to-br from-primary/10 to-violet-500/10 border border-primary/20 rounded-[2rem] shadow-sm">
                <h4 className="flex items-center gap-2 text-primary font-bold mb-2">
                  <CheckCircle2 className="w-5 h-5" /> Vector Recall
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed font-medium">
                  Modifications are instantly indexed in your AI&apos;s long-term memory for situational awareness.
                </p>
             </div>
           </div>
        </div>
      </div>

      {/* Date Details Modal / Popup */}
      <AnimatePresence>
        {isModalOpen && selectedDate && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 lg:p-8">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsModalOpen(false)}
              className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
            />
            
            <motion.div
              layoutId={`modal-${selectedDate.toDateString()}`}
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-[2.5rem] overflow-hidden shadow-2xl"
            >
              {/* Modal Header */}
              <div className="p-8 border-b border-slate-800 flex items-center justify-between bg-zinc-950/20">
                <div>
                   <h3 className="text-3xl font-bold text-white">
                     {selectedDate.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
                   </h3>
                   <p className="text-slate-400 font-medium">Daily agenda breakdown</p>
                </div>
                <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-slate-800 rounded-full transition-colors">
                   <X className="w-6 h-6 text-white" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-8 max-h-[60vh] overflow-y-auto space-y-6 bg-slate-900/50">
                {getEventsForDay(selectedDate).length === 0 ? (
                  <div className="py-20 text-center flex flex-col items-center gap-4">
                    <div className="p-6 bg-slate-800/40 rounded-full border border-slate-700/50">
                      <Plus className="w-10 h-10 text-slate-600" />
                    </div>
                    <p className="text-slate-500 font-medium">No events scheduled for this day.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {getEventsForDay(selectedDate).map((evt) => (
                      <div key={evt.id} className="group relative p-6 bg-slate-950/60 border border-slate-800/80 rounded-[2rem] hover:border-primary/40 transition-all shadow-sm overflow-hidden">
                        <div className={`absolute top-0 left-0 w-1.5 h-full ${CATEGORIES[evt.category]?.dot}`} />
                        
                        <div className="flex items-start justify-between gap-4">
                           <div className="space-y-2">
                             <div className="flex items-center gap-2">
                               <span className={`text-xs font-bold uppercase tracking-widest ${CATEGORIES[evt.category]?.dot.replace("bg-", "text-")}`}>
                                 {evt.category}
                               </span>
                               <span className="w-1 h-1 bg-slate-700 rounded-full" />
                               <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                                 <Clock className="w-3 h-3" /> 
                                 {new Date(evt.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                               </span>
                               <span className="flex items-center gap-1 text-[10px] text-primary/70 font-bold bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
                                 <CheckCircle2 className="w-3 h-3" /> AI SYNCED
                               </span>
                             </div>
                             <h4 className="text-xl font-bold text-white group-hover:text-primary transition-colors">{evt.title}</h4>
                             <p className="text-sm text-slate-400 leading-relaxed">{evt.description}</p>
                           </div>
                           
                           <div className="flex gap-2">
                              <button 
                                onClick={() => setEditingEvent(evt)}
                                className="p-3 bg-slate-900 border border-slate-800 rounded-xl hover:bg-primary/20 hover:border-primary/40 transition-all"
                              >
                                <Edit3 className="w-4 h-4 text-slate-300" />
                              </button>
                           </div>
                        </div>

                        {evt.is_remote && (
                          <div className="mt-4 pt-4 border-t border-slate-800/50 flex items-center gap-2 text-xs text-primary font-bold">
                             <MapPin className="w-4 h-4" /> Remote Experience
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="p-8 bg-zinc-950/40 flex justify-end gap-3">
                 <button onClick={handleCreateEvent} className="px-8 py-3 bg-slate-900 border border-slate-800 text-white rounded-full font-bold hover:bg-slate-800 transition-all flex items-center gap-2">
                   Add Event
                 </button>
                 <button onClick={() => setIsModalOpen(false)} className="px-8 py-3 bg-primary text-white rounded-full font-bold hover:shadow-[0_0_20px_rgba(138,43,226,0.5)] transition-all">
                   Done
                 </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Inline Editing Popup / Overlay */}
      <AnimatePresence>
        {editingEvent && (
          <div className="fixed inset-0 z-[110] flex items-center justify-center p-4">
             <motion.div 
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               exit={{ opacity: 0 }}
               className="absolute inset-0 bg-slate-950/90 backdrop-blur-md"
             />
             <motion.div 
               initial={{ scale: 0.9, y: 20 }}
               animate={{ scale: 1, y: 0 }}
               exit={{ scale: 0.9, y: 20 }}
               className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-[3rem] p-10 shadow-2xl"
             >
                <form onSubmit={handleUpdateEvent} className="space-y-6">
                   <div className="flex items-center justify-between mb-8">
                      <h3 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Edit3 className="w-6 h-6 text-primary" /> Edit Schedule
                      </h3>
                      <button type="button" onClick={() => setEditingEvent(null)} className="p-2 hover:bg-slate-800 rounded-full">
                         <X className="w-6 h-6 text-slate-500" />
                      </button>
                   </div>

                   <div className="space-y-4">
                      <div>
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-widest pl-1 mb-2 block">Event Title</label>
                        <input 
                          type="text" 
                          value={editingEvent.title}
                          onChange={(e) => setEditingEvent({...editingEvent, title: e.target.value})}
                          className="w-full bg-slate-950 border border-slate-800 rounded-full px-8 py-4 text-white focus:outline-none focus:border-primary transition-all shadow-inner"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-widest pl-1 mb-2 block">Description</label>
                        <textarea 
                           rows={3}
                           value={editingEvent.description}
                           onChange={(e) => setEditingEvent({...editingEvent, description: e.target.value})}
                           className="w-full bg-slate-950 border border-slate-800 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-primary transition-all resize-none"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                         <div>
                            <label className="text-xs font-bold text-slate-500 uppercase tracking-widest pl-1 mb-2 block">Status</label>
                            <select 
                               value={editingEvent.status}
                               onChange={(e) => setEditingEvent({...editingEvent, status: e.target.value})}
                               className="w-full bg-slate-950 border border-slate-800 rounded-full px-8 py-4 text-white focus:outline-none focus:border-primary appearance-none shadow-inner"
                            >
                               <option value="confirmed">Confirmed</option>
                               <option value="pending">Pending</option>
                               <option value="canceled">Canceled</option>
                            </select>
                         </div>
                         <div>
                            <label className="text-xs font-bold text-slate-500 uppercase tracking-widest pl-1 mb-2 block">Category</label>
                            <select 
                               value={editingEvent.category}
                               onChange={(e) => setEditingEvent({...editingEvent, category: e.target.value as CalendarCategory})}
                               className="w-full bg-slate-950 border border-slate-800 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-primary appearance-none"
                            >
                               {Object.keys(CATEGORIES).map(c => <option key={c} value={c}>{c.toUpperCase()}</option>)}
                            </select>
                         </div>
                      </div>
                   </div>

                   <div className="pt-6 flex gap-3">
                      <button 
                         type="button" 
                         onClick={() => handleDeleteEvent(editingEvent.id)}
                         className="px-6 py-4 bg-red-500/10 border border-red-500/20 text-red-500 rounded-full font-bold hover:bg-red-500 hover:text-white transition-all shadow-sm"
                      >
                         <Trash2 className="w-5 h-5" />
                      </button>
                      <button 
                         type="button" 
                         onClick={() => setEditingEvent(null)}
                         className="flex-1 px-8 py-4 bg-slate-800 text-white rounded-full font-bold hover:bg-slate-700 transition-all shadow-sm"
                      >
                         Cancel
                      </button>
                      <button 
                         type="submit"
                         className="flex-[2] px-8 py-4 bg-primary text-white rounded-full font-bold hover:shadow-[0_0_30px_rgba(138,43,226,0.6)] transition-all flex items-center justify-center gap-2"
                      >
                         <CheckCircle2 className="w-5 h-5" /> Save & Sync AI
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

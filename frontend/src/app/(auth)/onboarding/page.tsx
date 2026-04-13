"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Box, Typography, Button, TextField, Grid, Stack } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { 
  User, 
  Calendar, 
  Sparkles, 
  Check, 
  ArrowRight, 
  ArrowLeft, 
  Zap, 
  Clock, 
  Bell,
  Terminal,
  Activity,
  Cpu
} from "lucide-react";
import { toast } from "@/components/ui/Toast";
import { AuthLayout } from "@/components/auth/AuthLayout";

const steps = ["BOOT_ENV", "USER_PROFILE", "PREF_SYNC", "COMMS_READY"];

const timeZones = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Asia/Tokyo",
  "Asia/Singapore",
  "Australia/Sydney",
];

export default function OnboardingPage() {
  const router = useRouter();
  const [activeStep, setActiveStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [timeZone, setTimeZone] = useState("UTC");
  const [workHours, setWorkHours] = useState({ start: "09:00", end: "17:00" });
  const [notifications, setNotifications] = useState(true);
  const [aiSuggestions, setAiSuggestions] = useState(true);

  const handleNext = () => {
    if (activeStep === 1 && !name.trim()) {
      toast.error("PROTOCOL_ERROR: IDENTITY_DATA_REQUIRED");
      return;
    }
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleComplete = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/auth/onboarding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          timezone: timeZone,
          work_hours_start: workHours.start,
          work_hours_end: workHours.end,
          notifications_enabled: notifications,
          ai_suggestions_enabled: aiSuggestions,
        }),
      });

      if (!response.ok) {
        throw new Error("KERNEL_REJECTION: ONBOARDING_SYNC_FAILED");
      }

      toast.success("KERNEL_ACCESS_GRANTED: WELCOME_USER");
      router.push("/dashboard");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "SYSTEM_CRITICAL: UNKNOWN_ERROR_DURING_SYNC");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout title="GraftAI // Kernel_Setup">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        {/* Technical Stepper */}
        <Box sx={{ mb: 6 }}>
          <div className="flex items-center gap-1 mb-2">
             {steps.map((label, i) => (
               <div key={i} className="flex-1 flex items-center gap-2">
                  <div className={`h-[2px] flex-1 ${activeStep >= i ? "bg-[var(--primary)]" : "bg-[var(--border-subtle)]"}`} />
                  {i === steps.length - 1 && <div className={`h-[2px] flex-1 ${activeStep > i ? "bg-[var(--primary)]" : "bg-[var(--border-subtle)]"}`} />}
               </div>
             ))}
          </div>
          <div className="flex justify-between px-1">
             {steps.map((label, i) => (
               <span 
                 key={i} 
                 className={`text-[8px] font-black font-mono tracking-widest ${activeStep === i ? "text-[var(--primary)]" : "text-[var(--text-faint)]"}`}
               >
                 {label}
               </span>
             ))}
          </div>
        </Box>

        <Box
          sx={{
            p: { xs: 3, md: 5 },
            background: "#050505",
            border: "1px dashed var(--border-subtle)",
            position: "relative",
            overflow: "hidden"
          }}
        >
          {/* Corner accents */}
          <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-[var(--primary)]" />
          <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-[var(--primary)]" />
          
          <AnimatePresence mode="wait">
            {activeStep === 0 && (
              <motion.div
                key="step0"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.2 }}
              >
                <Box sx={{ mb: 6 }}>
                  <div className="flex items-center gap-3 mb-4">
                     <Terminal size={20} className="text-[var(--primary)]" />
                     <h2 className="text-[14px] font-black text-white uppercase tracking-tighter font-mono">INIT_KERNEL_SEQUENCE</h2>
                  </div>
                  
                  <Typography sx={{ color: "var(--text-secondary)", fontSize: "12px", fontFamily: "var(--font-mono)", textTransform: "uppercase", lineHeight: 1.6, mb: 4 }}>
                     Initializing AI-powered core scheduling protocols. GraftAI is preparing your dedicated compute node for automated organizational management.
                  </Typography>
                </Box>

                <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 4 }}>
                  {[
                    { icon: Zap, text: "SMART_SCHEDULING_PROTOCOL" },
                    { icon: Clock, text: "AUTO_AVAILABILITY_DETECTION" },
                    { icon: Bell, text: "INTEL_NOTIFICATION_HANDLERS" },
                  ].map((feature, i) => (
                    <Box
                      key={i}
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 3,
                        p: 2.5,
                        background: "rgba(255,255,255,0.02)",
                        borderLeft: "2px solid var(--primary)",
                      }}
                    >
                      <feature.icon size={16} className="text-[var(--primary)]" />
                      <Typography sx={{ color: "white", fontSize: "10px", fontWeight: 900, fontFamily: "var(--font-mono)", letterSpacing: "0.1em" }}>
                        {feature.text}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </motion.div>
            )}

            {activeStep === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                <Box sx={{ mb: 6 }}>
                  <div className="flex items-center gap-3 mb-4">
                     <User size={20} className="text-[var(--primary)]" />
                     <h2 className="text-[14px] font-black text-white uppercase tracking-tighter font-mono">USER_PROFILE_SYNC</h2>
                  </div>
                  <Typography sx={{ color: "var(--text-faint)", fontSize: "11px", fontFamily: "var(--font-mono)", textTransform: "uppercase", mb: 4 }}>
                     IDENTITY_MANIFEST: Verify primary operator credentials.
                  </Typography>
                </Box>

                <Stack spacing={4}>
                  <Box>
                     <div className="text-[9px] font-black text-[var(--text-faint)] mb-2 font-mono uppercase">OPERATOR_NAME</div>
                     <TextField
                       fullWidth
                       placeholder="[ENTER_NAME]"
                       value={name}
                       onChange={(e) => setName(e.target.value)}
                       sx={{
                         "& .MuiOutlinedInput-root": {
                           background: "rgba(255,255,255,0.03)",
                           borderRadius: 0,
                           color: "white",
                           fontFamily: "var(--font-mono)",
                           fontSize: "13px",
                           "& fieldset": { border: "1px dashed var(--border-subtle)" },
                           "&:hover fieldset": { borderColor: "var(--primary)" },
                           "&.Mui-focused fieldset": { borderColor: "var(--primary)" },
                         },
                       }}
                     />
                  </Box>

                  <Box>
                     <div className="text-[9px] font-black text-[var(--text-faint)] mb-2 font-mono uppercase">TIMEZONE_SYNC</div>
                     <TextField
                       fullWidth
                       select
                       value={timeZone}
                       onChange={(e) => setTimeZone(e.target.value)}
                       SelectProps={{ native: true }}
                       sx={{
                         "& .MuiOutlinedInput-root": {
                           background: "rgba(255,255,255,0.03)",
                           borderRadius: 0,
                           color: "white",
                           fontFamily: "var(--font-mono)",
                           fontSize: "13px",
                           "& fieldset": { border: "1px dashed var(--border-subtle)" },
                         },
                       }}
                     >
                       {timeZones.map((tz) => (
                         <option key={tz} value={tz}>
                           {tz}
                         </option>
                       ))}
                     </TextField>
                  </Box>
                </Stack>
              </motion.div>
            )}

            {activeStep === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                <Box sx={{ mb: 6 }}>
                  <div className="flex items-center gap-3 mb-4">
                     <Cpu size={20} className="text-[var(--primary)]" />
                     <h2 className="text-[14px] font-black text-white uppercase tracking-tighter font-mono">PREFERENCE_SYNC</h2>
                  </div>
                  <Typography sx={{ color: "var(--text-faint)", fontSize: "11px", fontFamily: "var(--font-mono)", textTransform: "uppercase", mb: 4 }}>
                     CORE_LOGIC: Configure AI scheduling thresholds.
                  </Typography>
                </Box>

                <Stack spacing={3}>
                  <Box sx={{ p: 3, background: "rgba(255,255,255,0.02)", border: "1px dashed var(--border-subtle)" }}>
                    <div className="text-[9px] font-black text-white mb-4 font-mono uppercase">WORKING_WINDOW</div>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <TextField
                          fullWidth
                          type="time"
                          value={workHours.start}
                          onChange={(e) => setWorkHours((p) => ({ ...p, start: e.target.value }))}
                          sx={{
                            "& .MuiOutlinedInput-root": {
                              borderRadius: 0,
                              color: "white",
                              fontFamily: "var(--font-mono)",
                              fontSize: "12px",
                              "& fieldset": { border: "1px dashed var(--border-subtle)" },
                            },
                          }}
                        />
                      </Grid>
                      <Grid item xs={6}>
                        <TextField
                          fullWidth
                          type="time"
                          value={workHours.end}
                          onChange={(e) => setWorkHours((p) => ({ ...p, end: e.target.value }))}
                          sx={{
                            "& .MuiOutlinedInput-root": {
                              borderRadius: 0,
                              color: "white",
                              fontFamily: "var(--font-mono)",
                              fontSize: "12px",
                              "& fieldset": { border: "1px dashed var(--border-subtle)" },
                            },
                          }}
                        />
                      </Grid>
                    </Grid>
                  </Box>

                  {[
                    { icon: Bell, title: "NOTIFICATIONS", desc: "SYSTEM_REPORTS", state: notifications, set: setNotifications },
                    { icon: Sparkles, title: "AI_AUGMENTATION", desc: "SCHEDULE_OPTIMIZATION", state: aiSuggestions, set: setAiSuggestions },
                  ].map((p, i) => (
                    <Box 
                      key={i}
                      onClick={() => p.set(!p.state)}
                      sx={{ 
                        p: 3, 
                        display: "flex", 
                        alignItems: "center", 
                        justifyContent: "space-between", 
                        background: "rgba(255,255,255,0.02)", 
                        border: "1px solid transparent",
                        borderColor: p.state ? "rgba(0,255,156,0.3)" : "transparent",
                        cursor: "pointer",
                        transition: "all 0.1s"
                      }}
                    >
                      <div className="flex items-center gap-4">
                        <p.icon size={16} className={p.state ? "text-[var(--primary)]" : "text-[var(--text-faint)]"} />
                        <div>
                           <div className="text-[10px] font-black text-white font-mono uppercase">{p.title}</div>
                           <div className="text-[8px] font-bold text-[var(--text-faint)] font-mono uppercase">{p.desc}</div>
                        </div>
                      </div>
                      <div className={`w-8 h-4 border ${p.state ? "border-[var(--primary)] bg-[var(--primary)]/20" : "border-[var(--border-subtle)]"} p-[2px] transition-all`}>
                         <div className={`w-full h-full ${p.state ? "bg-[var(--primary)]" : "bg-transparent"}`} />
                      </div>
                    </Box>
                  ))}
                </Stack>
              </motion.div>
            )}

            {activeStep === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.2 }}
              >
                <Box sx={{ textAlign: "center", py: 4 }}>
                  <div className="w-20 h-20 border border-dashed border-[var(--primary)] flex items-center justify-center mx-auto mb-8 relative">
                     <Box className="scanline" sx={{ opacity: 0.2 }} />
                     <Check size={40} className="text-[var(--primary)]" />
                     <div className="absolute -top-1 -right-1 w-2 h-2 bg-[var(--primary)]" />
                  </div>

                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 900,
                      color: "white",
                      fontFamily: "var(--font-mono)",
                      mb: 2,
                      textTransform: "uppercase"
                    }}
                  >
                    SYNC_COMPLETE
                  </Typography>

                  <Typography sx={{ color: "var(--text-faint)", fontSize: "11px", fontFamily: "var(--font-mono)", textTransform: "uppercase", maxWidth: 300, mx: "auto", mb: 8 }}>
                     Your operator identity is now integrated into the AI Cortex. Access to the GraftAI kernel has been authorized.
                  </Typography>
                  
                  <div className="flex justify-center">
                    <div className="px-6 py-2 border-l-2 border-[var(--primary)] bg-[var(--primary)]/10 text-[var(--primary)] text-[10px] font-black font-mono tracking-widest uppercase">
                       PROTOCOL_READY // 100%_STABLE
                    </div>
                  </div>
                </Box>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Navigation Buttons */}
          <Box sx={{ display: "flex", justifyContent: "space-between", mt: 10 }}>
            <button
              onClick={handleBack}
              disabled={activeStep === 0}
              className={`flex items-center gap-2 text-[10px] font-black font-mono tracking-widest uppercase transition-all ${activeStep === 0 ? "opacity-20 cursor-not-allowed" : "text-white hover:text-[var(--primary)]"}`}
            >
              <ArrowLeft size={16} />
              BACK_STEP
            </button>

            {activeStep === steps.length - 1 ? (
              <button
                onClick={handleComplete}
                disabled={isLoading}
                className="px-10 py-3 bg-[var(--primary)] text-black text-[10px] font-black font-mono tracking-[.25em] uppercase hover:bg-white transition-all disabled:opacity-50"
              >
                {isLoading ? "SYNCING..." : "ENTER_KERNEL"}
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="px-10 py-3 bg-white text-black text-[10px] font-black font-mono tracking-[.25em] uppercase hover:bg-[var(--primary)] transition-all"
              >
                CONTINUE_INIT
              </button>
            )}
          </Box>
        </Box>
        
        {/* Environment status line */}
        <div className="mt-4 flex justify-between font-mono text-[7px] text-[var(--text-faint)] uppercase tracking-widest">
           <span>BUILD_ID: GRAFT_0.82_N</span>
           <span>INIT_CODE: 0xFD91_X</span>
           <span>KERN_STAT: NOMINAL</span>
        </div>
      </motion.div>
    </AuthLayout>
  );
}

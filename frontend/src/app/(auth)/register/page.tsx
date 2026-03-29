"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signUp, signIn } from "@/lib/auth-client";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Mail, 
  Lock, 
  User, 
  Globe, 
  ShieldCheck, 
  ArrowLeft,
  Cpu,
  Sparkles,
  Zap
} from "lucide-react";

import AuthInput from "../components/AuthInput";
import AuthButton from "../components/AuthButton";
import SocialAuthGrid from "../components/SocialAuthGrid";

export default function RegisterPage() {
  const router = useRouter();
  
  // State
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [timezone, setTimezone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    // Automatically capture browser timezone
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      setTimezone(tz || "UTC");
    } catch (e) {
      console.warn("Could not capture timezone", e);
      setTimezone("UTC");
    }
  }, []);

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { error } = await signUp(email, password, fullName, timezone);
      if (error) throw new Error(error.message || "Registration failed");
      
      setSuccess(true);
      setTimeout(() => router.push("/login"), 2500);
    } catch (err) {
      setError((err as Error).message || "Identity establishment failed. Please check your data.");
    } finally {
      setLoading(false);
    }
  }

  const handleOAuth = async (provider: "google" | "github" | "discord" | "microsoft") => {
    setLoading(true);
    try {
      await signIn.social({ provider });
    } catch (err) {
      setError("OAuth registration protocol failed.");
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#0A0E27] flex items-center justify-center p-6 relative overflow-hidden">
      
      {/* Static Background Accents */}
      <div className="absolute top-0 left-0 w-full h-full -z-10 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-[#0066FF]/5 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-[#6366F1]/5 rounded-full blur-[120px]" />
      </div>

      <section className="w-full max-w-[520px] bg-[#1A1D2E]/40 border border-white/5 p-8 md:p-12 rounded-[2.5rem] backdrop-blur-3xl shadow-2xl relative z-10">
        
        <div className="flex justify-between items-center mb-10">
          <Link href="/login" className="group flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-slate-500 hover:text-white transition-colors">
             <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
             Back to Terminal
          </Link>
          <div className="flex items-center gap-2">
            <Cpu className="text-[#0066FF] w-4 h-4" />
             <span className="text-[10px] font-bold tracking-tighter text-white uppercase italic">Binding Protocol</span>
          </div>
        </div>

        {!success ? (
          <>
            <header className="mb-6 md:mb-10 text-center px-2">
               <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#0066FF]/10 border border-[#0066FF]/20 text-[#0066FF] text-[8px] md:text-[9px] font-black uppercase tracking-widest mb-3 md:mb-4">
                  <Sparkles className="w-3 md:w-3.5 h-3 md:h-3.5" />
                  New Identity Portal
               </div>
               <h1 className="text-2xl md:text-4xl font-bold text-white tracking-tight mb-2 md:mb-4 italic">
                  Establish <br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#0066FF] to-cyan-400 uppercase">Your Identity.</span>
               </h1>
               <p className="text-slate-500 font-medium text-[11px] md:text-sm">Coordinate your digital workspace with autonomous precision.</p>
            </header>

            <SocialAuthGrid onSelect={handleOAuth} loading={loading} />

            <div className="relative my-10 text-center">
              <div className="absolute inset-y-1/2 left-0 right-0 h-[1px] bg-white/5" />
              <span className="relative z-10 bg-[#16192b] px-6 text-[10px] font-bold uppercase tracking-[0.3em] text-slate-700">Protocol Binding</span>
            </div>

            <motion.form 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              onSubmit={handleRegister} 
              className="space-y-6"
            >
              <AuthInput 
                label="Legal Entity Name" 
                icon={User} 
                type="text"
                placeholder="Full Name / Brand"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />

              <AuthInput 
                label="Registry Email" 
                icon={Mail} 
                type="email"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              
              <AuthInput 
                label="Secure Signature" 
                icon={Lock} 
                type="password"
                id="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                showToggle
                required
              />

              {error && (
                <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-bold flex items-center gap-3">
                  <Zap className="w-4 h-4 shrink-0" />
                  {error}
                </div>
              )}

              <AuthButton 
                label="Initiate Identity Protocol" 
                loading={loading} 
                type="submit"
              />
            </motion.form>
          </>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-12"
          >
            <div className="w-20 h-20 rounded-full bg-[#0066FF]/10 border border-[#0066FF]/20 flex items-center justify-center mx-auto mb-8 shadow-2xl shadow-[#0066FF]/10">
               <ShieldCheck className="w-10 h-10 text-[#0066FF]" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-4 italic uppercase tracking-tight">Registry Confirmed.</h3>
            <p className="text-slate-500 font-medium mb-10 leading-relaxed text-sm px-4">
              Identity portal established. Redirecting to terminal authentication in seconds...
            </p>
            <div className="px-10">
               <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: "0%" }}
                    animate={{ width: "100%" }}
                    transition={{ duration: 2.5 }}
                    className="h-full bg-[#0066FF]"
                  />
               </div>
            </div>
          </motion.div>
        )}

        <footer className="mt-12 text-center text-sm space-y-6">
          <p className="text-slate-600 font-medium">
             Part of the Protocol? <Link href="/login" className="text-white hover:text-[#0066FF] transition-colors font-bold ml-1">Terminal Auth</Link>
          </p>
          
          <div className="flex items-center justify-center gap-4 text-[10px] font-bold text-slate-700 uppercase tracking-widest">
             <Link href="/terms" className="hover:text-slate-400 transition-colors">Terms</Link>
             <span className="w-1 h-1 rounded-full bg-white/5" />
             <Link href="/privacy" className="hover:text-slate-400 transition-colors">Privacy</Link>
             <span className="w-1 h-1 rounded-full bg-white/5" />
             <div className="flex items-center gap-1 font-black text-white/40 italic">FIDO2 SECURE</div>
          </div>
        </footer>
      </section>
    </main>
  );
}

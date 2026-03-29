"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { signIn } from "@/lib/auth-client";
import { useAuthContext } from "@/app/providers/auth-provider";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Mail, 
  Lock, 
  Cpu,
  ArrowLeft,
  ShieldCheck,
  Fingerprint,
  Zap,
  Globe
} from "lucide-react";

import AuthInput from "../components/AuthInput";
import AuthButton from "../components/AuthButton";
import SocialAuthGrid from "../components/SocialAuthGrid";

type AuthTab = "credentials" | "passwordless" | "passkey";

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuthContext();
  const [activeTab, setActiveTab] = useState<AuthTab>("credentials");

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, authLoading, router]);
  
  // State
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ── Handlers ──
  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (activeTab === "credentials") {
        const { error } = await signIn.email({ email, password });
        if (error) throw new Error(error.message || "Invalid credentials");
      } else if (activeTab === "passwordless") {
        const { error } = await signIn.magicLink({ email });
        if (error) throw new Error(error.message || "Failed to send magic link");
      } else if (activeTab === "passkey") {
        const { error } = await signIn.passkey({ email });
        if (error) throw new Error(error.message || "Passkey login failed");
      }
      
      if (activeTab === "credentials") {
        router.replace("/dashboard");
      }
    } catch (err) {
      setError((err as Error).message || "Authentication failed. Please verify your credentials.");
    } finally {
      setLoading(false);
    }
  }

  const handleOAuth = async (provider: "google" | "github" | "discord" | "microsoft") => {
    setLoading(true);
    try {
      await signIn.social({ provider });
    } catch (err) {
      setError("OAuth initiation failed.");
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

      <section className="w-full max-w-[480px] bg-[#1A1D2E]/40 border border-white/5 p-8 md:p-12 rounded-[2.5rem] backdrop-blur-3xl shadow-2xl relative z-10">
        
        <div className="flex justify-between items-center mb-10">
          <Link href="/" className="group flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-slate-500 hover:text-white transition-colors">
             <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
             Back to Home
          </Link>
          <div className="flex items-center gap-2">
            <Cpu className="text-[#0066FF] w-4 h-4" />
            <span className="text-xs font-bold tracking-tighter text-white uppercase italic">GraftAI</span>
          </div>
        </div>

        <header className="mb-6 md:mb-8 text-center px-2">
          <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight mb-2 italic text-glow uppercase">Welcome back.</h2>
          <p className="text-slate-500 font-medium text-[10px] md:text-xs">Re-entering the orchestration layer.</p>
        </header>

        <SocialAuthGrid onSelect={handleOAuth} loading={loading} />

        <div className="relative my-8 text-center">
          <div className="absolute inset-y-1/2 left-0 right-0 h-[1px] bg-white/5" />
          <span className="relative z-10 bg-[#16192b] px-4 text-[9px] font-bold uppercase tracking-[0.3em] text-slate-700">Protocol Entry</span>
        </div>

        {/* ── Tabbed Interface ── */}
        <div className="flex p-1 bg-white/5 rounded-2xl mb-8 border border-white/5">
          <button type="button" onClick={() => setActiveTab("credentials")} className={`flex-1 flex items-center justify-center gap-2 h-11 rounded-xl text-[9px] font-bold uppercase tracking-widest transition-all ${activeTab === 'credentials' ? "bg-[#0066FF] text-white shadow-lg shadow-[#0066FF]/20" : "text-slate-500 hover:text-white"}`}>
             <Zap className="w-3.5 h-3.5" /> Credentials
          </button>
          <button type="button" onClick={() => setActiveTab("passwordless")} className={`flex-1 flex items-center justify-center gap-2 h-11 rounded-xl text-[9px] font-bold uppercase tracking-widest transition-all ${activeTab === 'passwordless' ? "bg-[#0066FF] text-white shadow-lg shadow-[#0066FF]/20" : "text-slate-500 hover:text-white"}`}>
             <Mail className="w-3.5 h-3.5" /> Link
          </button>
          <button type="button" onClick={() => setActiveTab("passkey")} className={`flex-1 flex items-center justify-center gap-2 h-11 rounded-xl text-[9px] font-bold uppercase tracking-widest transition-all ${activeTab === 'passkey' ? "bg-[#0066FF] text-white shadow-lg shadow-[#0066FF]/20" : "text-slate-500 hover:text-white"}`}>
             <Fingerprint className="w-3.5 h-3.5" /> Bio
          </button>
        </div>

        <AnimatePresence mode="wait">
          <motion.form 
            key={activeTab}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onSubmit={handleLogin} 
            className="space-y-5"
          >
            <AuthInput 
              label="Identity Email" 
              icon={Mail} 
              type="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            
            {activeTab === "credentials" && (
              <AuthInput 
                label="Secure Password" 
                icon={Lock} 
                type="password"
                id="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                showToggle
                required
              />
            )}

            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[10px] font-bold flex items-center gap-3">
                <Globe className="w-3.5 h-3.5 shrink-0" />
                {error}
              </div>
            )}

            <AuthButton 
              label={activeTab === 'credentials' ? "Authenticate Entity" : (activeTab === 'passwordless' ? "Dispatch Link" : "Initiate Scan")} 
              loading={loading} 
              type="submit"
            />
          </motion.form>
        </AnimatePresence>

        <footer className="mt-8 text-center space-y-4">
          <p className="text-xs text-slate-600 font-medium">
            New to the Protocol? <Link href="/register" className="text-white hover:text-[#0066FF] transition-colors font-bold ml-1">Establish Portal</Link>
          </p>
          
          <div className="flex items-center justify-center gap-4 text-[9px] font-bold text-slate-700 uppercase tracking-widest">
             <Link href="/terms" className="hover:text-slate-400 transition-colors">Terms</Link>
             <span className="w-1 h-1 rounded-full bg-white/5" />
             <Link href="/privacy" className="hover:text-slate-400 transition-colors">Privacy</Link>
             <span className="w-1 h-1 rounded-full bg-white/5" />
             <div className="flex items-center gap-1"><ShieldCheck className="w-3 h-3" /> Encrypted</div>
          </div>
        </footer>
      </section>
    </main>
  );
}

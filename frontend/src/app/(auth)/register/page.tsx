"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { signUp, signIn } from "@/lib/auth-client";
import { motion } from "framer-motion";
import { Mail, Lock, User, ArrowRight, Loader2, Globe, ShieldCheck } from "lucide-react";
import Link from "next/link";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [timezone, setTimezone] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    // Automatically capture browser timezone
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      setTimezone(tz);
    } catch (e) {
      console.warn("Could not capture timezone", e);
    }
  }, []);

  async function handleRegister(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { error } = await signUp(email, password, fullName, timezone);

      if (error) {
        throw new Error(error.message || "Registration failed");
      }

      setSuccess(true);
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err) {
      setError((err as Error).message || "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell flex min-h-screen flex-col items-center justify-center p-4 relative overflow-hidden bg-slate-950">
      
      {/* Background Ambience */}
      <div className="hidden md:block absolute top-0 left-0 w-full h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="hidden md:block absolute bottom-0 right-0 w-[400px] h-[400px] bg-fuchsia-500/5 rounded-full blur-[100px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-[440px] z-10"
      >
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-fuchsia-600 flex items-center justify-center shadow-[0_0_20px_rgba(79,70,229,0.3)] mb-4">
            <span className="text-white font-bold text-2xl leading-none">G</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-2">Create your account</h1>
          <p className="text-slate-400 text-sm text-center px-4">Get started with GraftAI — the future of AI scheduling</p>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl shadow-xl p-8 relative">
          
          {success ? (
            <motion.div 
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="text-center py-8"
            >
              <div className="w-16 h-16 bg-emerald-500/20 border border-emerald-500/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <ShieldCheck className="w-8 h-8 text-emerald-500" />
              </div>
              <h2 className="text-xl font-bold text-white mb-2">Registration Successful!</h2>
              <p className="text-slate-400 mb-6 text-sm">Redirecting you to login...</p>
              <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                <motion.div 
                   initial={{ width: "0%" }}
                   animate={{ width: "100%" }}
                   transition={{ duration: 2 }}
                   className="bg-primary h-full"
                />
              </div>
            </motion.div>
          ) : (
            <form className="space-y-4" onSubmit={handleRegister}>
              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-400 uppercase tracking-wider ml-1">Full Name</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-4 w-4 text-slate-500" />
                  </div>
                  <input
                    type="text" required value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="block w-full pl-10 pr-3 py-3 border border-slate-700/50 rounded-xl bg-slate-800/30 text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm"
                    placeholder="John Doe"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-400 uppercase tracking-wider ml-1">Email Address</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-4 w-4 text-slate-500" />
                  </div>
                  <input
                    type="email" required value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full pl-10 pr-3 py-3 border border-slate-700/50 rounded-xl bg-slate-800/30 text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm"
                    placeholder="name@company.com"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-400 uppercase tracking-wider ml-1">Password</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-4 w-4 text-slate-500" />
                  </div>
                  <input
                    type="password" required value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full pl-10 pr-3 py-3 border border-slate-700/50 rounded-xl bg-slate-800/30 text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-sm"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              {timezone && (
                <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/30 rounded-lg border border-slate-700/30">
                  <Globe className="w-3 h-3 text-slate-500" />
                  <span className="text-[10px] text-slate-500 font-mono uppercase">Timezone: {timezone}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full relative group flex justify-center items-center gap-2 py-3.5 px-4 rounded-xl text-sm font-semibold text-white bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-[0_0_20px_rgba(79,70,229,0.2)] overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
                {loading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Creating account...</>
                ) : (
                  <><span className="relative z-10">Get Started Now</span> <ArrowRight className="w-4 h-4 relative z-10" /></>
                )}
              </button>
            </form>
          )}

          {!success && (
            <>
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-800"></div>
                </div>
                <div className="relative flex justify-center text-[10px] uppercase tracking-widest">
                  <span className="bg-slate-900 px-2 text-slate-500">Or join with</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pb-2">
                <button
                  type="button"
                  onClick={() => signIn.social("google")}
                  disabled={loading}
                  className="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl text-[12px] font-medium text-slate-300 bg-slate-800/40 border border-slate-700/50 hover:bg-slate-800/60 hover:border-slate-600 transition-all active:scale-[0.98] disabled:opacity-50"
                >
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="currentColor" d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l3.66-2.84z" />
                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                  </svg>
                  Google
                </button>
                <button
                  type="button"
                  onClick={() => signIn.social("microsoft")}
                  disabled={loading}
                  className="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl text-[12px] font-medium text-slate-300 bg-slate-800/40 border border-slate-700/50 hover:bg-slate-800/60 hover:border-slate-600 transition-all active:scale-[0.98] disabled:opacity-50"
                >
                  <svg className="w-3.5 h-3.5" viewBox="0 0 23 23">
                    <path fill="currentColor" d="M0 0h11v11H0z" />
                    <path fill="currentColor" d="M12 0h11v11H12z" />
                    <path fill="currentColor" d="M0 12h11v11H0z" />
                    <path fill="currentColor" d="M12 12h11v11H12z" />
                  </svg>
                  Microsoft
                </button>
              </div>
            </>
          )}

          {error && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="mt-4 text-xs text-red-400 bg-red-400/10 border border-red-400/20 p-3 rounded-xl flex items-center gap-2"
            >
              <div className="w-1 h-1 rounded-full bg-red-400 shrink-0" />
              {error}
            </motion.div>
          )}
        </div>

        <div className="mt-8 text-center">
          <p className="text-sm text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-primary hover:text-primary/80 transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>
    </main>
  );
}

"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { signIn } from "@/lib/auth-client";
import { motion } from "framer-motion";
import { Mail, Lock, ArrowRight, Loader2, Play } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleCredentialLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail || !password) {
      setError("Please enter both email and password.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const { error: authError } = await signIn.email({ email: normalizedEmail, password });
      if (authError) {
        throw new Error(authError.message || "Invalid credentials");
      }
      router.replace("/dashboard");
    } catch (err) {
      setError((err as Error).message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-[100dvh] flex flex-col items-center justify-center p-5 bg-[#070711] relative overflow-hidden font-sans">
      {/* ── Ambient background matching landing page ── */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-[20%] left-[20%] h-[500px] w-[500px] rounded-full bg-indigo-600/10 blur-[120px]" />
        <div className="absolute top-[40%] right-[-10%] h-[400px] w-[400px] rounded-full bg-violet-600/8 blur-[100px]" />
        <div className="absolute bottom-[-10%] left-[10%] h-[400px] w-[400px] rounded-full bg-blue-600/6 blur-[100px]" />
        <div 
          className="absolute inset-0 opacity-[0.03]" 
          style={{ 
            backgroundImage: "linear-gradient(rgba(148,163,184,1) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,1) 1px, transparent 1px)", 
            backgroundSize: "60px 60px" 
          }} 
        />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 15 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-[420px] z-10"
      >
        <div className="flex flex-col items-center mb-8 text-center">
          <Link href="/" className="group mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-xl shadow-indigo-500/20 transition-all hover:scale-105 hover:shadow-indigo-500/40">
            <span className="text-2xl font-black text-white leading-none">G</span>
          </Link>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white mb-2" style={{ fontFamily: "'DM Serif Display', Georgia, serif" }}>
            Welcome back
          </h1>
          <p className="text-slate-400 text-sm font-medium">
            Sign in to continue to your dashboard.
          </p>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-2xl border border-slate-700/40 rounded-3xl shadow-2xl p-6 sm:p-8 relative overflow-hidden ring-1 ring-white/5">
          <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-indigo-500/30 to-transparent" />
          
          <form className="space-y-4" onSubmit={handleCredentialLogin}>
            <div className="space-y-3.5">
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors group-focus-within:text-indigo-400 text-slate-500">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3.5 border border-slate-700/60 rounded-2xl bg-slate-950/40 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all text-sm font-medium"
                  placeholder="name@company.com"
                />
              </div>

              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors group-focus-within:text-indigo-400 text-slate-500">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3.5 border border-slate-700/60 rounded-2xl bg-slate-950/40 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all text-sm font-medium"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-2 py-3.5 px-4 rounded-2xl text-sm font-bold text-slate-900 bg-white hover:bg-slate-100 shadow-xl shadow-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98] mt-2 group"
            >
              {loading ? (
                <><Loader2 className="w-4 h-4 animate-spin text-slate-500" /> <span className="text-slate-600">Signing in...</span></>
              ) : (
                <>Sign in securely <ArrowRight className="w-4 h-4 text-slate-400 transition-transform group-hover:translate-x-0.5" /></>
              )}
            </button>
          </form>
          
          <div className="relative my-7">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800/80"></div>
            </div>
            <div className="relative flex justify-center text-[10px] font-bold uppercase tracking-wider">
              <span className="bg-slate-900/60 px-3 text-slate-500 backdrop-blur-md rounded-full border border-slate-800/80 py-0.5">Or continue with</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:gap-4">
            <button
              onClick={() => signIn.social("google")}
              disabled={loading}
              className="flex items-center justify-center gap-2.5 py-3 rounded-2xl text-[13px] font-semibold text-slate-300 bg-slate-800/30 border border-slate-700/50 hover:bg-slate-800/60 hover:border-slate-600 transition-all active:scale-[0.98] disabled:opacity-50"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="currentColor" d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l3.66-2.84z" />
                <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              Google
            </button>
            <button
              onClick={() => signIn.social("microsoft")}
              disabled={loading}
              className="flex items-center justify-center gap-2.5 py-3 rounded-2xl text-[13px] font-semibold text-slate-300 bg-slate-800/30 border border-slate-700/50 hover:bg-slate-800/60 hover:border-slate-600 transition-all active:scale-[0.98] disabled:opacity-50"
            >
              <svg className="w-4 h-4" viewBox="0 0 23 23">
                <path fill="currentColor" d="M0 0h11v11H0z" />
                <path fill="currentColor" d="M12 0h11v11H12z" />
                <path fill="currentColor" d="M0 12h11v11H0z" />
                <path fill="currentColor" d="M12 12h11v11H12z" />
              </svg>
              Microsoft
            </button>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0, marginTop: 0 }}
              animate={{ opacity: 1, height: "auto", marginTop: 16 }}
              className="overflow-hidden"
            >
              <div className="flex items-center gap-2 text-[13px] font-medium text-rose-400 bg-rose-500/10 border border-rose-500/20 p-3 rounded-xl">
                {error}
              </div>
            </motion.div>
          )}
        </div>

        <div className="mt-8 flex flex-col items-center gap-3">
          <p className="text-[13px] font-medium text-slate-400">
            Don't have an account?{" "}
            <Link href="/register" className="text-white hover:text-indigo-300 transition-colors pointer-events-auto">
              Create one now
            </Link>
          </p>
          <div className="flex items-center gap-4 text-[11px] font-semibold text-slate-600">
            <Link href="/privacy-policy" className="hover:text-slate-400 transition-colors">Privacy</Link>
            <Link href="/terms-of-service" className="hover:text-slate-400 transition-colors">Terms of Service</Link>
          </div>
        </div>
      </motion.div>
    </main>
  );
}

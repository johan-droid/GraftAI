"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { signIn } from "@/lib/auth-client";
import { motion } from "framer-motion";
import { Mail, Lock, ArrowRight, Loader2 } from "lucide-react";

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
    <main className="app-shell flex min-h-screen flex-col items-center justify-start px-4 pb-10 pt-12 md:pt-20 relative overflow-hidden">
      <div className="hidden md:block absolute top-0 right-0 w-full h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="hidden md:block absolute bottom-1/4 left-1/4 w-[300px] h-[300px] bg-fuchsia-500/5 rounded-full blur-[100px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="w-full max-w-[400px] z-10"
      >
        <div className="flex flex-col items-center mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-fuchsia-600 flex items-center justify-center shadow-[0_0_15px_rgba(79,70,229,0.4)] mb-3">
            <span className="text-white font-bold text-xl leading-none">G</span>
          </div>
          <h1 className="text-xl font-semibold tracking-tight text-white mb-1.5">Welcome back</h1>
          <p className="text-slate-500 text-[13px] text-center leading-relaxed">
            Sign in with your email and password.
          </p>
        </div>

        <div className="spotlight-card bg-slate-950/40 backdrop-blur-xl border border-white/[0.08] rounded-2xl shadow-2xl p-6 md:p-7 relative overflow-hidden">
          <div className="pixel-grid opacity-20 pointer-events-none" />

          <form className="space-y-3" onSubmit={handleCredentialLogin}>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-3.5 w-3.5 text-slate-600" />
              </div>
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="block w-full pl-9 pr-3 py-2.5 border border-white/[0.05] rounded-xl bg-white/[0.03] text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all text-[13px]"
                placeholder="name@company.com"
              />
            </div>

            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-3.5 w-3.5 text-slate-600" />
              </div>
              <input
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="block w-full pl-9 pr-3 py-2.5 border border-white/[0.05] rounded-xl bg-white/[0.03] text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all text-[13px]"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-2 py-2.5 px-4 rounded-xl text-[13px] font-semibold text-white bg-primary/90 hover:bg-primary shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
            >
              {loading ? (
                <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Please wait...</>
              ) : (
                <>Sign In <ArrowRight className="w-3.5 h-3.5" /></>
              )}
            </button>
          </form>
          
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/[0.05]"></div>
            </div>
            <div className="relative flex justify-center text-[11px] uppercase tracking-wider">
              <span className="bg-[#020617]/80 px-2 text-slate-600 backdrop-blur-sm">Or continue with</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => signIn.social("google")}
              disabled={loading}
              className="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl text-[12px] font-medium text-slate-300 bg-white/[0.03] border border-white/[0.08] hover:bg-white/[0.06] hover:border-white/[0.12] transition-all active:scale-[0.98] disabled:opacity-50"
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
              onClick={() => signIn.social("microsoft")}
              disabled={loading}
              className="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl text-[12px] font-medium text-slate-300 bg-white/[0.03] border border-white/[0.08] hover:bg-white/[0.06] hover:border-white/[0.12] transition-all active:scale-[0.98] disabled:opacity-50"
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

          {error && (
            <motion.p
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mt-3 text-sm text-red-400 bg-red-400/10 border border-red-400/20 p-3 rounded-xl"
            >
              {error}
            </motion.p>
          )}
        </div>

        <div className="mt-6 flex flex-col items-center gap-2">
          <p className="text-sm text-slate-500">
            Do not have an account?{" "}
            <Link href="/register" className="font-medium text-primary hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </motion.div>
    </main>
  );
}

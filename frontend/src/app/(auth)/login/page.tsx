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

"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { signIn } from "@/lib/auth-client";
import { AnimatePresence, motion } from "framer-motion";
import { Mail, Lock, ArrowRight, Loader2, Shield, Fingerprint, Eye, EyeOff } from "lucide-react";

type Tab = "email" | "sso" | "passkey";

export default function LoginPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("email");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCredentialLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    const normalizedEmail = email.trim().toLowerCase();

    if (!normalizedEmail || !password) {
      setError("Please enter your email and password.");
      return;
    }

    setLoading(true);
    try {
      const { error: authError } = await signIn.email({ email: normalizedEmail, password });
      if (authError) {
        throw new Error(authError.message || "Unable to sign in.");
      }
      router.replace("/dashboard");
    } catch (err) {
      setError((err as Error).message || "Unable to sign in.");
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = async (provider: "google" | "microsoft") => {
    setError("");
    setLoading(true);
    try {
      await signIn.social(provider);
    } catch (err) {
      setError((err as Error).message || "OAuth failed.");
      setLoading(false);
    }
  };

  const handlePasskey = async () => {
    setError("");
    setLoading(true);
    try {
      const { error: authError } = await signIn.passkey();
      if (authError) {
        throw new Error(authError.message || "Passkey login failed.");
      }
      router.replace("/dashboard");
    } catch (err) {
      setError((err as Error).message || "Passkey authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-[100dvh] bg-[#030712] flex items-center justify-center p-4 relative overflow-hidden text-slate-100">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-0 h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-indigo-500/10 blur-[120px]" />
        <div className="absolute right-0 top-1/4 h-[320px] w-[320px] rounded-full bg-violet-500/8 blur-[100px]" />
        <div className="absolute left-0 bottom-0 h-[320px] w-[320px] rounded-full bg-cyan-500/8 blur-[100px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 w-full max-w-[460px]"
      >
        <div className="mb-7 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-xl shadow-indigo-500/25">
            <span className="text-2xl font-black text-white">G</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Welcome back</h1>
          <p className="mt-2 text-sm text-slate-400">Securely access your scheduling workspace and AI assistant.</p>
        </div>

        <div className="overflow-hidden rounded-[2rem] border border-white/[0.06] bg-white/[0.02] p-6 shadow-[0_30px_70px_-50px_rgba(15,23,42,0.75)] backdrop-blur-xl sm:p-8">
          <div className="flex flex-col gap-2 rounded-3xl bg-slate-950/70 p-1 border border-slate-800/70 mb-6">
            {([
              { id: "email", label: "Email", icon: Mail },
              { id: "sso", label: "SSO", icon: Shield },
              { id: "passkey", label: "Passkey", icon: Fingerprint },
            ] as { id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[]).map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => { setTab(id); setError(""); }}
                className={`flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition ${tab === id ? "bg-indigo-600 text-white shadow-[0_15px_35px_-22px_rgba(79,70,229,0.8)]" : "text-slate-400 hover:text-slate-200 hover:bg-white/5"}`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {tab === "email" && (
              <motion.form
                key="email"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="space-y-4"
                onSubmit={handleCredentialLogin}
              >
                <div className="space-y-4">
                  <label className="block text-sm font-medium text-slate-300">Email</label>
                  <div className="relative">
                    <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500"><Mail className="h-4 w-4" /></span>
                    <input
                      type="email"
                      autoComplete="email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      placeholder="you@company.com"
                      className="w-full rounded-3xl border border-white/[0.06] bg-slate-900/80 py-3 pl-11 pr-4 text-sm text-white placeholder-slate-500 outline-none ring-1 ring-transparent transition focus:border-indigo-500/70 focus:ring-indigo-500/20"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <label className="block text-sm font-medium text-slate-300">Password</label>
                  <div className="relative">
                    <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500"><Lock className="h-4 w-4" /></span>
                    <input
                      type={showPassword ? "text" : "password"}
                      autoComplete="current-password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      placeholder="Enter your password"
                      className="w-full rounded-3xl border border-white/[0.06] bg-slate-900/80 py-3 pl-11 pr-11 text-sm text-white placeholder-slate-500 outline-none ring-1 ring-transparent transition focus:border-indigo-500/70 focus:ring-indigo-500/20"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500 hover:text-slate-300"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="flex w-full items-center justify-center gap-2 rounded-3xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Signing in...</>
                  ) : (
                    <>Sign in <ArrowRight className="h-4 w-4" /></>
                  )}
                </button>
              </motion.form>
            )}

            {tab === "sso" && (
              <motion.div
                key="sso"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="space-y-4"
              >
                <p className="text-sm text-slate-400">Use your existing company identity or social account.</p>
                <div className="grid gap-3">
                  <button
                    onClick={() => handleOAuth("google")}
                    disabled={loading}
                    className="flex items-center justify-center gap-3 rounded-3xl border border-white/[0.08] bg-slate-900/80 px-4 py-3 text-sm font-semibold text-slate-100 transition hover:border-indigo-500/40 hover:bg-slate-800/90 disabled:opacity-50"
                  >
                    <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-white/10">
                      <Mail className="h-4 w-4 text-white" />
                    </span>
                    Continue with Google
                  </button>
                  <button
                    onClick={() => handleOAuth("microsoft")}
                    disabled={loading}
                    className="flex items-center justify-center gap-3 rounded-3xl border border-white/[0.08] bg-slate-900/80 px-4 py-3 text-sm font-semibold text-slate-100 transition hover:border-indigo-500/40 hover:bg-slate-800/90 disabled:opacity-50"
                  >
                    <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-white/10">
                      <Shield className="h-4 w-4 text-white" />
                    </span>
                    Continue with Microsoft
                  </button>
                </div>
                <p className="text-center text-xs uppercase tracking-[0.24em] text-slate-500">We’ll redirect you securely.</p>
              </motion.div>
            )}

            {tab === "passkey" && (
              <motion.div
                key="passkey"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="space-y-5"
              >
                <div className="rounded-3xl border border-white/[0.08] bg-slate-950/70 p-5 text-center">
                  <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-3xl bg-indigo-500/10 text-indigo-300">
                    <Fingerprint className="h-6 w-6" />
                  </div>
                  <p className="text-sm font-semibold text-white">Authenticate with your device</p>
                  <p className="mt-2 text-sm text-slate-400">Use biometrics or a security key for passwordless access.</p>
                </div>
                <button
                  type="button"
                  onClick={handlePasskey}
                  disabled={loading}
                  className="flex w-full items-center justify-center gap-2 rounded-3xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-500 disabled:opacity-50"
                >
                  {loading ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Authenticating…</>
                  ) : (
                    <>Use Passkey <Shield className="h-4 w-4" /></>
                  )}
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {error && (
            <div className="mt-6 rounded-3xl border border-rose-500/20 bg-rose-500/10 p-4 text-sm text-rose-200">
              {error}
            </div>
          )}
        </div>

        <div className="mt-6 flex flex-col items-center gap-3 text-center">
          <p className="text-sm text-slate-500">
            New here?{' '}
            <Link href="/register" className="text-white hover:text-indigo-300 transition-colors">
              Create an account
            </Link>
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 text-[11px] font-semibold text-slate-600">
            <Link href="/privacy-policy" className="hover:text-slate-400 transition-colors">Privacy</Link>
            <Link href="/terms-of-service" className="hover:text-slate-400 transition-colors">Terms</Link>
          </div>
        </div>
      </motion.div>
    </main>
  );
}
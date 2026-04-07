"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { signUp, signIn } from "@/lib/auth-client";
import { motion } from "framer-motion";
import { Mail, Lock, User, ArrowRight, Loader2, Eye, EyeOff, Zap, CheckCircle, Shield } from "lucide-react";
import Link from "next/link";

const PERKS = [
  "Unlimited booking pages",
  "AI-powered scheduling",
  "Cross-timezone coordination",
  "Google & Zoom integrations",
];

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [timezone, setTimezone] = useState("");

  useEffect(() => {
    try {
      setTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone);
    } catch {
      /* empty */
    }
  }, []);

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const { error: authError } = await signUp(email, password, fullName, timezone);
      if (authError) {
        throw new Error(authError.message ?? "Registration failed");
      }

      setSuccess(true);
      setTimeout(() => router.push("/login"), 2500);
    } catch (err) {
      setError((err as Error).message ?? "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = async (provider: "google" | "microsoft") => {
    setError("");
    setLoading(true);
    try {
      const { error: socialError } = await signIn.social(provider);
      if (socialError) {
        throw new Error(socialError.message || "Social sign-in failed.");
      }
    } catch (err) {
      setError((err as Error).message || "Social sign-in failed.");
      setLoading(false);
    }
  };

  const passwordStrength =
    password.length === 0 ? 0 : password.length < 6 ? 1 : password.length < 10 ? 2 : 3;

  return (
    <main className="min-h-screen bg-[#030712] flex overflow-hidden">
      <div className="hidden lg:flex flex-col justify-between w-[480px] shrink-0 bg-gradient-to-br from-indigo-600/20 via-[#030712] to-violet-600/10 border-r border-white/[0.06] p-12 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-0 w-[400px] h-[400px] bg-indigo-600/20 rounded-full blur-[100px]" />
          <div className="absolute bottom-0 right-0 w-[300px] h-[300px] bg-violet-600/15 rounded-full blur-[80px]" />
        </div>
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-xl shadow-indigo-500/30 ring-1 ring-white/20">
              <Zap className="w-5 h-5 text-white fill-white" />
            </div>
            <span className="text-xl font-black text-white tracking-tight">GraftAI</span>
          </div>
          <h2 className="font-serif text-4xl sm:text-5xl font-black text-white leading-[1.1] mb-6">
            Smarter<br />scheduling<br />starts here.
          </h2>
          <p className="max-w-[300px] text-slate-400 text-[15px] leading-relaxed mb-12 font-medium">
            Join the elite tier of productivity. Coordinate across time zones, effortlessly.
          </p>
          <div className="space-y-4">
            {PERKS.map((perk) => (
              <div key={perk} className="flex items-center gap-4">
                <div className="w-6 h-6 rounded-full bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center shrink-0">
                  <CheckCircle className="w-3.5 h-3.5 text-indigo-400" />
                </div>
                <span className="text-[14px] text-slate-300 font-semibold">{perk}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="relative z-10 flex items-center gap-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-600">© 2026 GraftAI · Sovereign Edition</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 relative">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 right-0 w-[400px] h-[300px] bg-violet-600/5 rounded-full blur-[100px]" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-[380px] z-10"
        >
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white fill-white" />
            </div>
            <span className="font-bold text-white">GraftAI</span>
          </div>

          <h1 className="text-2xl font-bold text-white mb-1">Create your account</h1>
          <p className="text-slate-500 text-sm mb-7">Free forever · No credit card required</p>

          {success ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center py-10 rounded-2xl border border-emerald-500/20 bg-emerald-500/5"
            >
              <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
              <h2 className="text-lg font-bold text-white mb-2">Account created!</h2>
              <p className="text-sm text-slate-400">Redirecting you to login…</p>
              <div className="w-32 h-0.5 bg-white/5 rounded-full overflow-hidden mx-auto mt-5">
                <motion.div initial={{ width: 0 }} animate={{ width: "100%" }} transition={{ duration: 2.5 }} className="h-full bg-emerald-500 rounded-full" />
              </div>
            </motion.div>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500/60 transition-colors"
                  placeholder="Your full name"
                />
              </div>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500/60 transition-colors"
                  placeholder="you@company.com"
                />
              </div>
              <div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600" />
                  <input
                    type={showPass ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-10 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500/60 transition-colors"
                    placeholder="Create a strong password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(!showPass)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-400"
                    aria-label={showPass ? "Hide password" : "Show password"}
                  >
                    {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {password.length > 0 && (
                  <div className="flex gap-1.5 mt-2">
                    {[1, 2, 3].map((level) => (
                      <div
                        key={level}
                        className={`h-1 flex-1 rounded-full transition-colors ${
                          passwordStrength >= level
                            ? level === 1
                              ? "bg-red-500"
                              : level === 2
                              ? "bg-amber-400"
                              : "bg-emerald-400"
                            : "bg-white/10"
                        }`}
                      />
                    ))}
                  </div>
                )}
              </div>

              {error && (
                <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-xs text-red-400 bg-red-400/8 border border-red-400/15 px-3 py-2.5 rounded-xl">
                  {error}
                </motion.p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center items-center gap-2 py-3 rounded-xl text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition-all shadow-lg shadow-indigo-600/20"
              >
                {loading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Creating account…</>
                ) : (
                  <>Get started free <ArrowRight className="w-4 h-4" /></>
                )}
              </button>

              <div className="relative py-2 flex items-center gap-4">
                <div className="flex-1 h-px bg-white/5" />
                <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">or</span>
                <div className="flex-1 h-px bg-white/5" />
              </div>

              <div className="grid grid-cols-1 gap-3">
                <button
                  type="button"
                  onClick={() => handleOAuth("google")}
                  disabled={loading}
                  className="flex items-center justify-center gap-3 w-full py-2.5 rounded-xl border border-white/5 bg-white/[0.03] hover:bg-white/[0.06] text-[13px] font-semibold text-slate-200 transition-all disabled:opacity-50"
                >
                  <Mail className="w-4 h-4 text-indigo-400" />
                  Continue with Google
                </button>
                <button
                  type="button"
                  onClick={() => handleOAuth("microsoft")}
                  disabled={loading}
                  className="flex items-center justify-center gap-3 w-full py-2.5 rounded-xl border border-white/5 bg-white/[0.03] hover:bg-white/[0.06] text-[13px] font-semibold text-slate-200 transition-all disabled:opacity-50"
                >
                  <Shield className="w-4 h-4 text-violet-400" />
                  Continue with Microsoft
                </button>
              </div>

              <p className="text-[11px] text-center text-slate-600 leading-relaxed">
                By signing up you agree to our {" "}
                <a href="/terms" className="text-slate-500 hover:text-slate-300">Terms of Service</a>
                {" and "}
                <a href="/privacy" className="text-slate-500 hover:text-slate-300">Privacy Policy</a>.
                {timezone && ` Timezone: ${timezone}.`}
              </p>
            </form>
          )}

          <p className="mt-6 text-center text-sm text-slate-600">
            Already have an account? {" "}
            <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold transition-colors">Sign in</Link>
          </p>
        </motion.div>
      </div>
    </main>
  );
}

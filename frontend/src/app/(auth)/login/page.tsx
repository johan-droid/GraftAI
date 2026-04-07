"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { getSessionSafe, signIn } from "@/lib/auth-client";
import { useAuthContext } from "@/app/providers/auth-provider";
import { AnimatePresence, motion } from "framer-motion";
import { Mail, Lock, ArrowRight, Loader2, Shield, Fingerprint, Eye, EyeOff, Zap } from "lucide-react";

type Tab = "email" | "sso" | "passwordless";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthContext();
  const [tab, setTab] = useState<Tab>("email");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [passkeyEmail, setPasskeyEmail] = useState("");
  const [passkeyStatus, setPasskeyStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const waitForSessionReady = async () => {
    for (let attempt = 0; attempt < 3; attempt += 1) {
      const sessionResult = await getSessionSafe();
      if (sessionResult?.data?.authenticated) {
        return true;
      }
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
    return false;
  };

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

      const sessionReady = await waitForSessionReady();
      if (!sessionReady) {
        throw new Error("Login succeeded but session is not ready yet. Please retry.");
      }

      router.replace("/dashboard");
    } catch (err) {
      setError((err as Error).message || "Unable to sign in.");
    } finally {
      setLoading(false);
    }
  };

  const handleSAML = async () => {
    setError("");
    setLoading(true);
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "";
    window.location.assign(`${backendUrl}/api/v1/auth/saml/login`);
  };

  const handleOAuth = async (provider: "google" | "microsoft" | "zoom") => {
    setError("");
    setLoading(true);
    try {
      const { error: socialError } = await signIn.social(provider);
      if (socialError) {
        throw new Error(socialError.message || "OAuth failed.");
      }
    } catch (err) {
      setError((err as Error).message || "OAuth failed.");
      setLoading(false);
    }
  };

  const handlePasskeyRegister = async () => {
    setError("");
    setPasskeyStatus("");
    setLoading(true);
    try {
      const { data, error: passkeyError } = await signIn.passkeyRegister({ email: passkeyEmail });
      if (passkeyError || !data) {
        throw new Error(passkeyError?.message || "Unable to register passkey.");
      }
      setPasskeyStatus("Fingerprint registration successful. You can now sign in with your passkey.");
    } catch (err) {
      setError((err as Error).message || "Passkey registration failed.");
    } finally {
      setLoading(false);
    }
  };

  const handlePasskeyLogin = async () => {
    setError("");
    setPasskeyStatus("");
    setLoading(true);
    try {
      const { data, error: passkeyError } = await signIn.passkeyLogin({ email: passkeyEmail });
      if (passkeyError || !data || typeof data !== "object" || !("access_token" in data)) {
        throw new Error(passkeyError?.message || "Unable to sign in with passkey.");
      }
      const tokenData = data as { access_token: string };
      await login(tokenData.access_token);
      router.replace("/dashboard");
    } catch (err) {
      setError((err as Error).message || "Passkey login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-dvh bg-[#070711] flex flex-col items-center justify-center p-6 relative overflow-hidden font-sans selection:bg-indigo-500/30">
      {/* Sovereign Background Engine */}
      <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
        {/* Fractal Noise Component */}
        <svg className="absolute h-full w-full opacity-[0.03] contrast-150 grayscale" xmlns="http://www.w3.org/2000/svg">
          <filter id="fractal">
            <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" />
          </filter>
          <rect width="100%" height="100%" filter="url(#fractal)" />
        </svg>

        {/* Dynamic Light Leaks */}
        <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-indigo-600/20 blur-[120px] rounded-full opacity-40 mix-blend-screen animate-[pulse_8s_ease-in-out_infinite]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] bg-violet-600/15 blur-[100px] rounded-full opacity-30 mix-blend-screen animate-[pulse_12s_ease-in-out_infinite]" />
        <div className="absolute top-1/2 left-[-10%] w-[500px] h-[500px] bg-cyan-600/10 blur-[100px] rounded-full opacity-20 mix-blend-screen" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 w-full max-w-[410px]"
      >
        {/* Branding & Header */}
        <div className="mb-8 text-center">
          <motion.div 
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-[1.5rem] bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-700 shadow-[0_20px_40px_-10px_rgba(79,70,229,0.5)] ring-1 ring-white/30"
          >
            <Zap className="h-8 w-8 text-white fill-white animate-pulse" />
          </motion.div>
          <h1 className="font-serif text-4xl sm:text-5xl font-black tracking-tight text-white mb-3">
            Graft<span className="text-white/40">AI</span>
          </h1>
          <p className="max-w-[280px] mx-auto text-sm font-medium leading-relaxed text-slate-400">
            Secure access to your <span className="text-indigo-400">Scheduling Sovereignty</span>.
          </p>
        </div>

        {/* Main Login Card */}
        <div className="group relative overflow-hidden rounded-[2.5rem] border border-white/[0.08] bg-white/[0.03] p-1 shadow-[0_40px_80px_-40px_rgba(0,0,0,0.8)] backdrop-blur-[32px]">
          {/* Subtle Glow Effect */}
          <div className="absolute inset-0 -z-10 bg-gradient-to-br from-indigo-500/5 via-transparent to-violet-500/5 opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
          
          <div className="p-6 sm:p-8">
            {/* Horizontal Segmented Control */}
            <div className="relative flex p-1 mb-8 rounded-2xl bg-slate-950/60 border border-white/[0.05] shadow-inner">
              <div
                className={`absolute top-1 bottom-1 transition-all duration-300 ease-out bg-indigo-600 rounded-xl shadow-[0_4px_12px_rgba(79,70,229,0.4)] ${
                  tab === 'email'
                    ? 'left-1 w-[calc(33.33%-4px)]'
                    : tab === 'sso'
                    ? 'left-[33.33%] w-[calc(33.33%-4px)]'
                    : 'left-[66.66%] w-[calc(33.33%-4px)]'
                }`}
              />
              {[
                { id: "email", label: "Email", icon: Mail },
                { id: "sso", label: "SSO", icon: Shield },
                { id: "passwordless", label: "Passkey", icon: Fingerprint },
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => { setTab(id as Tab); setError(""); }}
                  className={`relative z-10 flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-bold transition-colors duration-200 ${tab === id ? "text-white" : "text-slate-400 hover:text-slate-200"}`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {label}
                </button>
              ))}
            </div>

            <AnimatePresence mode="wait">
              {tab === "email" && (
                <motion.form
                  key="email"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-4"
                  onSubmit={handleCredentialLogin}
                >
                  <div className="space-y-2">
                    <label className="text-[11px] uppercase tracking-widest font-black text-slate-500 px-1">Email Address</label>
                    <div className="relative group">
                      <div className="absolute inset-y-0 left-0 flex items-center pl-4 text-slate-500 transition-colors group-focus-within:text-indigo-400">
                        <Mail className="h-4 w-4" />
                      </div>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="name@company.com"
                        className="w-full rounded-2xl border border-white/[0.06] bg-slate-900/50 py-3.5 pl-11 pr-4 text-sm text-white placeholder-slate-600 outline-none ring-1 ring-transparent transition-all focus:border-indigo-500/50 focus:ring-indigo-500/10 focus:bg-slate-900/80"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-[11px] uppercase tracking-widest font-black text-slate-500 px-1">Security Code</label>
                    <div className="relative group">
                      <div className="absolute inset-y-0 left-0 flex items-center pl-4 text-slate-500 transition-colors group-focus-within:text-indigo-400">
                        <Lock className="h-4 w-4" />
                      </div>
                      <input
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full rounded-2xl border border-white/[0.06] bg-slate-900/50 py-3.5 pl-11 pr-12 text-sm text-white placeholder-slate-600 outline-none ring-1 ring-transparent transition-all focus:border-indigo-500/50 focus:ring-indigo-500/10 focus:bg-slate-900/80"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute inset-y-0 right-0 flex items-center pr-4 text-slate-500 hover:text-white transition-colors"
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="group relative w-full overflow-hidden rounded-2xl bg-indigo-600 py-3.5 text-sm font-black text-white shadow-xl shadow-indigo-500/20 transition-all hover:bg-indigo-500 active:scale-[0.98] disabled:opacity-50"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 -translate-x-[100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                    <span className="relative flex items-center justify-center gap-2">
                      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <>Enter Console <ArrowRight className="h-4 w-4" /></>}
                    </span>
                  </button>
                </motion.form>
              )}

              {tab === "sso" && (
                <motion.div
                  key="sso"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-3"
                >
                  <div className="grid gap-3">
                    <button
                      onClick={() => handleOAuth("google")}
                      disabled={loading}
                      className="flex items-center gap-3 rounded-2xl border border-white/[0.08] bg-slate-900/50 px-4 py-3 text-sm font-bold text-slate-200 transition-all hover:bg-slate-800 hover:border-white/20 disabled:opacity-50"
                    >
                      <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                        <path d="M22.5 12.27c0-.74-.06-1.45-.17-2.14H12v4.05h5.92c-.26 1.42-1.04 2.63-2.23 3.44v2.86h3.61c2.1-1.94 3.29-4.83 3.29-8.21Z" fill="#4285F4"/>
                        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.61-2.86c-1.01.68-2.28 1.09-3.67 1.09-2.82 0-5.21-1.91-6.06-4.49H2.22v2.82C4.03 20.95 7.75 23 12 23Z" fill="#34A853"/>
                        <path d="M5.94 14.08c-.22-.65-.35-1.34-.35-2.08 0-.74.13-1.43.35-2.08V7.1H2.22A11.96 11.96 0 0 0 0 12c0 1.96.47 3.81 1.3 5.44l3.64-2.82Z" fill="#FBBC05"/>
                        <path d="M12 4.88c1.61 0 3.05.56 4.19 1.66l3.14-3.14C17.43 1.61 14.97.5 12 .5 7.75.5 4.03 2.55 2.22 5.1l3.72 2.82C6.79 6.79 9.18 4.88 12 4.88Z" fill="#EA4335"/>
                      </svg>
                      Sign in with Google
                    </button>
                    <button
                      onClick={() => handleOAuth("microsoft")}
                      disabled={loading}
                      className="flex items-center gap-3 rounded-2xl border border-white/[0.08] bg-slate-900/50 px-4 py-3 text-sm font-bold text-slate-200 transition-all hover:bg-slate-800 hover:border-white/20 disabled:opacity-50"
                    >
                      <svg className="h-5 w-5" viewBox="0 0 23 23"><path fill="#f3f3f3" d="M0 0h11v11H0z"/><path fill="#f3f3f3" d="M12 0h11v11H12z"/><path fill="#f3f3f3" d="M0 12h11v11H0z"/><path fill="#f3f3f3" d="M12 12h11v11H12z"/></svg>
                      Continue with Microsoft
                    </button>
                    <div className="relative my-2 py-2 flex items-center gap-4 before:h-px before:flex-1 before:bg-white/[0.05] after:h-px after:flex-1 after:bg-white/[0.05]">
                      <span className="text-[9px] uppercase font-black text-slate-600 tracking-[0.2em]">Enterprise</span>
                    </div>
                    <button
                      onClick={handleSAML}
                      disabled={loading}
                      className="flex items-center justify-between gap-3 rounded-2xl border border-indigo-500/20 bg-indigo-500/5 px-4 py-3.5 text-sm font-black text-indigo-100 transition-all hover:bg-indigo-500/10 hover:border-indigo-500/40 disabled:opacity-50 group"
                    >
                      <div className="flex items-center gap-3">
                        <Shield className="h-5 w-5 text-indigo-400" />
                        Company SSO
                      </div>
                      <ArrowRight className="h-4 w-4 opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" />
                    </button>
                  </div>
                </motion.div>
              )}

              {tab === "passwordless" && (
                <motion.div
                  key="passkey"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-6 py-4"
                >
                  <div className="flex flex-col items-center text-center">
                    <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-[1.25rem] bg-slate-900/70 text-slate-100 border border-slate-700/80">
                      <Fingerprint className="h-8 w-8" />
                    </div>
                    <h3 className="text-lg font-bold text-white mb-2">Fingerprint Login</h3>
                    <p className="text-xs text-slate-500 max-w-[240px]">
                      Use your device biometrics to sign in securely without a password.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-[11px] uppercase tracking-widest font-black text-slate-500 px-1">Email</label>
                      <input
                        type="email"
                        value={passkeyEmail}
                        onChange={(e) => setPasskeyEmail(e.target.value)}
                        placeholder="name@company.com"
                        className="w-full rounded-2xl border border-white/[0.06] bg-slate-900/50 py-3.5 px-4 text-sm text-white placeholder:text-slate-500 outline-none ring-1 ring-transparent transition-all focus:border-slate-500/60 focus:ring-slate-500/10 focus:bg-slate-900/80"
                      />
                    </div>

                    {passkeyStatus && (
                      <div className="rounded-2xl border border-slate-700/80 bg-slate-900/70 p-3 text-sm text-slate-200">
                        {passkeyStatus}
                      </div>
                    )}
                  </div>

                  <div className="grid gap-3">
                    <button
                      onClick={handlePasskeyRegister}
                      disabled={loading || !passkeyEmail}
                      className="w-full rounded-2xl bg-slate-700 py-3.5 text-sm font-black text-white transition-all hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Register fingerprint"}
                    </button>
                    <button
                      onClick={handlePasskeyLogin}
                      disabled={loading || !passkeyEmail}
                      className="w-full rounded-2xl border border-slate-700 bg-transparent py-3.5 text-sm font-bold text-slate-200 transition-all hover:border-slate-500 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Sign in with fingerprint"}
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {error && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4 text-xs font-bold text-rose-400 flex items-center gap-3"
              >
                <div className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse" />
                {error}
              </motion.div>
            )}
          </div>
        </div>

        {/* Footer Links */}
        <div className="mt-8 flex flex-col items-center gap-4 text-center">
          <p className="text-xs font-bold text-slate-600 tracking-wide uppercase">
            Not part of the elite?{' '}
            <Link href="/register" className="text-white hover:text-indigo-400 transition-colors">
              Request Access
            </Link>
          </p>
          <div className="flex items-center gap-6 text-[10px] font-black text-slate-700 tracking-[0.25em] uppercase">
            <Link href="/privacy-policy" className="hover:text-slate-400 transition-colors">Privacy</Link>
            <div className="h-1 w-1 rounded-full bg-slate-800" />
            <Link href="/terms-of-service" className="hover:text-slate-400 transition-colors">Terms</Link>
          </div>
        </div>
      </motion.div>
    </main>
  );
}
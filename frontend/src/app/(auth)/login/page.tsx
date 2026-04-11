"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { authClient } from "@/lib/auth-client";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mail, Lock, ArrowRight, Loader2, Fingerprint, Shield, KeyRound, Eye, EyeOff,
} from "lucide-react";
import { toast } from "@/components/ui/Toast";

type AuthTab = "credentials" | "passwordless" | "passkey";
type OAuthProvider = "google" | "github";

const TABS: { key: AuthTab; label: string; icon: React.ReactNode }[] = [
  { key: "credentials",  label: "Password",   icon: <Lock className="w-4 h-4" /> },
  { key: "passwordless", label: "Magic Link",  icon: <Mail className="w-4 h-4" /> },
  { key: "passkey",      label: "Passkey",     icon: <Fingerprint className="w-4 h-4" /> },
];

export default function LoginPage() {
  const router = useRouter();
  const [tab, setTab] = useState<AuthTab>("credentials");

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw]     = useState(false);

  const [magicEmail, setMagicEmail] = useState("");
  const [magicSent, setMagicSent]   = useState(false);

  const [loading, setLoading] = useState<string | null>(null);

  async function handleCredentialLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setLoading("credentials");
    try {
      const { error } = await authClient.signIn.email({
        email: email.trim(),
        password,
        callbackURL: "/auth-callback",
      });
      if (error) throw new Error(error.message ?? "Invalid credentials");
      router.replace("/dashboard");
    } catch (err) {
      toast.error((err as Error).message || "Sign-in failed. Please try again.");
    } finally {
      setLoading(null);
    }
  }

  async function handleOAuth(provider: OAuthProvider) {
    setLoading(provider);
    try {
      await authClient.signIn.social({ provider, callbackURL: "/dashboard" });
    } catch (err) {
      toast.error(`${provider} sign-in unavailable. Try another method.`);
      setLoading(null);
    }
  }

  async function handleMagicLink(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!magicEmail.trim()) return;
    setLoading("magic");
    try {
      const { error } = await authClient.signIn.magicLink({
        email: magicEmail.trim(),
        callbackURL: "/auth-callback",
      });
      if (error) throw error;
      setMagicSent(true);
      toast.success("Magic link sent! Check your inbox.");
    } catch (err) {
      toast.error((err as Error).message || "Failed to send magic link.");
    } finally {
      setLoading(null);
    }
  }

  async function handlePasskey() {
    setLoading("passkey");
    try {
      const { error } = await authClient.signIn.passkey({});
      if (error) throw new Error("Passkey authentication failed.");
      router.replace("/dashboard");
    } catch {
      toast.error("Passkey authentication failed or was cancelled.");
    } finally {
      setLoading(null);
    }
  }

  return (
    <main className="app-shell flex min-h-screen flex-col items-center justify-center p-4 bg-[var(--bg)]">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle,_rgba(255,171,145,0.08)_0%,_transparent_70%)]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="w-full max-w-[420px] z-10"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-4 font-bold text-xl bg-peach text-[#1A0F0A] shadow-[0_0_24px_rgba(255,171,145,0.18)]">
            G
          </div>
          <h1 className="text-2xl font-bold tracking-tight mb-1 text-white">
            Welcome back
          </h1>
          <p className="text-sm text-slate-400">
            Sign in to your GraftAI workspace
          </p>
        </div>

        <div className="card p-6 md:p-8">
          <div className="grid grid-cols-2 gap-3 mb-6">
            {(["google", "github"] as OAuthProvider[]).map((p) => (
              <OAuthButton
                key={p}
                provider={p}
                loading={loading === p}
                onClick={() => handleOAuth(p)}
              />
            ))}
          </div>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center">
              <span className="px-3 text-xs font-medium bg-[#0a0a14] text-slate-400">
                or continue with
              </span>
            </div>
          </div>

          <div className="flex rounded-xl p-1 mb-6 gap-1 bg-slate-800">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold transition-all ${tab === t.key ? 'bg-peach text-[#1A0F0A] shadow-[0_1px_6px_rgba(255,171,145,0.3)]' : 'text-slate-400'}`}
              >
                {t.icon}
                <span className="hidden sm:inline">{t.label}</span>
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {tab === "credentials" && (
              <motion.form
                key="creds"
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 8 }}
                transition={{ duration: 0.18 }}
                className="space-y-3"
                onSubmit={handleCredentialLogin}
              >
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none text-slate-400" />
                  <input
                    className="input pl-10"
                    type="email" autoComplete="email" required
                    placeholder="name@company.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                  />
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none text-slate-400" />
                  <input
                    className="input pl-10 pr-10"
                    type={showPw ? "text" : "password"}
                    autoComplete="current-password" required
                    placeholder="••••••••"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 min-h-0 min-w-0 p-0"
                    onClick={() => setShowPw(v => !v)}
                    tabIndex={-1}
                  >
                    {showPw
                      ? <EyeOff className="w-4 h-4 text-slate-400" />
                      : <Eye className="w-4 h-4 text-slate-400" />
                    }
                  </button>
                </div>
                <div className="flex justify-end">
                  <Link href="/forgot-password" className="text-xs min-h-0 min-w-0 font-medium hover:underline text-peach">
                    Forgot password?
                  </Link>
                </div>
                <PrimaryButton loading={loading === "credentials"} label="Sign In" />
              </motion.form>
            )}

            {tab === "passwordless" && (
              <motion.div
                key="magic"
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 8 }}
                transition={{ duration: 0.18 }}
              >
                {!magicSent ? (
                  <form className="space-y-3" onSubmit={handleMagicLink}>
                    <p className="text-xs mb-3 text-slate-400">
                      Enter your email and we'll send a one-click sign-in link — no password needed.
                    </p>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none text-slate-400" />
                      <input
                        className="input pl-10"
                        type="email" autoComplete="email" required
                        placeholder="name@company.com"
                        value={magicEmail}
                        onChange={e => setMagicEmail(e.target.value)}
                      />
                    </div>
                    <PrimaryButton loading={loading === "magic"} label="Send Magic Link" />
                  </form>
                ) : (
                  <motion.div
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="text-center py-8 space-y-3"
                  >
                    <div className="w-12 h-12 rounded-full flex items-center justify-center mx-auto bg-emerald-500/10 border border-emerald-500/20">
                      <Mail className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-sm text-emerald-400">Check your inbox</p>
                      <p className="text-xs mt-1 text-slate-400">
                        Magic link sent to <strong className="text-white">{magicEmail}</strong>
                      </p>
                    </div>
                    <button
                      type="button"
                      className="text-xs font-medium hover:underline min-h-0 min-w-0 text-slate-400 hover:text-white"
                      onClick={() => setMagicSent(false)}
                    >
                      Use a different email
                    </button>
                  </motion.div>
                )}
              </motion.div>
            )}

            {tab === "passkey" && (
              <motion.div
                key="passkey"
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 8 }}
                transition={{ duration: 0.18 }}
                className="text-center py-4 space-y-4"
              >
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto bg-slate-800 border border-white/10">
                  <Fingerprint className="w-8 h-8 text-peach" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">FIDO2 / WebAuthn</p>
                  <p className="text-xs mt-1 text-slate-400">
                    Use your device biometric or security key
                  </p>
                </div>
                <button
                  className="btn btn-primary w-full"
                  onClick={handlePasskey}
                  disabled={loading === "passkey"}
                >
                  {loading === "passkey"
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Waiting for device…</>
                    : <><Fingerprint className="w-4 h-4" /> Authenticate with Passkey</>
                  }
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="mt-6 flex flex-col items-center gap-2">
          <div className="flex items-center gap-4">
            <Link href="/sso" className="flex items-center gap-1 text-xs font-medium hover:underline min-h-0 min-w-0 text-slate-400">
              <Shield className="w-3 h-3" /> Enterprise SSO
            </Link>
            <Link href="/mfa" className="flex items-center gap-1 text-xs font-medium hover:underline min-h-0 min-w-0 text-slate-400">
              <KeyRound className="w-3 h-3" /> MFA Verification
            </Link>
          </div>
          <p className="text-sm mt-2 text-slate-400">
            No account? <Link href="/register" className="font-semibold hover:underline text-peach">Sign up free</Link>
          </p>
        </div>
      </motion.div>
    </main>
  );
}

function PrimaryButton({ loading, label }: { loading: boolean; label: string }) {
  return (
    <button type="submit" className="btn btn-primary w-full" disabled={loading}>
      {loading
        ? <><Loader2 className="w-4 h-4 animate-spin" /> Please wait…</>
        : <>{label} <ArrowRight className="w-4 h-4" /></>
      }
    </button>
  );
}

function OAuthButton({
  provider, loading, onClick,
}: { provider: "google" | "github"; loading: boolean; onClick: () => void }) {
  const icons: Record<string, React.ReactNode> = {
    google: (
      <svg className="w-4 h-4" viewBox="0 0 24 24">
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.70 23 12 23z" fill="#34A853"/>
        <path d="M5.84 14.09a7.12 7.12 0 010-4.18V7.07H2.18A11.99 11.99 0 001 12c0 1.94.46 3.77 1.18 5.43l3.66-2.84.81-.5z" fill="#FBBC05"/>
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.70 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.60 3.30-4.53 6.16-4.53z" fill="#EA4335"/>
      </svg>
    ),
    github: (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
        <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/>
      </svg>
    ),
  };
  const labels: Record<string, string> = { google: "Google", github: "GitHub" };

  return (
    <button
      type="button"
      className="btn btn-ghost"
      onClick={onClick}
      disabled={loading}
    >
      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : icons[provider]}
      {labels[provider]}
    </button>
  );
}

"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { signIn } from "@/lib/auth-client";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, Lock, ArrowRight, Loader2, KeyRound, Shield } from "lucide-react";

type AuthTab = "credentials" | "passwordless";
type OAuthProvider = "google" | "github" | "microsoft" | "apple";

export default function LoginPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<AuthTab>("credentials");

  // Credentials state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Passwordless state
  const [magicEmail, setMagicEmail] = useState("");
  const [magicSent, setMagicSent] = useState(false);

  // Shared state
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
      const { error } = await signIn.email({ email: normalizedEmail, password });

      if (error) {
        throw new Error(error.message || "Invalid credentials");
      }

      router.replace("/dashboard");
    } catch (err) {
      setError((err as Error).message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  }

  const handleOAuthLogin = async (provider: OAuthProvider) => {
    setLoading(true);
    setError("");

    try {
      await signIn.social({ provider });
      return;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      const msg = errorMessage.toLowerCase();
      if (msg.includes("network") || msg.includes("failed to fetch") || msg.includes("cors")) {
        setError("Unable to reach authentication service. Please try password login.");
      } else if (msg.includes("400") || msg.includes("bad request") || msg.includes("unauthorized")) {
        setError("Social login is temporarily unavailable. Use password login or try again.");
      } else {
        setError(errorMessage || "Failed to initiate social login");
      }
      setLoading(false);
    }
  };

  async function handleMagicRequest(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const normalizedEmail = magicEmail.trim().toLowerCase();
    if (!normalizedEmail) {
      setError("Please enter your email address.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const { error } = await signIn.magicLink({ email: normalizedEmail });
      if (error) throw error;
      setMagicSent(true);
    } catch (err) {
      setError((err as Error).message || "Failed to send magic link");
    } finally {
      setLoading(false);
    }
  }

  const tabs: { key: AuthTab; label: string; icon: React.ReactNode }[] = [
    { key: "credentials", label: "Password", icon: <Lock className="w-4 h-4" /> },
    { key: "passwordless", label: "Magic Link", icon: <Mail className="w-4 h-4" /> },
  ];

  return (
    <main className="app-shell flex min-h-screen flex-col items-center justify-start px-4 pb-10 relative overflow-hidden pt-12 md:pt-20">

      {/* Background Ambience */}
      <div className="hidden md:block absolute top-0 right-0 w-full h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="hidden md:block absolute bottom-1/4 left-1/4 w-[300px] h-[300px] bg-fuchsia-500/5 rounded-full blur-[100px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-[440px] z-10"
      >
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-6 md:mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-fuchsia-600 flex items-center justify-center shadow-[0_0_20px_rgba(79,70,229,0.3)] mb-4">
            <span className="text-white font-bold text-2xl leading-none">G</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-2">Welcome back</h1>
          <p className="text-slate-400 text-sm text-center">Simple and secure login for your GraftAI workspace</p>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl shadow-xl p-5 md:p-8">

          <div className="grid grid-cols-2 gap-3 mb-5">
            <button
              onClick={() => handleOAuthLogin("google")}
              disabled={loading}
              className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border border-slate-700/50 bg-slate-800/50 hover:bg-slate-700/60 text-sm font-medium text-slate-200 transition-colors group"
            >
              <svg className="w-4 h-4 opacity-70 group-hover:opacity-100 transition-opacity" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09a7.12 7.12 0 010-4.18V7.07H2.18A11.99 11.99 0 001 12c0 1.94.46 3.77 1.18 5.43l3.66-2.84.81-.5z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Google
            </button>
            <button
              onClick={() => handleOAuthLogin("github")}
              disabled={loading}
              className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border border-slate-700/50 bg-slate-800/50 hover:bg-slate-700/60 text-sm font-medium text-slate-200 transition-colors group"
            >
              <svg className="w-4 h-4 opacity-70 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/>
              </svg>
              GitHub
            </button>
            <button
              onClick={() => handleOAuthLogin("microsoft")}
              disabled={loading}
              className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border border-slate-700/50 bg-slate-800/50 hover:bg-slate-700/60 text-sm font-medium text-slate-200 transition-colors group"
            >
              <svg className="w-4 h-4 opacity-70 group-hover:opacity-100 transition-opacity" viewBox="0 0 23 23">
                <rect width="10.8" height="10.8" fill="#f25022" />
                <rect width="10.8" height="10.8" x="11.8" fill="#7fba00" />
                <rect width="10.8" height="10.8" y="11.8" fill="#00a1f1" />
                <rect width="10.8" height="10.8" x="11.8" y="11.8" fill="#ffb900" />
              </svg>
              Microsoft
            </button>
            <button
              onClick={() => handleOAuthLogin("apple")}
              disabled={loading}
              className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border border-slate-700/50 bg-slate-800/50 hover:bg-slate-700/60 text-sm font-medium text-slate-200 transition-colors group"
            >
              <svg className="w-4 h-4 opacity-70 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.06.75 1.21-.02 2.34-.84 3.75-.76 1.74.01 3.01.62 3.73 1.83-3.64 2.16-3.05 7.15.54 8.64-.72 1.82-1.65 3.51-3.08 4.51zM12.03 7.25c-.08-2.69 2.25-4.99 4.85-5.11.36 2.97-2.73 5.42-4.85 5.11z"/>
              </svg>
              Apple
            </button>
          </div>

          <div className="relative mb-5">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-800"></div></div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-slate-900 px-2 text-slate-500">Or choose a method</span>
            </div>
          </div>

          <div className="flex rounded-xl bg-slate-800/50 p-1 mb-5 gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => { setActiveTab(tab.key); setError(""); }}
                disabled={loading}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all ${
                  activeTab === tab.key
                    ? "bg-primary text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {tab.icon}
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            {activeTab === "credentials" && (
              <motion.form
                key="credentials"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ duration: 0.2 }}
                className="space-y-3"
                onSubmit={handleCredentialLogin}
              >
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-4 w-4 text-slate-500" />
                  </div>
                  <input
                    type="email" autoComplete="email" required value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full pl-10 pr-3 py-3 border border-slate-700/50 rounded-xl bg-slate-800/50 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-colors text-sm"
                    placeholder="name@company.com"
                  />
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-4 w-4 text-slate-500" />
                  </div>
                  <input
                    type="password" autoComplete="current-password" required value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full pl-10 pr-3 py-3 border border-slate-700/50 rounded-xl bg-slate-800/50 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-colors text-sm"
                    placeholder="••••••••"
                  />
                </div>
                <SubmitButton loading={loading} label="Sign In" />
              </motion.form>
            )}

            {activeTab === "passwordless" && (
              <motion.div
                key="passwordless"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ duration: 0.2 }}
              >
                {!magicSent ? (
                  <form className="space-y-3" onSubmit={handleMagicRequest}>
                    <p className="text-xs text-slate-400 mb-2">We will send a one-time sign-in link to your email.</p>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Mail className="h-4 w-4 text-slate-500" />
                      </div>
                      <input
                        type="email" autoComplete="email" required value={magicEmail}
                        onChange={(e) => setMagicEmail(e.target.value)}
                        className="block w-full pl-10 pr-3 py-3 border border-slate-700/50 rounded-xl bg-slate-800/50 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-colors text-sm"
                        placeholder="name@company.com"
                      />
                    </div>
                    <SubmitButton loading={loading} label="Send Magic Link" />
                  </form>
                ) : (
                  <div className="text-center py-6 space-y-4">
                    <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto">
                      <Mail className="w-6 h-6 text-emerald-500" />
                    </div>
                    <div>
                      <h3 className="text-emerald-400 font-medium mb-1">Check your email</h3>
                      <p className="text-xs text-slate-400">We have sent a magic link to {magicEmail}. Click the link to sign in instantly.</p>
                    </div>
                    <button type="button" onClick={() => setMagicSent(false)} className="text-xs text-slate-500 hover:text-slate-300 transition-colors">
                      Use a different email
                    </button>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {error && (
            <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mt-3 text-sm text-red-400 bg-red-400/10 border border-red-400/20 p-3 rounded-xl">
              {error}
            </motion.p>
          )}
        </div>

        <div className="mt-6 flex flex-col items-center gap-2">
          <Link href="/sso" className="text-xs text-slate-500 hover:text-primary transition-colors flex items-center gap-1">
            <Shield className="w-3 h-3" /> Enterprise SSO
          </Link>
          <Link href="/mfa" className="text-xs text-slate-500 hover:text-primary transition-colors flex items-center gap-1">
            <KeyRound className="w-3 h-3" /> MFA Verification
          </Link>
          <p className="mt-2 text-sm text-slate-500">
            Do you not have an account? <Link href="/register" className="font-medium text-primary hover:underline">Sign up</Link>
          </p>
        </div>
      </motion.div>
    </main>
  );
}

function SubmitButton({ loading, label }: { loading: boolean; label: string }) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl text-sm font-medium text-white bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
    >
      {loading ? (
        <><Loader2 className="w-4 h-4 animate-spin" /> Please wait...</>
      ) : (
        <>{label} <ArrowRight className="w-4 h-4" /></>
      )}
    </button>
  );
}

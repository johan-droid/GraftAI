"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Zap, Mail, Lock, Globe, ArrowRight } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://graftai.onrender.com";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);

  const redirectPath = useMemo(() => {
    const target = searchParams.get("redirect");
    if (!target || !target.startsWith("/")) {
      return "/dashboard";
    }
    return target;
  }, [searchParams]);

  useEffect(() => {
    if (searchParams.get("verified") === "true") {
      setInfo("Email verified successfully. You can sign in now.");
    } else if (searchParams.get("registered") === "true") {
      setInfo("Registration completed. Please sign in.");
    }
  }, [searchParams]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const response = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const detail = typeof payload.detail === "string" ? payload.detail : "Invalid credentials";
        throw new Error(detail);
      }

      const data = await response.json();
      localStorage.setItem("token", data.access_token);
      router.push(redirectPath);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070711] flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[20%] w-[600px] h-[600px] bg-indigo-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[10%] right-[10%] w-[400px] h-[400px] bg-violet-600/5 blur-[100px] rounded-full" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        {/* Logo */}
        <Link href="/" className="flex items-center justify-center gap-2 mb-8 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/25">
            <Zap className="w-6 h-6 text-white fill-white" />
          </div>
          <span className="text-xl font-black tracking-tight text-white uppercase">GraftAI</span>
        </Link>

        {/* Form Card */}
        <div className="rounded-3xl border border-white/10 bg-[#0a0a14]/80 backdrop-blur-xl p-8 shadow-2xl">
          <h2 className="text-2xl font-bold text-white mb-2">Welcome back</h2>
          <p className="text-slate-400 text-sm mb-8">Sign in to your account to continue</p>

          {info && !error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 rounded-xl border border-emerald-500/25 bg-emerald-500/10 p-3 text-sm font-medium text-emerald-200"
            >
              {info}
            </motion.div>
          )}
          
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 text-red-400 text-sm font-medium bg-red-500/10 border border-red-500/20 p-3 rounded-xl"
            >
              {error}
            </motion.div>
          )}
          
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium mb-2 text-slate-300">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                <input 
                  type="email" 
                  required
                  placeholder="you@example.com"
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                  value={email} 
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2 text-slate-300">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                <input 
                  type="password" 
                  required
                  placeholder="••••••••"
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                  value={password} 
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <p className="mt-2 text-xs text-slate-500">Use your verified account email and password.</p>
            </div>
            
            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-white text-black rounded-xl py-3 font-bold hover:bg-slate-200 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
            >
              {loading ? "Signing in..." : "Sign In"}
              {!loading && <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />}
            </button>

            <p className="text-center text-xs text-slate-500">
              Need an account? <Link href="/register" className="text-slate-300 hover:text-white underline underline-offset-2">Create one</Link>
            </p>
          </form>

          <div className="mt-6 relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-[#0a0a14] px-2 text-slate-500 font-bold">Or continue with</span>
            </div>
          </div>

          <div className="mt-6 grid gap-3">
            <button
              type="button"
              onClick={() => (window.location.href = `${API_URL}/api/v1/auth/google/login`)}
              className="w-full flex items-center justify-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-white hover:bg-white/10 transition"
            >
              <Globe className="h-5 w-5" />
              Continue with Google
            </button>
            <button
              type="button"
              onClick={() => (window.location.href = `${API_URL}/api/v1/auth/microsoft/login`)}
              className="w-full flex items-center justify-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-white hover:bg-white/10 transition"
            >
              <svg className="h-5 w-5" viewBox="0 0 23 23" fill="none">
                <path d="M0 0h11v11H0z" fill="#f25022"/>
                <path d="M12 0h11v11H12z" fill="#00a4ef"/>
                <path d="M0 12h11v11H0z" fill="#7fba00"/>
                <path d="M12 12h11v11H12z" fill="#ffb900"/>
              </svg>
              Continue with Microsoft
            </button>
          </div>

        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          Protected by enterprise-grade security · {" "}
          <Link href="/docs" className="text-slate-400 hover:text-slate-200 underline underline-offset-2">
            Docs
          </Link>
          {" "}· {" "}
          <Link href="/privacy-policy" className="text-slate-400 hover:text-slate-200 underline underline-offset-2">
            Privacy
          </Link>
          {" "}· {" "}
          <Link href="/terms-of-service" className="text-slate-400 hover:text-slate-200 underline underline-offset-2">
            Terms
          </Link>
        </p>
      </motion.div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <LoginContent />
    </React.Suspense>
  );
}
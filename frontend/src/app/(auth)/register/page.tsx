"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Zap, Mail, Lock, User, ArrowRight, Globe, ShieldCheck } from "lucide-react";
import { apiClient } from "@/lib/api-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://graftai.onrender.com";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [savedEmail, setSavedEmail] = useState("");
  const [step, setStep] = useState<"register" | "verify">("register");
  const [error, setError] = useState("");
  const [infoMessage, setInfoMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);

  const handleRegister = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setInfoMessage("");
    setLoading(true);

    try {
      const response = await apiClient.post<{ message: string; email: string }>(
        "/auth/register",
        {
          full_name: fullName,
          email,
          password,
        }
      );

      setSavedEmail(email);
      setStep("verify");
      setInfoMessage(response.message || "A verification code has been sent to your email.");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to register. Please try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setInfoMessage("");
    setLoading(true);

    try {
      await apiClient.post<{ message: string }>("/auth/verify-email", {
        email: savedEmail || email,
        code: verificationCode,
      });
      router.push("/login?verified=true");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to verify your email. Please try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError("");
    setInfoMessage("");
    setResendLoading(true);

    try {
      const response = await apiClient.post<{ message: string }>("/auth/resend-verification", {
        email: savedEmail || email,
      });
      setInfoMessage(response.message || "Verification code resent.");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to resend code. Please try again.";
      setError(message);
    } finally {
      setResendLoading(false);
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
          <div className="mb-6 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.14em]">
            <span className={`rounded-full px-2.5 py-1 ${step === "register" ? "bg-indigo-500/20 text-indigo-300" : "bg-slate-800 text-slate-400"}`}>
              1. Account
            </span>
            <span className="text-slate-600">→</span>
            <span className={`rounded-full px-2.5 py-1 ${step === "verify" ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-800 text-slate-400"}`}>
              2. Verify
            </span>
          </div>

          <h2 className="text-2xl font-bold text-white mb-2">
            {step === "register" ? "Create your account" : "Verify your email"}
          </h2>
          <p className="text-slate-400 text-sm mb-8">
            {step === "register"
              ? "Start managing your time intelligently"
              : "Enter the code we sent to complete your signup."}
          </p>
          
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 text-red-400 text-sm font-medium bg-red-500/10 border border-red-500/20 p-3 rounded-xl"
            >
              {error}
            </motion.div>
          )}

          {infoMessage && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 text-slate-100 text-sm font-medium bg-slate-800/70 border border-slate-700/80 p-3 rounded-xl"
            >
              {infoMessage}
            </motion.div>
          )}

          {step === "register" ? (
            <form onSubmit={handleRegister} className="space-y-5">
              <div>
                <label htmlFor="full-name" className="block text-sm font-medium mb-2 text-slate-300">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                  <input
                    id="full-name"
                    type="text"
                    required
                    placeholder="John Doe"
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium mb-2 text-slate-300">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                  <input
                    id="email"
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
                <label htmlFor="password" className="block text-sm font-medium mb-2 text-slate-300">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                  <input
                    id="password"
                    type="password"
                    required
                    minLength={6}
                    placeholder="At least 6 characters"
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
                <p className="mt-2 text-xs text-slate-500">Use at least 6 characters. Longer passphrases are recommended.</p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-white text-black rounded-xl py-3 font-bold hover:bg-slate-200 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
              >
                {loading ? "Creating account..." : "Create Account"}
                {!loading && <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />}
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerify} className="space-y-5">
              <div>
                <label htmlFor="verify-email" className="block text-sm font-medium mb-2 text-slate-300">Email Address</label>
                <input
                  id="verify-email"
                  type="email"
                  value={savedEmail || email}
                  readOnly
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                />
              </div>

              <div>
                <label htmlFor="verification-code" className="block text-sm font-medium mb-2 text-slate-300">Verification Code</label>
                <div className="relative">
                  <ShieldCheck className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                  <input
                    id="verification-code"
                    type="text"
                    required
                    inputMode="numeric"
                    maxLength={6}
                    placeholder="Enter OTP code"
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value)}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || verificationCode.trim().length < 6}
                className="w-full bg-white text-black rounded-xl py-3 font-bold hover:bg-slate-200 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
              >
                {loading ? "Verifying..." : "Verify Email"}
                {!loading && <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />}
              </button>

              <button
                type="button"
                disabled={resendLoading}
                onClick={handleResend}
                className="w-full bg-white/5 text-white border border-white/10 rounded-xl py-3 font-semibold hover:bg-white/10 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {resendLoading ? "Resending code..." : "Resend verification code"}
              </button>

              <button
                type="button"
                onClick={() => setStep("register")}
                className="w-full rounded-xl border border-white/10 bg-transparent py-3 text-sm font-semibold text-slate-300 transition hover:bg-white/5 hover:text-white"
              >
                Back to account details
              </button>
            </form>
          )}

          {step === "register" ? (
            <>
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
            </>
          ) : null}

          <div className="mt-6 text-center text-sm text-slate-400">
            Already have an account?{" "}
            <Link href="/login" className="text-indigo-400 font-semibold hover:text-indigo-300 transition">
              Sign in
            </Link>
          </div>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          By creating an account, you agree to our {" "}
          <Link href="/terms-of-service" className="text-slate-400 hover:text-slate-200 underline underline-offset-2">
            Terms of Service
          </Link>
          {" "}and {" "}
          <Link href="/privacy-policy" className="text-slate-400 hover:text-slate-200 underline underline-offset-2">
            Privacy Policy
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
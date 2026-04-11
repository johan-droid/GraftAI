"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Zap } from "lucide-react";
import { BACKEND_API_URL } from "../../../lib/backend";

export default function RegisterPage() {
  const router = useRouter();

  const getBackendUrl = (provider: "google" | "microsoft") => {
    if (process.env.NODE_ENV === "production") {
      // Always use production backend in production
      return `https://graftai.onrender.com/api/v1/auth/${provider}/login`;
    }
    // Use local backend in development
    return `${BACKEND_API_URL}/auth/${provider}/login`;
  };

  const handleOAuthLogin = (provider: "google" | "microsoft") => {
    window.location.href = getBackendUrl(provider);
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
        <div className="rounded-3xl border border-white/10 bg-[#0a0a14]/80 backdrop-blur-xl p-8 shadow-2xl text-center">
          <h2 className="text-2xl font-bold text-white mb-2">
            Registration is SSO Only
          </h2>
          <p className="text-slate-400 text-sm mb-8">
            For security reasons, we only support sign-up via Google or Microsoft.
            Please use one of these providers to create your account.
          </p>

          <div className="grid grid-cols-1 gap-4 mb-6">
            <button
              type="button"
              onClick={() => handleOAuthLogin("google")}
              className="w-full flex items-center justify-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-4 text-sm font-semibold text-white hover:bg-white/10 transition"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.70 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09a7.12 7.12 0 010-4.18V7.07H2.18A11.99 11.99 0 001 12c0 1.94.46 3.77 1.18 5.43l3.66-2.84.81-.5z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.70 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.60 3.30-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>
            <button
              type="button"
              onClick={() => handleOAuthLogin("microsoft")}
              className="w-full flex items-center justify-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-4 text-sm font-semibold text-white hover:bg-white/10 transition"
            >
              <svg className="w-5 h-5" viewBox="0 0 23 23">
                <path d="M0 0h11v11H0z" fill="#f25022"/>
                <path d="M12 0h11v11H12z" fill="#00a4ef"/>
                <path d="M0 12h11v11H0z" fill="#7fba00"/>
                <path d="M12 12h11v11H12z" fill="#ffb900"/>
              </svg>
              Continue with Microsoft
            </button>
          </div>

          <div className="mt-6 text-center text-sm text-slate-400">
            Already have an account?{" "}
            <Link href="/login" className="text-indigo-400 font-semibold hover:text-indigo-300 transition">
              Sign in
            </Link>
          </div>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          By signing in, you agree to our {" "}
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
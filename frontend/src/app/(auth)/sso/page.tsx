"use client";

import { useState } from "react";
import { signIn } from "@/lib/auth-client";
import { motion } from "framer-motion";
import { ArrowRight, Loader2, Shield } from "lucide-react";

export default function SSOPage() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const redirectTo = typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("next") || "/dashboard" : "/dashboard";

  const startSSO = async () => {
    setLoading(true);
    setError("");
    try {
      const { error } = await signIn.sso({
        callbackURL: redirectTo,
      });
      if (error) {
        throw new Error(error.message || "Unable to start SSO flow");
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app-shell flex min-h-screen flex-col items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-full h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-[420px] z-10"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-fuchsia-600 flex items-center justify-center shadow-[0_0_20px_rgba(79,70,229,0.3)] mb-4">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-2">Enterprise SSO</h1>
          <p className="text-slate-400 text-sm text-center">Continue with your corporate identity provider</p>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl shadow-xl p-6 md:p-8">
          <button
            onClick={startSSO}
            disabled={loading}
            className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl text-sm font-medium text-white bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? (
              <><Loader2 className="w-5 h-5 animate-spin" /> Connecting...</>
            ) : (
              <>Start SSO <ArrowRight className="w-4 h-4" /></>
            )}
          </button>

          {error && (
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4 text-sm text-red-400 bg-red-400/10 border border-red-400/20 p-3 rounded-xl">
              {error}
            </motion.p>
          )}

          <p className="mt-6 text-center text-xs text-slate-500">
            Your company IT admin must configure SSO before you can use this.
          </p>
        </div>

        <p className="mt-8 text-center text-sm text-slate-500">
          <a href="/login" className="font-medium text-primary hover:underline">← Back to login</a>
        </p>
      </motion.div>
    </main>
  );
}

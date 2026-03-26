"use client";

import { useState } from "react";
import { mfaVerify } from "@/lib/api";
import { useAuthContext } from "@/app/providers/auth-provider";
import { motion } from "framer-motion";
import { KeyRound, Loader2, ArrowRight } from "lucide-react";

type AuthUser = { id?: number } | null;

export default function MfaPage() {
  const { user } = useAuthContext();
  const authUser = user as AuthUser;
  const [code, setCode] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const verify = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setStatus("");
    try {
      await mfaVerify(authUser?.id ?? 1, code);
      setStatus("MFA verified successfully!");
      setSuccess(true);
    } catch (err) {
      setStatus((err as Error).message);
      setSuccess(false);
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
            <KeyRound className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-2">MFA Verification</h1>
          <p className="text-slate-400 text-sm text-center">Enter the 6-digit code from your authenticator app</p>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl shadow-xl p-6 md:p-8">
          <form className="space-y-4" onSubmit={verify}>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <KeyRound className="h-5 w-5 text-slate-500" />
              </div>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="block w-full pl-10 px-3 py-3 border border-slate-700/50 rounded-xl leading-5 bg-slate-800/50 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-colors sm:text-sm text-center text-2xl tracking-[0.5em] font-mono"
                placeholder="000000"
                required
              />
            </div>

            {status && (
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className={`text-sm p-3 rounded-xl flex items-center gap-2 ${success ? "text-emerald-400 bg-emerald-400/10 border border-emerald-400/20" : "text-red-400 bg-red-400/10 border border-red-400/20"}`}>
                {status}
              </motion.p>
            )}

            <button
              type="submit"
              disabled={loading || code.length < 6}
              className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl text-sm font-medium text-white bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? (
                <><Loader2 className="w-5 h-5 animate-spin" /> Verifying...</>
              ) : (
                <>Verify <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>
        </div>

        <p className="mt-8 text-center text-sm text-slate-500">
          <a href="/login" className="font-medium text-primary hover:underline">← Back to login</a>
        </p>
      </motion.div>
    </main>
  );
}

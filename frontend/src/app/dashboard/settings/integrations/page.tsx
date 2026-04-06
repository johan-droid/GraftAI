"use client";

import { motion } from "framer-motion";
import { 
  ShieldCheck, 
  Puzzle,
  Sparkles
} from "lucide-react";

export default function IntegrationsPage() {

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  return (
    <div className="p-5 md:p-8 max-w-[900px] mx-auto">
      <motion.div 
        variants={containerVariants} 
        initial="hidden" 
        animate="visible"
        className="space-y-6"
      >
      <header className="mb-8">
        <h1 className="text-2xl md:text-3xl font-black text-white mb-2 bg-gradient-to-r from-white to-slate-500 bg-clip-text">
          Integrations Unified
        </h1>
        <p className="text-sm text-slate-400 font-medium opacity-90">
          GraftAI has moved all workspace connections to the Plugin Marketplace for a unified experience.
        </p>
      </header>

      <div className="p-8 rounded-2xl border border-indigo-500/20 bg-indigo-500/5 text-center space-y-4">
        <Puzzle className="w-12 h-12 text-indigo-400 mx-auto mb-2" />
        <h2 className="text-xl font-bold text-white">We&apos;ve moved!</h2>
        <p className="text-sm text-slate-400 max-w-md mx-auto">
          Manage your Google Workspace, Microsoft 365, and other connections directly from the Plugin Marketplace.
        </p>
        <button 
          onClick={() => window.location.assign("/dashboard/plugins")}
          className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-bold transition-all shadow-lg shadow-indigo-600/20"
        >
          Go to Plugin Marketplace
        </button>
      </div>

      <div className="mt-12 p-6 rounded-2xl bg-primary/5 border border-primary/10 flex items-start gap-4">
        <ShieldCheck className="w-6 h-6 text-primary shrink-0" />
        <div>
          <h4 className="text-sm font-bold text-white mb-1 flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            Security & Data Sovereignty
          </h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            GraftAI utilizes scoped OAuth 2.0 signatures to interact with your services. Your credentials never leave the provider&apos;s secure enclave, and all session tokens are rotated automatically.
          </p>
        </div>
      </div>
      </motion.div>
    </div>
  );
}

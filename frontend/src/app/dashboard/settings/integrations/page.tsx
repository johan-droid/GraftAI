"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { composeEndpoint } from "@/lib/api-client";
import { getIntegrationStatus } from "@/lib/api";
import { 
  ShieldCheck, 
  ExternalLink,
  Loader2,
  Puzzle,
  LayoutGrid,
  Sparkles
} from "lucide-react";

// Integration Providers Metadata
const PROVIDERS = [
  {
    id: "google",
    name: "Google Workspace",
    description: "Two-way sync for calendars and automated meeting link creation.",
    color: "from-blue-500/10 to-red-500/10",
    iconColor: "text-red-400",
    scopes: ["Calendar", "Meetings"]
  },
  {
    id: "microsoft",
    name: "Microsoft 365",
    description: "Two-way sync for calendars and automated meeting link creation.",
    color: "from-blue-600/10 to-cyan-500/10",
    iconColor: "text-blue-400",
    scopes: ["Calendar", "Meetings"]
  }
];

export default function IntegrationsPage() {
  const [connections, setConnections] = useState<Record<string, boolean>>({});
  const [availableProviders, setAvailableProviders] = useState<Record<string, boolean>>({
    google: false,
    microsoft: false,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    fetch("/api/auth/providers", { credentials: "include" })
      .then(async (res) => {
        const data = (await res.json().catch(() => ({}))) as { providers?: string[] };
        const providers = Array.isArray(data.providers) ? data.providers : [];
        if (!alive) return;
        setAvailableProviders({
          google: providers.includes("google"),
          microsoft: providers.includes("microsoft"),
        });
      })
      .catch(() => {
        if (!alive) return;
        setAvailableProviders({ google: false, microsoft: false });
      });

    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);

    getIntegrationStatus()
      .then((data) => {
        if (!alive) return;
        setConnections({
          google: Boolean(data.connections?.google),
          microsoft: Boolean(data.connections?.microsoft),
        });
      })
      .catch((err) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Failed to load integrations");
        setConnections({ google: false, microsoft: false });
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  const handleConnect = (providerId: string) => {
    if (!availableProviders[providerId]) {
      setError(`${providerId} SSO is not configured right now.`);
      return;
    }

    const currentPath = typeof window !== "undefined" ? window.location.pathname : "";
    const callbackPath = currentPath || "/dashboard/settings/integrations";
    const base = composeEndpoint("/auth/sso/start", true);
    const url = `${base}?provider=${encodeURIComponent(providerId)}&redirect_to=${encodeURIComponent(callbackPath)}`;
    window.location.assign(url);
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
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

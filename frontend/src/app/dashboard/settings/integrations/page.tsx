"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { composeEndpoint } from "@/lib/api-client";
import { getIntegrationStatus } from "@/lib/api";
import { 
  ShieldCheck, 
  Video,
  Calendar, 
  ExternalLink,
  CheckCircle2,
  Loader2,
  Sparkles
} from "lucide-react";

// Integration Providers Metadata
const PROVIDERS = [
  {
    id: "google",
    name: "Google Workspace",
    description: "Sync your Google Calendar and create Google Meet links automatically.",
    color: "from-blue-500/10 to-red-500/10",
    iconColor: "text-red-400",
    scopes: ["Calendar", "Meet"]
  },
  {
    id: "microsoft",
    name: "Microsoft 365",
    description: "Connect Outlook Calendar and generate Microsoft Teams meeting links.",
    color: "from-blue-600/10 to-cyan-500/10",
    iconColor: "text-blue-400",
    scopes: ["Outlook", "Teams"]
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
    <motion.div 
      variants={containerVariants} 
      initial="hidden" 
      animate="visible"
      className="space-y-6"
    >
      <header className="mb-8">
        <h1 className="text-2xl md:text-3xl font-black text-white mb-2 bg-gradient-to-r from-white to-slate-500 bg-clip-text">
          SaaS Integrations
        </h1>
        <p className="text-sm text-slate-400 font-medium opacity-80">
          Connect your ecosystem to activate autonomous scheduling.
        </p>
      </header>

      {error && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-[10px] uppercase tracking-widest font-black text-slate-600">Verifying Encrypted Links</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {PROVIDERS.map((provider) => (
            <motion.div 
              key={provider.id} 
              variants={itemVariants}
              className="group relative bg-slate-950/40 backdrop-blur-xl border border-slate-800/60 rounded-2xl p-6 overflow-hidden transition-all hover:border-primary/40"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${provider.color} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
              
              <div className="relative z-10 flex flex-col h-full">
                <div className="flex justify-between items-start mb-6">
                  <div className={`p-3 bg-slate-900 rounded-xl border border-slate-800 ${provider.iconColor}`}>
                    {provider.id === 'google' && <Video className="w-6 h-6" />}
                    {provider.id === 'microsoft' && <Calendar className="w-6 h-6" />}
                  </div>
                  {connections[provider.id] ? (
                    <span className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase">
                      <CheckCircle2 className="w-3 h-3" /> Active
                    </span>
                  ) : (
                    <span className="px-2 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-500 text-[10px] font-black uppercase">
                      Offline
                    </span>
                  )}
                </div>

                <h3 className="text-lg font-bold text-white mb-2">{provider.name}</h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-6 flex-grow">
                  {provider.description}
                </p>

                <div className="flex flex-wrap gap-2 mb-6">
                  {provider.scopes.map(scope => (
                    <span key={scope} className="text-[9px] px-2 py-0.5 rounded-full bg-slate-900/50 text-slate-500 border border-slate-800 font-bold uppercase tracking-tighter">
                      {scope}
                    </span>
                  ))}
                </div>

                <button 
                  onClick={() => handleConnect(provider.id)}
                  disabled={!availableProviders[provider.id]}
                  className={`w-full py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all active:scale-95 flex items-center justify-center gap-2 ${
                    !availableProviders[provider.id]
                      ? "bg-slate-900/70 text-slate-500 border border-slate-800 cursor-not-allowed"
                      : connections[provider.id]
                      ? "bg-slate-900 text-white border border-slate-800 hover:bg-slate-800"
                      : "bg-primary text-white shadow-lg shadow-primary/20 hover:bg-primary/90"
                  }`}
                >
                  {!availableProviders[provider.id]
                    ? "Unavailable"
                    : connections[provider.id]
                    ? "Manage Link"
                    : "Connect Account"}
                  {availableProviders[provider.id] && !connections[provider.id] && <ExternalLink className="w-3.5 h-3.5" />}
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}

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
  );
}

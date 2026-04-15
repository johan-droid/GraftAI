"use client";

import { useEffect, useState, type ReactNode } from "react";
import { apiClient } from "@/lib/api-client";
import { motion } from "framer-motion";
import { Globe, Sparkles, Video, AlertCircle, CheckCircle2, Trash2, ArrowRight } from "lucide-react";

export default function IntegrationsPage() {
  const [integrationStatus, setIntegrationStatus] = useState<{ active_providers: string[]; inactive_providers: string[] }>({
    active_providers: [],
    inactive_providers: [],
  });
  const [loading, setLoading] = useState(true);

  const fetchIntegrations = async () => {
    try {
      const data = await apiClient.fetch<{ active_providers: string[]; inactive_providers: string[] }>("/users/me/integrations");
      setIntegrationStatus({
        active_providers: data.active_providers || [],
        inactive_providers: data.inactive_providers || [],
      });
    } catch (fetchError) {
      console.error("Failed to fetch integrations", fetchError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const handleConnect = (provider: string) => {
    const redirectTo = "/dashboard/settings/integrations";
    window.location.assign(`/api/auth/social/${provider}?redirect_to=${encodeURIComponent(redirectTo)}`);
  };

  const handleDisconnect = async (provider: string) => {
    if (!confirm(`This will stop GraftAI from syncing with your ${provider} account. Proceed?`)) return;
    
    try {
      await apiClient.fetch(`/users/me/integrations/${provider}`, { method: "DELETE" });
      setIntegrationStatus((current) => ({
        ...current,
        active_providers: current.active_providers.filter(p => p !== provider),
      }));
      alert(`${provider} disconnected successfully.`);
    } catch {
      alert(`Failed to disconnect ${provider}. Please try again later.`);
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center py-20 bg-gray-50/30">
        <div className="w-8 h-8 border-4 border-gray-200 border-t-indigo-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto min-h-screen">
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10"
      >
        <h1 className="text-4xl font-black text-gray-900 tracking-tight">Connected Ecosystems</h1>
        <p className="text-gray-500 mt-2 font-medium">Link your primary calendar platforms to allow GraftAI to unify your schedule.</p>
      </motion.div>

      <div className="grid gap-6">
        {/* Google Workspace */}
        <IntegrationCard
          id="google"
          name="Google Workspace"
          desc={integrationStatus.inactive_providers.includes("google") ? "Reconnect expired Google access to resume sync." : "Sync events and Google Meet links seamlessly."}
          icon={<Globe className="w-8 h-8" />}
          accentColor="text-red-500"
          bgColor="bg-red-50/50"
          borderColor="border-red-100"
          status={integrationStatus.active_providers.includes("google") ? "active" : integrationStatus.inactive_providers.includes("google") ? "reconnect" : "disconnected"}
          onConnect={() => handleConnect("google")}
          onDisconnect={() => handleDisconnect("google")}
        />

        {/* Microsoft 365 */}
        <IntegrationCard
          id="microsoft"
          name="Microsoft 365"
          desc={integrationStatus.inactive_providers.includes("microsoft") ? "Reconnect expired Microsoft access to resume sync." : "Synchronize Outlook events and Teams coordination."}
          icon={<Sparkles className="w-8 h-8" />}
          accentColor="text-blue-500"
          bgColor="bg-blue-50/50"
          borderColor="border-blue-100"
          status={integrationStatus.active_providers.includes("microsoft") ? "active" : integrationStatus.inactive_providers.includes("microsoft") ? "reconnect" : "disconnected"}
          onConnect={() => handleConnect("microsoft")}
          onDisconnect={() => handleDisconnect("microsoft")}
        />

        {/* Zoom */}
        <IntegrationCard
          id="zoom"
          name="Zoom"
          desc={integrationStatus.inactive_providers.includes("zoom") ? "Reconnect expired Zoom access to resume meeting creation." : "Generate and sync Zoom meetings from your calendar."}
          icon={<Video className="w-8 h-8" />}
          accentColor="text-purple-500"
          bgColor="bg-purple-50/50"
          borderColor="border-purple-100"
          status={integrationStatus.active_providers.includes("zoom") ? "active" : integrationStatus.inactive_providers.includes("zoom") ? "reconnect" : "disconnected"}
          onConnect={() => handleConnect("zoom")}
          onDisconnect={() => handleDisconnect("zoom")}
        />
      </div>

      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="mt-12 p-6 rounded-3xl bg-indigo-50/30 border border-indigo-100 flex items-start gap-4"
      >
        <AlertCircle className="w-5 h-5 text-indigo-500 mt-1" />
        <div>
          <h4 className="font-bold text-indigo-900 text-sm italic">Privacy Note</h4>
          <p className="text-indigo-700/70 text-xs mt-1 leading-relaxed">
            GraftAI uses industry-standard OAuth2 scopes to fetch only your calendar availability. 
            We do not store your credentials, and you can revoke access at any time.
          </p>
        </div>
      </motion.div>
    </div>
  );
}

interface IntegrationCardProps {
  id?: string;
  name: string;
  desc: string;
  icon: ReactNode;
  accentColor: string;
  bgColor: string;
  borderColor: string;
  status?: "active" | "reconnect" | "disconnected";
  onConnect: () => void;
  onDisconnect: () => void;
}

function IntegrationCard({ name, desc, icon, accentColor, bgColor, borderColor, status = "disconnected", onConnect, onDisconnect }: IntegrationCardProps) {
  const isConnected = status === "active";
  const needsReconnect = status === "reconnect";

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      whileHover={{ y: -2 }}
      className={`relative group p-8 rounded-[32px] border ${borderColor} ${bgColor} flex flex-col md:flex-row items-center justify-between gap-6 transition-all shadow-sm hover:shadow-xl hover:shadow-gray-200/50`}
    >
      <div className="flex items-center gap-6 text-center md:text-left flex-col md:flex-row">
        <div className={`p-5 rounded-2xl bg-white border border-gray-100 shadow-sm ${accentColor}`}>
          {icon}
        </div>
        <div>
          <div className="flex items-center gap-2 justify-center md:justify-start">
            <h3 className="font-black text-xl text-gray-900 uppercase tracking-tight">{name}</h3>
            {isConnected && (
              <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-[10px] font-black uppercase tracking-widest">
                <CheckCircle2 className="w-3 h-3" />
                Active
              </span>
            )}
            {needsReconnect && (
              <span className="flex items-center gap-1.5 px-3 py-1 bg-yellow-100 text-amber-700 rounded-full text-[10px] font-black uppercase tracking-widest">
                Reconnect
              </span>
            )}
          </div>
          <p className="text-gray-500 text-sm mt-1 font-medium">{desc}</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {isConnected ? (
          <button
            onClick={onDisconnect}
            className="flex items-center gap-2 px-6 py-3 rounded-2xl border border-red-200 text-red-600 bg-white font-bold text-xs uppercase tracking-widest hover:bg-red-50 transition-all active:scale-95"
          >
            <Trash2 className="w-4 h-4" />
            Disconnect
          </button>
        ) : (
          <button
            onClick={onConnect}
            className="flex items-center gap-2 px-8 py-3 rounded-2xl bg-indigo-600 text-white font-bold text-xs uppercase tracking-widest shadow-lg shadow-indigo-500/20 hover:bg-indigo-700 transition-all active:scale-95"
          >
            {needsReconnect ? "Reconnect" : "Connect Account"}
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </motion.div>
  );
}

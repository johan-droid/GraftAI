"use client";

import { useState } from "react";
import { Calendar, Video, CreditCard, Webhook, Check, Plus } from "lucide-react";
import { toast } from "@/components/ui/Toast";

const INTEGRATIONS = [
  {
    id: "google_calendar",
    name: "Google Calendar",
    description: "Check for conflicts and add events to your Google Calendar.",
    icon: Calendar,
    color: "text-[#1A73E8]",
    bg: "bg-[#E8F0FE]",
    status: "connected",
    account: "user@example.com"
  },
  {
    id: "ms_outlook",
    name: "Microsoft Outlook",
    description: "Connect your Outlook calendar for real-time availability.",
    icon: Calendar,
    color: "text-[#0078D4]",
    bg: "bg-[#E6F2FA]",
    status: "disconnected"
  },
  {
    id: "zoom",
    name: "Zoom",
    description: "Automatically generate Zoom meeting links for your events.",
    icon: Video,
    color: "text-[#2D8CFF]",
    bg: "bg-[#EAF3FF]",
    status: "connected",
    account: "Zoom Pro Account"
  },
  {
    id: "stripe",
    name: "Stripe",
    description: "Accept payments directly when clients book an appointment.",
    icon: CreditCard,
    color: "text-[#635BFF]",
    bg: "bg-[#EFEFFF]",
    status: "disconnected"
  },
  {
    id: "webhooks",
    name: "Custom Webhooks",
    description: "Send real-time booking data to your external systems.",
    icon: Webhook,
    color: "text-[#5F6368]",
    bg: "bg-[#F1F3F4]",
    status: "disconnected"
  }
];

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState(INTEGRATIONS);

  const toggleConnection = (id: string, currentStatus: string) => {
    if (currentStatus === "connected") {
      toast.success("Integration disconnected.");
      setIntegrations((prev) => prev.map(i => i.id === id ? { ...i, status: "disconnected", account: undefined } : i));
    } else {
      toast.success("Redirecting to OAuth provider...");
      setTimeout(() => {
        setIntegrations((prev) => prev.map(i => i.id === id ? { ...i, status: "connected", account: "new_auth@example.com" } : i));
      }, 1000);
    }
  };

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto w-full">
      <div className="mb-8 pb-6 border-b border-[#DADCE0]">
        <h1 className="text-3xl font-medium text-[#202124] tracking-tight mb-2">
          Integrations
        </h1>
        <p className="text-[#5F6368] text-base max-w-2xl">
          Connect GraftAI with your favorite tools to sync calendars, generate video links, and automate your scheduling workflow.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {integrations.map((app) => (
          <div key={app.id} className="flex flex-col bg-white border border-[#DADCE0] rounded-2xl p-6 hover:shadow-md transition-all">
            <div className="flex items-start justify-between mb-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${app.bg} ${app.color}`}>
                <app.icon size={24} />
              </div>
              {app.status === "connected" && (
                <span className="flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-[#137333] bg-[#E6F4EA] px-2.5 py-1 rounded-full">
                  <Check size={12} strokeWidth={3} /> Active
                </span>
              )}
            </div>
            
            <h3 className="text-lg font-semibold text-[#202124] mb-2">{app.name}</h3>
            <p className="text-sm text-[#5F6368] mb-6 flex-1">{app.description}</p>
            
            {app.status === "connected" ? (
              <div className="pt-4 border-t border-[#F1F3F4] flex items-center justify-between mt-auto">
                <span className="text-xs font-medium text-[#5F6368] truncate pr-4">
                  {app.account}
                </span>
                <button 
                  onClick={() => toggleConnection(app.id, app.status)}
                  className="text-sm font-medium text-[#D93025] hover:bg-[#FCE8E6] px-3 py-1.5 rounded-full transition-colors"
                >
                  Disconnect
                </button>
              </div>
            ) : (
              <div className="pt-4 border-t border-[#F1F3F4] mt-auto">
                <button 
                  onClick={() => toggleConnection(app.id, app.status)}
                  className="w-full flex items-center justify-center gap-2 text-sm font-medium bg-white border border-[#DADCE0] text-[#1A73E8] hover:bg-[#F8F9FA] px-4 py-2 rounded-full transition-colors"
                >
                  <Plus size={16} />
                  Connect {app.name}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

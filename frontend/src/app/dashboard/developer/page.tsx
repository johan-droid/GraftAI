"use client";

import { motion } from "framer-motion";
import { 
  Terminal, 
  Cpu, 
  Database, 
  Activity, 
  Shield, 
  Zap, 
  Globe, 
  Code2,
  Lock,
  Search,
  BookOpen,
  Server
} from "lucide-react";

const SYSTEM_METRICS = [
  { label: "Kernel_Uptime", value: "99.98%", status: "OPTIMAL" },
  { label: "API_Latency", value: "14ms", status: "STABLE" },
  { label: "Vector_Load", value: "2.4 GB", status: "FLOWING" },
  { label: "Auth_Packets", value: "14.2k/hr", status: "SECURE" },
];

const API_PROTOCOLS = [
  { method: "GET", path: "/api/v1/auth/check", detail: "Session validation & user context" },
  { method: "POST", path: "/api/v1/calendar/sync", detail: "Trigger heuristic sync engine" },
  { method: "GET", path: "/api/v1/ai/memory", detail: "Retrieve semantic focus vectors" },
  { method: "WS", path: "/api/v1/monitoring/ws", detail: "Real-time system telemetry stream" },
];

export default function DeveloperCorner() {
  return (
    <div className="space-y-8 pb-12 font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-dashed border-[var(--border-subtle)]">
        <div>
          <h1 className="text-4xl font-black text-[var(--text-primary)] uppercase tracking-tighter">Developer_Corner</h1>
          <p className="text-xs mt-2 uppercase tracking-[0.2em] text-[var(--text-muted)]">
            // [NODE_STATUS: ROOT_ACCESS_GRANTED] // SYSTEM_DOCUMENTATION_HUB
          </p>
        </div>
        <div className="flex gap-2">
           <div className="px-4 py-2 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[10px] font-black uppercase text-[var(--primary)]">
              Build: v3.0.4-production
           </div>
        </div>
      </div>

      {/* Real-time Telemetry Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {SYSTEM_METRICS.map((metric, i) => (
          <motion.div 
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-5 bg-[var(--bg-base)] border border-dashed border-[var(--border-subtle)] hover:border-[var(--primary)] transition-all group"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] font-black uppercase tracking-widest text-[var(--text-faint)] group-hover:text-[var(--text-secondary)]">
                {metric.label}
              </span>
              <Activity className="h-3 w-3 text-[var(--primary)]" />
            </div>
            <div className="text-2xl font-black text-[var(--text-primary)] mb-1">
              {metric.value}
            </div>
            <div className="text-[9px] font-bold text-[var(--primary)] flex items-center gap-1">
              <div className="w-1 h-1 bg-[var(--primary)] rounded-full animate-pulse" />
              {metric.status}
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* API Protocols */}
        <div className="lg:col-span-12">
          <div className="bg-[var(--bg-elevated)] border border-dashed border-[var(--border-subtle)] p-6">
            <div className="flex items-center gap-3 mb-6">
              <Server className="h-5 w-5 text-[var(--secondary)]" />
              <h2 className="text-sm font-black uppercase tracking-widest text-[var(--text-primary)]">Kernel_Endpoints</h2>
            </div>
            <div className="space-y-4">
              {API_PROTOCOLS.map((api, i) => (
                <div key={i} className="flex flex-col sm:flex-row sm:items-center gap-4 p-4 border border-[var(--border-subtle)] bg-[var(--bg-base)] hover:border-[var(--secondary)] transition-all">
                  <span className={`text-[10px] font-black px-2 py-1 ${
                    api.method === 'GET' ? 'bg-blue-500/10 text-blue-400' :
                    api.method === 'POST' ? 'bg-green-500/10 text-green-400' :
                    'bg-purple-500/10 text-purple-400'
                  }`}>
                    {api.method}
                  </span>
                  <code className="text-[11px] font-bold text-[var(--text-primary)] flex-1">{api.path}</code>
                  <span className="text-[10px] text-[var(--text-muted)] italic">// {api.detail}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Database & Security */}
        <div className="lg:col-span-6">
          <div className="bg-[var(--bg-elevated)] border border-dashed border-[var(--border-subtle)] p-6 h-full">
             <div className="flex items-center gap-3 mb-6">
              <Database className="h-5 w-5 text-[var(--primary)]" />
              <h2 className="text-sm font-black uppercase tracking-widest text-[var(--text-primary)]">System_Persistence</h2>
            </div>
            <div className="p-4 border border-[var(--border-subtle)] bg-[var(--bg-base)] text-[11px] space-y-3 leading-relaxed text-[var(--text-muted)] font-bold">
               <div className="flex justify-between">
                  <span>POSTGRESQL_DB</span>
                  <span className="text-[var(--primary)]">ACTIVE</span>
               </div>
               <div className="flex justify-between">
                  <span>REDIS_CACHE</span>
                  <span className="text-[var(--primary)]">ACTIVE</span>
               </div>
               <div className="flex justify-between">
                  <span>VECTOR_STORE</span>
                  <span className="text-[var(--secondary)]">SYNCING...</span>
               </div>
               <div className="pt-4 border-t border-[var(--border-subtle)] mt-4">
                  <p className="italic">// All persistent nodes are secured via AES-256 standard and strictly isolated within the GraftAI virtual network.</p>
               </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-6">
          <div className="bg-[var(--bg-elevated)] border border-dashed border-[var(--border-subtle)] p-6 h-full">
             <div className="flex items-center gap-3 mb-6">
              <Shield className="h-5 w-5 text-[var(--accent)]" />
              <h2 className="text-sm font-black uppercase tracking-widest text-[var(--text-primary)]">Security_Mesh</h2>
            </div>
            <div className="p-4 border border-[var(--border-subtle)] bg-[var(--bg-base)] text-[11px] space-y-3 leading-relaxed text-[var(--text-muted)] font-bold">
               <div className="flex items-center gap-2">
                  <Lock className="h-3 w-3 text-[var(--accent)]" />
                  <span>E2E_ENCRYPTION_LAYER_v2</span>
               </div>
               <div className="flex items-center gap-2">
                  <Lock className="h-3 w-3 text-[var(--accent)]" />
                  <span>SESSION_INTEGRITY_AUDIT</span>
               </div>
               <div className="flex items-center gap-2">
                  <Lock className="h-3 w-3 text-[var(--accent)]" />
                  <span>SCOPE_GRADED_API_ACCESS</span>
               </div>
               <div className="pt-4 border-t border-[var(--border-subtle)] mt-4">
                  <p className="italic">// Continuous security scans monitor the execution cortex for zero-day vulnerabilities or unauthorized node attempts.</p>
               </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="p-6 border border-dashed border-[var(--border-subtle)] bg-[var(--bg-base)]">
        <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-[var(--text-muted)] mb-4">Internal_Knowledge_Nodes</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
           {[
             { label: "Git_History", icon: Code2 },
             { label: "Style_Guide", icon: BookOpen },
             { label: "Logic_Flow", icon: Zap },
             { label: "Audit_Logs", icon: Search },
           ].map((link, i) => (
             <button key={i} className="flex items-center gap-3 p-4 border border-[var(--border-subtle)] hover:bg-[var(--bg-hover)] hover:border-[var(--primary)] transition-all">
                <link.icon className="h-4 w-4 text-[var(--primary)]" />
                <span className="text-[11px] font-black uppercase tracking-widest text-[var(--text-secondary)]">{link.label}</span>
             </button>
           ))}
        </div>
      </div>
    </div>
  );
}

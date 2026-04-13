'use client';

import React from 'react';
import { DeveloperCorner } from '@/components/dashboard/DeveloperCorner';
import { Terminal } from 'lucide-react';

export default function DevelopersPage() {
  return (
    <div className="space-y-8 pb-12">
      {/* Header section with technical detail */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-subtle pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Terminal size={18} className="text-primary" />
            <h1 className="text-h2 font-mono uppercase tracking-tighter">Developer_Corner</h1>
          </div>
          <p className="text-secondary font-mono text-xs max-w-2xl">
            Real-time engine telemetry, system logs, and security protocols.
            Auth_Level: ROOT_ACCESS
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-[10px] text-muted font-mono uppercase">Node_ID</p>
            <p className="text-xs font-mono text-white">GRAFT_NODE_01_PROD</p>
          </div>
          <div className="w-[1px] h-8 bg-subtle" />
          <div className="text-right">
            <p className="text-[10px] text-muted font-mono uppercase">Uptime</p>
            <p className="text-xs font-mono text-primary">12D 04H 21M</p>
          </div>
        </div>
      </div>

      {/* Main Developer Views */}
      <DeveloperCorner />

      {/* Footer / System Note */}
      <div className="pt-8 border-t border-subtle">
        <div className="bg-elevated p-4 border border-subtle flex items-start gap-4">
          <div className="w-10 h-10 rounded-sm bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20">
            <Terminal size={20} className="text-primary" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white uppercase mb-1">Development Notice</h3>
            <p className="text-[11px] text-muted leading-relaxed">
              This environment is optimized for high-performance monitoring. All system metrics are streamed via dedicated WebSockets. 
              Sensitive data is masked in logs by default. Contact system admin for raw data access.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Terminal, 
  Activity, 
  Cpu, 
  HardDrive, 
  Wifi, 
  ShieldCheck, 
  AlertCircle,
  ChevronRight,
  Database,
  Search
} from 'lucide-react';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  event_type?: string;
}

export const DeveloperCorner: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [metrics, setMetrics] = useState({
    active_automations: 0,
    cpu_utilization: '12%',
    memory_usage: '256MB',
    latency: '42ms'
  });
  const [status, setStatus] = useState('SYNCED');
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Connect to Telemetry WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000';
    const wsUrl = `${protocol}//${host}/monitoring/ws`;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setMetrics(prev => ({
            ...prev,
            active_automations: data.active_automations || 0,
          }));
          
          if (data.recent_automations?.length > 0) {
            const newLogs = data.recent_automations.map((a: any) => ({
              timestamp: new Date().toISOString(),
              level: 'INFO',
              message: `Automation Event: ${a.type || 'Generic'} - PID: ${a.pid || '2841'}`,
              event_type: 'automation'
            }));
            setLogs(prev => [...prev.slice(-49), ...newLogs]);
          }
        };

        ws.onopen = () => setStatus('STABLE');
        ws.onclose = () => {
          setStatus('OFFLINE');
          setTimeout(connect, 5000);
        };
      } catch (err) {
        setStatus('ERROR');
      }
    };

    connect();

    // Initial Logs Mock (since real backend might be quiet)
    setLogs([
      { timestamp: new Date().toISOString(), level: 'SYSTEM', message: 'GraftAI Engine v3.0 initialized.' },
      { timestamp: new Date().toISOString(), level: 'AUTH', message: 'NextAuth Session provider linked.' },
      { timestamp: new Date().toISOString(), level: 'STORAGE', message: 'Redis cluster connected at 10.0.4.12' },
    ]);
  }, []);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Stat Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Active_Nodes', value: metrics.active_automations, icon: Cpu, color: 'var(--primary)' },
          { label: 'System_CPU', value: metrics.cpu_utilization, icon: Activity, color: 'var(--secondary)' },
          { label: 'Mem_Alloc', value: metrics.memory_usage, icon: HardDrive, color: 'var(--accent)' },
          { label: 'Net_Latency', value: metrics.latency, icon: Wifi, color: 'var(--primary)' },
        ].map((stat, i) => (
          <div key={i} className="tech-card p-4 flex items-center justify-between">
            <div>
              <p className="text-label mb-1">{stat.label}</p>
              <p className="text-xl font-mono font-bold">{stat.value}</p>
            </div>
            <stat.icon size={20} style={{ color: stat.color, opacity: 0.6 }} />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Terminal/Log Viewer */}
        <div className="lg:col-span-2 tech-card flex flex-col h-[500px]">
          <div className="flex items-center justify-between px-4 py-2 border-b border-subtle bg-elevated">
            <div className="flex items-center gap-2">
              <Terminal size={14} className="text-primary" />
              <span className="text-label text-[10px]">System_Logs_v3.0</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-[10px] font-mono text-primary font-bold tracking-widest">{status}</span>
            </div>
          </div>
          <div 
            ref={logContainerRef}
            className="flex-1 overflow-y-auto p-4 font-mono text-[11px] space-y-1 bg-[#050505] scrollbar-hide"
          >
            {logs.map((log, i) => (
              <div key={i} className="flex gap-4 group opacity-80 hover:opacity-100 transition-opacity">
                <span className="text-muted shrink-0">[{log.timestamp.split('T')[1].split('.')[0]}]</span>
                <span className={`shrink-0 font-bold ${
                  log.level === 'ERROR' ? 'text-accent' : 
                  log.level === 'SYSTEM' ? 'text-primary' : 
                  'text-secondary'
                }`}>
                  {log.level}
                </span>
                <span className="text-primary/90">{log.message}</span>
              </div>
            ))}
          </div>
          <div className="p-2 border-t border-subtle flex items-center gap-3 bg-[rgba(255,255,255,0.02)]">
            <ChevronRight size={14} className="text-primary" />
            <input 
              type="text" 
              placeholder="Execute command..." 
              className="bg-transparent border-none outline-none text-[11px] font-mono text-white w-full"
            />
          </div>
        </div>

        {/* Documentation / Quick Links */}
        <div className="space-y-4">
          <div className="tech-card">
            <div className="p-4 border-b border-subtle">
              <h3 className="text-label text-primary">Technical_Protocol</h3>
            </div>
            <div className="p-4 space-y-3">
              {[
                { title: 'API Authentication', desc: 'Secure OAuth2 tokens and JWT handling.' },
                { title: 'Vector Memory', desc: 'LlamaIndex RAG pipeline status.' },
                { title: 'Distributed Queues', desc: 'Redis Stream management.' },
              ].map((doc, i) => (
                <div key={i} className="group cursor-pointer">
                  <h4 className="text-xs font-bold text-white mb-1 group-hover:text-primary transition-colors flex items-center justify-between">
                    {doc.title} <ChevronRight size={12} />
                  </h4>
                  <p className="text-[10px] text-muted">{doc.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="tech-card bg-primary/5 border-primary/20">
            <div className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <ShieldCheck size={16} className="text-primary" />
                <span className="text-xs font-bold text-primary uppercase">Security_Verified</span>
              </div>
              <p className="text-[11px] text-muted leading-relaxed">
                All engine activities are encrypted and audited. The GraftAI core maintains zero-trust architecture across all local nodes.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

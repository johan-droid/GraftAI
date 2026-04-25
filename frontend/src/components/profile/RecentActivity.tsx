import React, { useEffect, useState } from 'react';
import { getAuditLogs } from '@/lib/api';
import { motion } from 'framer-motion';
import { Clock, Shield, Zap, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';

export const RecentActivity: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const data = await getAuditLogs();
        setLogs(data);
      } catch (err) {
        console.error("Failed to fetch audit logs", err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const getIcon = (category: string) => {
    switch (category) {
      case 'ai': return <Zap className="w-3.5 h-3.5 text-indigo-400" />;
      case 'billing': return <Shield className="w-3.5 h-3.5 text-emerald-400" />;
      case 'security': return <Shield className="w-3.5 h-3.5 text-red-400" />;
      default: return <Clock className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  const getStatusIcon = (status: string) => {
    if (status === 'success') return <CheckCircle2 className="w-3 h-3 text-emerald-500" />;
    if (status === 'denied') return <AlertCircle className="w-3 h-3 text-amber-500" />;
    return <XCircle className="w-3 h-3 text-red-500" />;
  };

  if (loading) return <div className="p-8 text-center text-slate-500 text-xs animate-pulse">Retrieving secure logs...</div>;

  return (
    <div className="space-y-1">
      {logs.length === 0 ? (
        <div className="p-8 text-center text-slate-600 text-xs italic">No recent activity detected.</div>
      ) : (
        logs.slice(0, 10).map((log, i) => (
          <div key={log.id} className="group flex items-center justify-between p-3 rounded-xl hover:bg-white/[0.03] transition-colors border border-transparent hover:border-white/[0.05]">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-white/[0.03] flex items-center justify-center shrink-0">
                {getIcon(log.event_category)}
              </div>
              <div className="min-w-0">
                <p className="text-[13px] font-medium text-slate-200 truncate capitalize">
                  {log.action.replace(/\./g, ' ')}
                </p>
                <p className="text-[10px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                  {new Date(log.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                  <span className="w-1 h-1 rounded-full bg-slate-700" />
                  {log.event_category.toUpperCase()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0">
               <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-white/[0.03] border border-white/[0.05]">
                 {getStatusIcon(log.status)}
                 <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">{log.status}</span>
               </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
};

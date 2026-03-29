"use client";

import Link from "next/link";
import { Cpu, ShieldCheck } from "lucide-react";

export default function Footer() {
  return (
    <footer className="w-full py-12 px-6 border-t border-white/5 bg-[#0A0E27]">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand Column */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 rounded-lg bg-[#0066FF] flex items-center justify-center">
                <Cpu className="text-white w-4 h-4" />
              </div>
              <span className="text-lg font-bold tracking-tight text-white">GraftAI</span>
            </Link>
            <p className="text-sm text-slate-500 leading-relaxed max-w-xs">
              Autonomous orchestration for modern teams. Secure, low-latency, and reliable.
            </p>
          </div>

          {/* Links Columns */}
          <div>
            <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-6">Platform</h4>
            <ul className="space-y-4">
              <li><Link href="#features" className="text-sm text-slate-500 hover:text-white transition-colors">Features</Link></li>
              <li><Link href="#pricing" className="text-sm text-slate-500 hover:text-white transition-colors">Pricing</Link></li>
              <li><Link href="/dashboard" className="text-sm text-slate-500 hover:text-white transition-colors">Dashboard</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-6">Company</h4>
            <ul className="space-y-4">
              <li><Link href="/about" className="text-sm text-slate-500 hover:text-white transition-colors">About</Link></li>
              <li><Link href="/blog" className="text-sm text-slate-500 hover:text-white transition-colors">Blog</Link></li>
              <li><Link href="/careers" className="text-sm text-slate-500 hover:text-white transition-colors">Careers</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-6">Support</h4>
            <ul className="space-y-4">
              <li><Link href="/docs" className="text-sm text-slate-500 hover:text-white transition-colors">Documentation</Link></li>
              <li><Link href="/help" className="text-sm text-slate-500 hover:text-white transition-colors">Help Center</Link></li>
              <li><Link href="/status" className="text-sm text-slate-500 hover:text-white transition-colors">Status</Link></li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-white/5 flex flex-col md:row justify-between items-center gap-6">
          <p className="text-[10px] font-medium text-slate-600 uppercase tracking-[0.2em]">
            © 2026 GRAFT AI SYSTEMS. ALL RIGHTS RESERVED.
          </p>
          
          <div className="flex items-center gap-8">
            <Link href="/privacy" className="text-[10px] font-bold text-slate-500 hover:text-white uppercase tracking-widest transition-colors">Privacy</Link>
            <Link href="/terms" className="text-[10px] font-bold text-slate-500 hover:text-white uppercase tracking-widest transition-colors">Terms</Link>
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-700 uppercase">
              <ShieldCheck className="w-3 h-3" />
              AES-256
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

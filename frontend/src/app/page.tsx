"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Calendar, Clock, ShieldCheck, Sparkles, Users } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F8F9FA] text-[#202124] font-sans selection:bg-[#D2E3FC]">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-[#F8F9FA]/80 backdrop-blur-md border-b border-[#DADCE0]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-[#1A73E8] flex items-center justify-center text-white font-bold text-xs">
              G
            </div>
            <span className="text-lg font-medium tracking-tight text-[#202124]">
              GraftAI
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-[#5F6368]">
            <Link href="#features" className="hover:text-[#202124] transition-colors">Features</Link>
            <Link href="/pricing" className="hover:text-[#202124] transition-colors">Pricing</Link>
            <Link href="/docs" className="hover:text-[#202124] transition-colors">Documentation</Link>
          </div>
          <div className="flex items-center gap-3">
            <Link 
              href="/login" 
              className="hidden sm:inline-flex text-sm font-medium text-[#1A73E8] hover:bg-[#E8F0FE] px-4 py-2 rounded-full transition-colors"
            >
              Sign in
            </Link>
            <Link 
              href="/signup" 
              className="inline-flex items-center gap-1.5 text-sm font-medium bg-[#1A73E8] text-white hover:bg-[#1557B0] px-5 py-2 rounded-full transition-colors shadow-sm"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 pt-24 pb-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#E8F0FE] text-[#1967D2] text-xs font-medium mb-6">
            <Sparkles size={14} />
            <span>Now in public beta</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-normal text-[#202124] tracking-tight leading-[1.15] mb-6">
            Scheduling, simplified by AI.
          </h1>
          <p className="text-base md:text-lg text-[#5F6368] max-w-2xl mx-auto leading-relaxed mb-10">
            GraftAI coordinates your meetings, manages your calendar routing, and handles the back-and-forth—so your team can focus on the work that actually matters.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link 
              href="/signup" 
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 text-base font-medium bg-[#1A73E8] text-white hover:bg-[#1557B0] px-7 py-3 rounded-full transition-colors shadow-sm"
            >
              Start for free
              <ArrowRight size={18} />
            </Link>
            <Link 
              href="/docs" 
              className="w-full sm:w-auto inline-flex items-center justify-center text-base font-medium text-[#5F6368] bg-white border border-[#DADCE0] hover:bg-[#F8F9FA] px-7 py-3 rounded-full transition-colors"
            >
              Read the docs
            </Link>
          </div>
        </motion.div>
      </main>

      {/* Features Grid */}
      <section id="features" className="bg-white border-t border-[#DADCE0] py-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-2xl md:text-3xl font-normal text-[#202124] tracking-tight mb-4">
              Everything you need to manage time
            </h2>
            <p className="text-sm md:text-base text-[#5F6368] max-w-xl mx-auto">
              A complete toolkit designed to eliminate scheduling friction without overcomplicating your workflow.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: Calendar,
                title: "Smart Calendar Sync",
                description: "Integrates instantly with Google Workspace and Microsoft 365 to prevent double-bookings.",
                color: "text-blue-600",
                bg: "bg-blue-50"
              },
              {
                icon: Users,
                title: "Team Routing",
                description: "Automatically distribute meetings across your team based on availability and logic rules.",
                color: "text-green-600",
                bg: "bg-green-50"
              },
              {
                icon: Clock,
                title: "Time Zone Intelligence",
                description: "Never calculate time differences again. We handle complex cross-continent scheduling seamlessly.",
                color: "text-orange-600",
                bg: "bg-orange-50"
              },
            ].map((feature, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="p-6 rounded-2xl border border-[#DADCE0] bg-white hover:shadow-md transition-shadow"
              >
                <div className={`w-12 h-12 rounded-xl ${feature.bg} ${feature.color} flex items-center justify-center mb-5`}>
                  <feature.icon size={24} />
                </div>
                <h3 className="text-lg font-medium text-[#202124] mb-2">{feature.title}</h3>
                <p className="text-sm text-[#5F6368] leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#F8F9FA] border-t border-[#DADCE0] py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-[#5F6368]">
            <div className="w-5 h-5 rounded bg-[#DADCE0] flex items-center justify-center text-white font-bold text-[10px]">
              G
            </div>
            <span className="text-xs font-medium">© {new Date().getFullYear()} GraftAI. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-6 text-xs font-medium text-[#5F6368]">
            <Link href="/terms" className="hover:text-[#202124] transition-colors">Terms</Link>
            <Link href="/privacy" className="hover:text-[#202124] transition-colors">Privacy Policy</Link>
            <div className="flex items-center gap-1">
              <ShieldCheck size={14} />
              <span>SOC2 Compliant</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

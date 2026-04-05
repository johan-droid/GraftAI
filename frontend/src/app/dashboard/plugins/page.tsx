"use client";

import { useState, useEffect } from "react";
import { listPlugins } from "@/lib/api";
import { motion } from "framer-motion";
import { Puzzle, Package, Loader2, Search, Check, ArrowUpRight, Zap } from "lucide-react";

interface Plugin {
  name: string;
  description: string;
  version: string;
  author?: string;
}

const STAGGER = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const ITEM = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0 },
};

const MOCK_FEATURED = [
  { name: "Zoom", desc: "Auto-generate meeting links for every booking", icon: "📹", installed: true, category: "Video" },
  { name: "Google Calendar", desc: "Two-way sync with your Google calendar", icon: "📅", installed: false, category: "Calendar" },
  { name: "Stripe", desc: "Accept payments for premium meetings", icon: "💳", installed: false, category: "Payments" },
  { name: "Slack", desc: "Get booking notifications in Slack channels", icon: "💬", installed: true, category: "Notifications" },
  { name: "Notion", desc: "Create meeting notes automatically in Notion", icon: "📝", installed: false, category: "Productivity" },
  { name: "HubSpot", desc: "Sync contacts and deals with CRM", icon: "🔶", installed: false, category: "CRM" },
];

const CATEGORIES = ["All", "Calendar", "Video", "Payments", "Notifications", "Productivity", "CRM"];

export default function PluginsPage() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");

  useEffect(() => {
    listPlugins()
      .then((d) => setPlugins(d.plugins))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const allPlugins = [
    ...MOCK_FEATURED,
    ...plugins.map((p) => ({ name: p.name, desc: p.description, icon: "🔌", installed: false, category: "Custom" })),
  ];

  const filtered = allPlugins.filter((p) => {
    const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) || p.desc.toLowerCase().includes(search.toLowerCase());
    const matchCat = activeCategory === "All" || p.category === activeCategory;
    return matchSearch && matchCat;
  });

  return (
    <div className="p-5 md:p-7 max-w-[1200px] mx-auto">
      <motion.div variants={STAGGER} initial="hidden" animate="visible" className="space-y-6">

        {/* Header */}
        <motion.div variants={ITEM} className="flex flex-col md:flex-row md:items-start gap-4">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-white tracking-tight">Plugin Marketplace</h1>
            <p className="text-slate-500 text-sm mt-0.5">Extend GraftAI with third-party integrations</p>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600" />
            <input
              type="text"
              placeholder="Search plugins…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500/50 w-full md:w-60 transition-colors"
            />
          </div>
        </motion.div>

        {/* Category filters */}
        <motion.div variants={ITEM} className="flex gap-2 flex-wrap">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-[12px] font-semibold transition-all border ${
                activeCategory === cat
                  ? "bg-indigo-600 border-indigo-500 text-white"
                  : "bg-white/5 border-white/10 text-slate-400 hover:text-white hover:bg-white/8"
              }`}
            >
              {cat}
            </button>
          ))}
        </motion.div>

        {/* AI Recommendation Banner */}
        <motion.div variants={ITEM} className="p-4 rounded-xl border border-indigo-500/20 bg-indigo-500/5 flex items-center gap-4">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center shrink-0">
            <Zap className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-white">AI Recommendation</p>
            <p className="text-xs text-slate-400 mt-0.5">
              Based on your usage, <span className="text-indigo-300 font-semibold">Google Calendar sync</span> would save you ~45 mins/week
            </p>
          </div>
          <button className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shrink-0">
            Install
          </button>
        </motion.div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-7 h-7 animate-spin text-indigo-400" />
          </div>
        ) : filtered.length > 0 ? (
          <motion.div variants={STAGGER} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((plugin, i) => (
              <motion.div
                key={`${plugin.name}-${i}`}
                variants={ITEM}
                className="group relative rounded-xl border border-white/[0.07] bg-white/[0.025] hover:border-white/12 hover:bg-white/[0.04] p-5 transition-all"
              >
                {plugin.installed && (
                  <div className="absolute top-4 right-4 flex items-center gap-1 text-[10px] font-bold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-1.5 py-0.5 rounded-full">
                    <Check className="w-3 h-3" /> Installed
                  </div>
                )}

                <div className="flex items-start gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-xl shrink-0">
                    {plugin.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-bold text-white">{plugin.name}</h3>
                    <span className="text-[10px] font-semibold text-slate-600 uppercase tracking-wide">{plugin.category}</span>
                  </div>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed mb-4">{plugin.desc}</p>
                {plugin.author && <p className="text-xs text-slate-500 mb-4">by {plugin.author}</p>}

                <div className="flex items-center gap-2">
                  <button
                    className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                      plugin.installed
                        ? "bg-white/5 border-white/10 text-slate-400 hover:text-white hover:bg-white/8"
                        : "bg-indigo-600/80 border-indigo-500/50 text-white hover:bg-indigo-600"
                    }`}
                  >
                    {plugin.installed ? "Manage" : "Install"}
                  </button>
                  <button className="p-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-500 hover:text-slate-300 transition-all" aria-label="View details">
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <motion.div variants={ITEM} className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-16 text-center">
            <Package className="w-10 h-10 text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">
              {search ? "No matching plugins" : "No plugins yet"}
            </h3>
            <p className="text-sm text-slate-400">
              {search ? "Try a different search term" : "Check back soon for new integrations and extensions"}
            </p>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}

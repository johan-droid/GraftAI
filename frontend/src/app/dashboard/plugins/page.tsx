"use client";

import { useState, useEffect } from "react";
import { listPlugins } from "@/lib/api";
import { motion } from "framer-motion";
import { Puzzle, Package, Loader2, Search } from "lucide-react";

interface Plugin {
  name: string;
  description: string;
  version: string;
  author?: string;
}

export default function PluginsPage() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    listPlugins()
      .then((data) => setPlugins(data.plugins))
      .catch((err) => console.error("Failed to load plugins:", err))
      .finally(() => setLoading(false));
  }, []);

  const filtered = plugins.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()) || p.description.toLowerCase().includes(search.toLowerCase())
  );

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
  };
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="space-y-6">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Plugins</h1>
          <p className="text-slate-400">Browse and manage your integrations</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search plugins..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-4 py-2.5 bg-slate-900/50 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 w-full md:w-64 transition-colors"
          />
        </div>
      </header>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((plugin) => (
            <motion.div
              key={plugin.name}
              variants={itemVariants}
              className="bg-slate-950/50 border border-slate-800 rounded-2xl p-6 hover:border-primary/30 transition-colors group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-xl bg-slate-800 text-primary group-hover:bg-primary/10 transition-colors">
                  <Puzzle className="w-5 h-5" />
                </div>
                <span className="text-xs font-mono text-slate-500 bg-slate-900 px-2 py-1 rounded-md">
                  v{plugin.version}
                </span>
              </div>
              <h3 className="text-base font-semibold text-white mb-1">{plugin.name}</h3>
              <p className="text-sm text-slate-400 mb-4 line-clamp-2">{plugin.description}</p>
              {plugin.author && (
                <p className="text-xs text-slate-500">by {plugin.author}</p>
              )}
            </motion.div>
          ))}
        </div>
      ) : (
        <motion.div variants={itemVariants} className="bg-slate-950/50 border border-slate-800 rounded-2xl p-12 text-center">
          <Package className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">
            {search ? "No plugins match your search" : "No plugins available yet"}
          </h3>
          <p className="text-sm text-slate-400">
            {search ? "Try a different search term" : "Check back later for new integrations and extensions"}
          </p>
        </motion.div>
      )}
    </motion.div>
  );
}

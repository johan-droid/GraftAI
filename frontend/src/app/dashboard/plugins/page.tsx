"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Puzzle, Package, Search, ExternalLink, Check, Loader2 } from "lucide-react";
import { useQuery, useDebounce } from "@/hooks/useQuery";
import { PluginCardSkeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { toast } from "@/components/ui/Toast";

interface Plugin {
  name: string;
  description: string;
  version: string;
  author?: string;
  category?: string;
  enabled?: boolean;
  website?: string;
}

export default function PluginsPage() {
  const [search, setSearch]       = useState("");
  const [installed, setInstalled] = useState<Set<string>>(new Set());
  const [installing, setInstalling] = useState<string | null>(null);
  const debouncedSearch            = useDebounce(search, 250);

  const { data, isLoading, error } = useQuery<{ plugins: Plugin[] }>("/api/plugins");

  const plugins   = data?.plugins ?? [];
  const filtered  = plugins.filter(
    p =>
      p.name.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
      p.description.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
      (p.category ?? "").toLowerCase().includes(debouncedSearch.toLowerCase())
  );

  async function handleInstall(plugin: Plugin) {
    setInstalling(plugin.name);
    try {
      const res = await fetch(`/api/plugins/${encodeURIComponent(plugin.name)}/enable`, { method: "POST", credentials: "include" });
      if (!res.ok) {
        const errText = await res.text();
        toast.error(errText || `Failed to install ${plugin.name}.`);
        return;
      }
      setInstalled(prev => new Set([...prev, plugin.name]));
      toast.success(`${plugin.name} installed successfully.`);
    } catch {
      toast.error(`Network error installing ${plugin.name}.`);
    } finally {
      setInstalling(null);
    }
  }

  const item = { hidden: { opacity: 0, y: 14 }, show: { opacity: 1, y: 0 } };
  const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };

  return (
    <ErrorBoundary>
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">

        <motion.div variants={item} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-h1 text-white">Plugins</h1>
            <p className="text-sm mt-1 text-slate-400">
              Browse and manage your integrations
            </p>
          </div>

          <div className="relative self-start sm:self-auto w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
              style={{ color: "var(--text-faint)" }} />
            <input
              className="input pl-9 w-full"
              type="search"
              placeholder="Search plugins…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </motion.div>

        {error && (
          <motion.div variants={item}
            className="p-4 rounded-xl text-sm"
            style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)", color: "var(--error)" }}>
            Failed to load plugins. {error.message}
          </motion.div>
        )}

        {!isLoading && plugins.length > 0 && (
          <motion.div variants={item} className="flex items-center gap-4 text-sm text-slate-400">
            <span>{plugins.length} available</span>
            <span className="text-white/30">·</span>
            <span className="text-amber-200">{installed.size} installed</span>
            {debouncedSearch && (
              <>
                <span className="text-white/30">·</span>
                <span>{filtered.length} results for "{debouncedSearch}"</span>
              </>
            )}
          </motion.div>
        )}

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => <PluginCardSkeleton key={i} />)}
          </div>
        ) : filtered.length > 0 ? (
          <motion.div
            variants={container}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {filtered.map((plugin) => {
              const isInstalled = installed.has(plugin.name) || plugin.enabled;
              const isBeingInstalled = installing === plugin.name;

              return (
                <motion.div
                  key={plugin.name}
                  variants={item}
                  className="card p-5 flex flex-col gap-4 group transition-all"
                  whileHover={{ translateY: -2 }}
                  transition={{ duration: 0.15 }}
                >
                  <div className="flex items-start justify-between">
                    <div className={`w-11 h-11 rounded-xl flex items-center justify-center transition-colors ${isInstalled ? "bg-white/10" : "bg-slate-800"}`}>
                      <Puzzle className={`w-5 h-5 ${isInstalled ? "text-amber-200" : "text-slate-500"}`} />
                    </div>
                    <div className="flex items-center gap-2">
                      {plugin.category && (
                        <span className="badge badge-muted text-[10px]">{plugin.category}</span>
                      )}
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-500">
                        v{plugin.version}
                      </span>
                    </div>
                  </div>

                  <div className="flex-1">
                    <h3 className="text-sm font-semibold mb-1 text-white">{plugin.name}</h3>
                    <p className="text-xs leading-relaxed line-clamp-2 text-slate-400">
                      {plugin.description}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-white/10">
                    <span className="text-[11px] text-slate-500">
                      {plugin.author ? `by ${plugin.author}` : "GraftAI"}
                    </span>
                    <div className="flex items-center gap-2">
                      {plugin.website && (
                        <a href={plugin.website} target="_blank" rel="noopener noreferrer"
                          className="p-1.5 rounded-lg transition-colors min-h-0 min-w-0 text-slate-400 hover:text-white"
                          aria-label={`Open ${plugin.name} website`}>
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span className="sr-only">Open website</span>
                        </a>
                      )}
                      <button
                        className={`btn text-xs py-1.5 px-3 min-h-0 ${isInstalled ? "btn-ghost" : "btn-primary"}`}
                        onClick={() => !isInstalled && handleInstall(plugin)}
                        disabled={isBeingInstalled || !!isInstalled}
                      >
                        {isBeingInstalled
                          ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          : isInstalled
                          ? <><Check className="w-3.5 h-3.5" /> Installed</>
                          : "Install"
                        }
                      </button>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        ) : (
          <EmptyState
            icon={Package}
            title={debouncedSearch ? "No plugins match your search" : "No plugins available yet"}
            description={
              debouncedSearch
                ? "Try a different search term or browse all plugins."
                : "New integrations are added regularly. Check back soon."
            }
            action={
              debouncedSearch ? (
                <button className="btn btn-ghost text-sm" onClick={() => setSearch("")}>
                  Clear search
                </button>
              ) : undefined
            }
          />
        )}
      </motion.div>
    </ErrorBoundary>
  );
}

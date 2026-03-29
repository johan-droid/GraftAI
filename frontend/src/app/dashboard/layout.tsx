"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { LayoutDashboard, Calendar, Settings, Bot, Menu, X, LogOut, Activity, Puzzle, ChevronDown, Building2, Plus, LayoutGrid } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthContext } from "@/app/providers/auth-provider";
import { useTenant } from "@/hooks/use-tenant";

const SIDEBAR_LINKS = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Analytics", href: "/dashboard/analytics", icon: Activity },
  { name: "Calendar", href: "/dashboard/calendar", icon: Calendar },
  { name: "AI Copilot", href: "/dashboard/ai", icon: Bot },
  { name: "Plugins", href: "/dashboard/plugins", icon: Puzzle },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [orgSwitcherOpen, setOrgSwitcherOpen] = useState(false);
  const { logout } = useAuthContext();
  const { 
    organizations, 
    workspaces, 
    activeOrgId, 
    activeWorkspaceId, 
    isLoading, 
    isWorkspacesLoading, 
    switchOrganization, 
    switchWorkspace 
  } = useTenant();

  const currentOrg = organizations.find(o => o.id.toString() === activeOrgId);
  const currentWorkspace = workspaces.find(w => w.id.toString() === activeWorkspaceId);

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden relative">
      
      {/* Background Ambience */}
      <div className="absolute top-0 right-0 w-full h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex flex-col w-60 border-r border-slate-800/50 bg-slate-950/40 backdrop-blur-xl z-20">
        <div className="p-5 flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-fuchsia-600 flex items-center justify-center shadow-[0_0_12px_rgba(79,70,229,0.4)]">
            <span className="text-white font-bold text-base leading-none">G</span>
          </div>
          <span className="font-bold text-base tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">GraftAI</span>
        </div>

        {/* Organization Switcher */}
        <div className="px-5 mb-4 relative">
          <button 
            onClick={() => setOrgSwitcherOpen(!orgSwitcherOpen)}
            className="flex w-full items-center justify-between gap-3 p-2.5 rounded-xl bg-slate-900/50 border border-slate-800/50 hover:bg-slate-800 transition-all text-left"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-6 h-6 rounded bg-slate-800 flex items-center justify-center flex-shrink-0">
                {currentWorkspace ? (
                  <LayoutGrid className="w-3.5 h-3.5 text-fuchsia-500" />
                ) : (
                  <Building2 className="w-3.5 h-3.5 text-primary" />
                )}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-white truncate">
                  {isLoading ? "Loading..." : (
                    currentWorkspace 
                      ? `${currentOrg?.name} / ${currentWorkspace?.name}` 
                      : (currentOrg?.name || "Select Org")
                  )}
                </span>
                <span className="text-[10px] text-slate-500 font-medium">
                  {currentWorkspace ? "Workspace" : "Organization"}
                </span>
              </div>
            </div>
            <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform ${orgSwitcherOpen ? "rotate-180" : ""}`} />
          </button>

          <AnimatePresence>
            {orgSwitcherOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setOrgSwitcherOpen(false)} />
                <motion.div 
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  className="absolute top-full left-5 right-5 mt-2 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl z-20 overflow-hidden py-1.5"
                >
                  <div className="px-3 py-1.5 border-b border-slate-800/50 mb-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Your Organizations</span>
                  </div>
                  <div className="max-h-40 overflow-y-auto custom-scrollbar">
                    {organizations.map(org => (
                      <button
                        key={org.id}
                        onClick={() => {
                          switchOrganization(org.id.toString());
                          setOrgSwitcherOpen(false);
                        }}
                        className={`flex w-full items-center gap-3 px-3 py-2 text-sm transition-all group ${
                          activeOrgId === org.id.toString() 
                            ? "bg-primary/10 text-primary" 
                            : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                        }`}
                      >
                        <div className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 ${
                          activeOrgId === org.id.toString() ? "bg-primary/20" : "bg-slate-800 group-hover:bg-slate-700"
                        }`}>
                          <span className="text-[10px] font-bold">{org.name[0]}</span>
                        </div>
                        <span className="truncate flex-1 text-left">{org.name}</span>
                        {activeOrgId === org.id.toString() && (
                          <div className="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(79,70,229,1)]" />
                        )}
                      </button>
                    ))}
                  </div>

                  {activeOrgId && (
                    <>
                      <div className="px-3 py-1.5 border-t border-b border-slate-800/50 my-1">
                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Workspaces in {currentOrg?.name}</span>
                      </div>
                      <div className="max-h-40 overflow-y-auto custom-scrollbar">
                        {isWorkspacesLoading ? (
                          <div className="px-3 py-2 text-xs text-slate-500 italic">Syncing workspaces...</div>
                        ) : workspaces.length > 0 ? (
                          workspaces.map(ws => (
                            <button
                              key={ws.id}
                              onClick={() => {
                                switchWorkspace(ws.id.toString());
                                setOrgSwitcherOpen(false);
                              }}
                              className={`flex w-full items-center gap-3 px-3 py-2 text-sm transition-all group ${
                                activeWorkspaceId === ws.id.toString() 
                                  ? "bg-fuchsia-500/10 text-fuchsia-500" 
                                  : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                              }`}
                            >
                              <div className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 ${
                                activeWorkspaceId === ws.id.toString() ? "bg-fuchsia-500/20" : "bg-slate-800 group-hover:bg-slate-700"
                              }`}>
                                <LayoutGrid className="w-3 h-3" />
                              </div>
                              <span className="truncate flex-1 text-left">{ws.name}</span>
                              {activeWorkspaceId === ws.id.toString() && (
                                <div className="w-1.5 h-1.5 rounded-full bg-fuchsia-500 shadow-[0_0_8px_rgba(217,70,239,1)]" />
                              )}
                            </button>
                          ))
                        ) : (
                          <div className="px-3 py-2 text-xs text-slate-500 italic">No workspaces found</div>
                        )}
                      </div>
                    </>
                  )}

                  <div className="mt-1 pt-1 border-t border-slate-800/50">
                    <button className="flex w-full items-center gap-3 px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all">
                      <Plus className="w-4 h-4" />
                      <span>Create New Context</span>
                    </button>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </div>

        <nav className="flex-1 px-4 space-y-2 overflow-y-auto custom-scrollbar">
          {SIDEBAR_LINKS.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.name}
                href={link.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive 
                    ? "bg-primary/10 text-primary font-medium" 
                    : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                }`}
              >
                <link.icon className="w-5 h-5" />
                {link.name}
                {isActive && (
                  <motion.div 
                    layoutId="active-nav" 
                    className="absolute left-0 w-1 h-8 bg-primary rounded-r-full"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800/50">
          <button onClick={logout} className="flex w-full items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all">
            <LogOut className="w-5 h-5" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* Mobile Header & Content Wrapper */}
      <div className="flex-1 flex flex-col min-w-0 z-10">
        
        {/* Mobile Header */}
        <header className="lg:hidden flex items-center justify-between p-3.5 border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-md sticky top-0 z-30">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-primary to-fuchsia-600 flex items-center justify-center shadow-[0_0_10px_rgba(79,70,229,0.3)]">
              <span className="text-white font-bold text-xs leading-none">G</span>
            </div>
            <span className="font-bold text-sm tracking-tight">GraftAI</span>
          </div>
          <button 
            onClick={() => setMobileMenuOpen(true)}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 active:scale-95 transition-all"
          >
            <Menu className="w-4 h-4" />
          </button>
        </header>

        {/* Mobile Sidebar Overlay */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <>
              <motion.div 
                initial={{ opacity: 0 }} 
                animate={{ opacity: 1 }} 
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
                onClick={() => setMobileMenuOpen(false)}
              />
              <motion.aside
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="fixed inset-y-0 right-0 w-64 bg-slate-950 border-l border-slate-800 z-50 flex flex-col shadow-2xl lg:hidden"
              >
                <div className="flex items-center justify-between p-4 border-b border-slate-800/50">
                  <span className="font-medium text-slate-200">Menu</span>
                  <button onClick={() => setMobileMenuOpen(false)} className="p-2 text-slate-400 hover:text-white">
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                <div className="px-4 mt-6">
                  <div className="flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-900 border border-slate-800">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-slate-800 flex items-center justify-center">
                        {currentWorkspace ? (
                          <LayoutGrid className="w-4 h-4 text-fuchsia-500" />
                        ) : (
                          <Building2 className="w-4 h-4 text-primary" />
                        )}
                      </div>
                      <div className="flex flex-col">
                        <span className="text-sm font-semibold text-white">
                          {isLoading ? "Loading..." : (
                            currentWorkspace 
                              ? `${currentOrg?.name} / ${currentWorkspace?.name}` 
                              : (currentOrg?.name || "Select Org")
                          )}
                        </span>
                        <span className="text-xs text-slate-500">
                          {currentWorkspace ? "Active Workspace" : "Active Organization"}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-4 space-y-1">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">Organizations</span>
                    <div className="max-h-32 overflow-y-auto custom-scrollbar pt-2">
                      {organizations.map(org => (
                        <button
                          key={org.id}
                          onClick={() => switchOrganization(org.id.toString())}
                          className={`flex w-full items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
                            activeOrgId === org.id.toString() 
                              ? "bg-primary/10 text-primary" 
                              : "text-slate-400 hover:text-white"
                          }`}
                        >
                          <span className="truncate flex-1 text-left text-sm">{org.name}</span>
                          {activeOrgId === org.id.toString() && <div className="w-1.5 h-1.5 rounded-full bg-primary" />}
                        </button>
                      ))}
                    </div>
                  </div>

                  {activeOrgId && (
                    <div className="mt-4 space-y-1">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest px-2">Workspaces</span>
                      <div className="max-h-32 overflow-y-auto custom-scrollbar pt-2">
                        {isWorkspacesLoading ? (
                          <div className="px-3 py-2 text-xs text-slate-500 italic">Syncing...</div>
                        ) : workspaces.length > 0 ? (
                          workspaces.map(ws => (
                            <button
                              key={ws.id}
                              onClick={() => switchWorkspace(ws.id.toString())}
                              className={`flex w-full items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
                                activeWorkspaceId === ws.id.toString() 
                                  ? "bg-fuchsia-500/10 text-fuchsia-500" 
                                  : "text-slate-400 hover:text-white"
                              }`}
                            >
                              <span className="truncate flex-1 text-left text-sm">{ws.name}</span>
                              {activeWorkspaceId === ws.id.toString() && <div className="w-1.5 h-1.5 rounded-full bg-fuchsia-500" />}
                            </button>
                          ))
                        ) : (
                          <div className="px-3 py-2 text-xs text-slate-500 italic">No workspaces</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto custom-scrollbar">
                  {SIDEBAR_LINKS.map((link) => {
                    const isActive = pathname === link.href;
                    return (
                      <Link
                        key={link.name}
                        href={link.href}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                          isActive 
                            ? "bg-primary/20 text-primary font-medium" 
                            : "text-slate-400 hover:text-white hover:bg-slate-900"
                        }`}
                      >
                        <link.icon className="w-5 h-5" />
                        {link.name}
                      </Link>
                    );
                  })}
                </nav>

                <div className="p-4 border-t border-slate-800/50">
                  <button onClick={logout} className="flex w-full items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:bg-slate-900 transition-all">
                    <LogOut className="w-5 h-5" />
                    <span>Sign out</span>
                  </button>
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-4 md:p-10 scroll-smooth">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, scale: 0.995 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className={`h-full w-full mx-auto flex flex-col items-center px-0 md:px-10`}
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}

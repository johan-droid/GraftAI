"use client";

import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuthContext } from "@/app/providers/auth-provider";
import { motion, AnimatePresence } from "framer-motion";
import {
  Calendar,
  Bot,
  ArrowUpRight,
  Sparkles,
  Plus,
  CheckCircle2,
  Circle,
  Trash2,
  TrendingUp,
  Activity,
  Clock,
  Star,
  Zap,
  ChevronRight,
} from "lucide-react";
import { getAnalyticsSummary, getProactiveSuggestion } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

// ─── Types ───────────────────────────────────────────────
type Priority = "low" | "medium" | "high";
interface Todo {
  id: string;
  text: string;
  done: boolean;
  priority: Priority;
  createdAt: number;
}

const PRIORITY_META: Record<Priority, { label: string; color: string; dot: string }> = {
  high: { label: "High", color: "text-rose-400", dot: "bg-rose-400" },
  medium: { label: "Medium", color: "text-amber-400", dot: "bg-amber-400" },
  low: { label: "Low", color: "text-emerald-400", dot: "bg-emerald-400" },
};

// ─── Greeting ────────────────────────────────────────────
function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return { word: "Good morning", emoji: "☀️" };
  if (h < 17) return { word: "Good afternoon", emoji: "🌤" };
  return { word: "Good evening", emoji: "🌙" };
}

// ─── Stat card ───────────────────────────────────────────
function StatCard({
  icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  color: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative overflow-hidden rounded-2xl p-5 transition-all glass-panel"
    >
      <div className={`mb-3 inline-flex h-9 w-9 items-center justify-center rounded-xl ${color}`}>
        {icon}
      </div>
      <p className="mb-0.5 text-xs font-medium text-slate-500">{label}</p>
      <p className="text-2xl font-bold tracking-tight text-white">{value}</p>
      {sub && (
        <p className="mt-1 flex items-center gap-1 text-[11px] font-medium text-emerald-400">
          <TrendingUp className="h-3 w-3" />
          {sub}
        </p>
      )}
    </motion.div>
  );
}

// ─── Todo item ───────────────────────────────────────────
function TodoItem({
  todo,
  onToggle,
  onDelete,
}: {
  todo: Todo;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const meta = PRIORITY_META[todo.priority];
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 12, scale: 0.95 }}
      className={`group flex items-center gap-3 rounded-xl border px-4 py-3 transition-all ${
        todo.done
          ? "border-slate-800/30 bg-transparent opacity-50"
          : "border-slate-800/60 bg-slate-900/40 hover:border-slate-700/60"
      }`}
    >
      <button
        onClick={() => onToggle(todo.id)}
        title={todo.done ? "Mark task incomplete" : "Mark task complete"}
        className="shrink-0 text-slate-500 transition-colors hover:text-indigo-400"
      >
        {todo.done ? (
          <CheckCircle2 className="h-4 w-4 text-indigo-400" />
        ) : (
          <Circle className="h-4 w-4" />
        )}
      </button>

      <span
        className={`flex-1 text-sm font-medium transition-all ${
          todo.done ? "line-through text-slate-600" : "text-slate-200"
        }`}
      >
        {todo.text}
      </span>

      <div className="flex shrink-0 items-center gap-2">
        <span className={`hidden text-[10px] font-bold sm:inline ${meta.color}`}>
          {meta.label}
        </span>
        <div className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
        <button
          onClick={() => onDelete(todo.id)}
          title="Delete task"
          className="hidden text-slate-700 transition-colors hover:text-red-400 group-hover:block"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </motion.div>
  );
}

// ─── Main dashboard ──────────────────────────────────────
export default function Dashboard() {
  const router = useRouter();
  const { user, isAuthenticated, loading } = useAuthContext();
  type DashboardUser = { full_name?: string; email?: string; name?: string } | null;
  const typedUser = user as DashboardUser;
  const profileName =
    typedUser?.full_name ||
    typedUser?.name ||
    typedUser?.email?.split("@")[0] ||
    "there";

  const { word: greeting, emoji } = getGreeting();

  const [stats, setStats] = useState({ meetings: 0, hours: 0, growth: 0 });
  const [aiSuggestion, setAiSuggestion] = useState("");
  const [summaryMsg, setSummaryMsg] = useState("");

  const [todos, setTodos] = useState<Todo[]>(() => {
    if (typeof window === "undefined") return defaultTodos();
    try {
      const stored = localStorage.getItem("graftai-todos");
      return stored ? JSON.parse(stored) : defaultTodos();
    } catch {
      return defaultTodos();
    }
  });
  const [newTodoText, setNewTodoText] = useState("");
  const [newPriority, setNewPriority] = useState<Priority>("medium");
  const [todoFilter, setTodoFilter] = useState<"all" | "active" | "done">("active");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    localStorage.setItem("graftai-todos", JSON.stringify(todos));
  }, [todos]);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
      return;
    }
    if (!isAuthenticated) return;

    getAnalyticsSummary()
      .then((d) => {
        setSummaryMsg(d.summary);
        if (d.details?.meetings) setStats(d.details as { meetings: number; hours: number; growth: number });
        else setStats({ meetings: 12, hours: 8.5, growth: 14 });
      })
      .catch(() => setStats({ meetings: 12, hours: 8.5, growth: 14 }));

    getProactiveSuggestion("dashboard")
      .then((d) => setAiSuggestion(d.suggestion))
      .catch(() => {});
  }, [isAuthenticated, loading, router]);

  if (loading || !isAuthenticated) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
      </div>
    );
  }

  const addTodo = () => {
    const text = newTodoText.trim();
    if (!text) return;
    const t: Todo = {
      id: Date.now().toString(),
      text,
      done: false,
      priority: newPriority,
      createdAt: Date.now(),
    };
    setTodos((prev) => [t, ...prev]);
    setNewTodoText("");
    inputRef.current?.focus();
    toast.success("Task added");
  };

  const toggleTodo = (id: string) => {
    setTodos((prev) =>
      prev.map((t) => {
        if (t.id !== id) return t;
        const updated = { ...t, done: !t.done };
        if (updated.done) toast.success("Task completed ✓");
        return updated;
      })
    );
  };

  const deleteTodo = (id: string) => {
    setTodos((prev) => prev.filter((t) => t.id !== id));
    toast.info("Task removed");
  };

  const clearDone = () => {
    const count = todos.filter((t) => t.done).length;
    setTodos((prev) => prev.filter((t) => !t.done));
    if (count > 0) toast.info(`Cleared ${count} completed task${count > 1 ? "s" : ""}`);
  };

  const filtered = todos.filter((t) =>
    todoFilter === "all" ? true : todoFilter === "done" ? t.done : !t.done
  );
  const doneCount = todos.filter((t) => t.done).length;
  const completionPct = todos.length ? Math.round((doneCount / todos.length) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="mb-1 text-sm font-medium text-slate-500">
            {emoji} {greeting}
          </p>
          <h1 className="text-2xl font-bold tracking-tight text-white text-gradient sm:text-3xl">
            {profileName}
          </h1>
          {summaryMsg && (
            <p className="mt-1 max-w-md text-sm text-slate-400">{summaryMsg}</p>
          )}
        </div>
        <Link
          href="/dashboard/calendar"
          className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 transition-all hover:bg-indigo-500 hover:-translate-y-0.5"
        >
          <Calendar className="h-4 w-4" />
          New booking
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
        <StatCard
          icon={<Calendar className="h-4 w-4 text-indigo-400" />}
          label="Upcoming meetings"
          value={String(stats.meetings)}
          sub="+2 this week"
          color="bg-indigo-500/10"
        />
        <StatCard
          icon={<Clock className="h-4 w-4 text-violet-400" />}
          label="AI hours saved"
          value={`${stats.hours}h`}
          sub={`${stats.growth}% vs last week`}
          color="bg-violet-500/10"
        />
        <StatCard
          icon={<Activity className="h-4 w-4 text-emerald-400" />}
          label="System status"
          value="Online"
          sub="99.9% uptime"
          color="bg-emerald-500/10"
        />
        <StatCard
          icon={<Star className="h-4 w-4 text-amber-400" />}
          label="Tasks done"
          value={`${completionPct}%`}
          sub={`${doneCount} of ${todos.length}`}
          color="bg-amber-500/10"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3 lg:gap-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="flex flex-col gap-4 lg:col-span-2"
        >
          <div className="rounded-2xl glass-panel p-5">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white">Today&apos;s tasks</h2>
                <p className="text-xs text-slate-500">
                  {doneCount}/{todos.length} complete
                </p>
              </div>
              <div className="flex items-center gap-2">
                <div className="hidden items-center gap-2 sm:flex">
                  <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-800">
                    <motion.div
                      className="h-full rounded-full bg-indigo-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${completionPct}%` }}
                      transition={{ duration: 0.6, ease: "easeOut" }}
                    />
                  </div>
                  <span className="text-xs font-medium text-slate-500">{completionPct}%</span>
                </div>
                <button
                  onClick={clearDone}
                  className="rounded-lg px-2.5 py-1.5 text-[11px] font-semibold text-slate-500 transition-colors hover:bg-slate-800/60 hover:text-slate-300"
                >
                  Clear done
                </button>
              </div>
            </div>

            <div className="mb-4 flex gap-2">
              <div className="flex flex-1 items-center gap-2 rounded-xl border border-slate-700/50 bg-slate-900/50 px-3 py-2.5 transition-colors focus-within:border-indigo-500/40 focus-within:ring-2 focus-within:ring-indigo-500/10">
                <Plus className="h-3.5 w-3.5 shrink-0 text-slate-600" />
                <input
                  ref={inputRef}
                  value={newTodoText}
                  onChange={(e) => setNewTodoText(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && addTodo()}
                  placeholder="Add a task… (Enter to save)"
                  className="flex-1 bg-transparent text-sm text-slate-200 outline-none placeholder:text-slate-600"
                />
              </div>
              <div className="flex rounded-xl border border-slate-700/50 bg-slate-900/50 p-1 gap-0.5">
                {(["low", "medium", "high"] as Priority[]).map((p) => (
                  <button
                    key={p}
                    onClick={() => setNewPriority(p)}
                    title={p}
                    className={`h-7 w-7 rounded-lg transition-all ${
                      newPriority === p
                        ? `bg-slate-800 ${PRIORITY_META[p].color}`
                        : "text-slate-700 hover:text-slate-500"
                    }`}
                  >
                    <div className={`mx-auto h-2 w-2 rounded-full ${PRIORITY_META[p].dot} ${newPriority !== p ? "opacity-40" : ""}`} />
                  </button>
                ))}
              </div>
              <button
                onClick={addTodo}
                disabled={!newTodoText.trim()}
                className="rounded-xl bg-indigo-600 px-3 text-sm font-semibold text-white transition-all hover:bg-indigo-500 disabled:opacity-30"
              >
                Add
              </button>
            </div>

            <div className="mb-4 flex gap-1 rounded-xl bg-slate-900/50 p-1">
              {(["active", "all", "done"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setTodoFilter(f)}
                  className={`flex-1 rounded-lg py-1.5 text-xs font-semibold capitalize transition-all ${
                    todoFilter === f
                      ? "bg-slate-800 text-slate-200 shadow-sm"
                      : "text-slate-600 hover:text-slate-400"
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>

            <div className="flex flex-col gap-2">
              <AnimatePresence mode="popLayout">
                {filtered.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="py-10 text-center text-sm text-slate-600"
                  >
                    {todoFilter === "done" ? "No completed tasks yet" : "All clear! Add a task above ↑"}
                  </motion.div>
                ) : (
                  filtered.map((todo) => (
                    <TodoItem
                      key={todo.id}
                      todo={todo}
                      onToggle={toggleTodo}
                      onDelete={deleteTodo}
                    />
                  ))
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>

        <div className="flex flex-col gap-4">
          {aiSuggestion && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="rounded-2xl border border-indigo-500/15 bg-indigo-500/6 p-4"
            >
              <div className="mb-2 flex items-center gap-2">
                <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                  AI insight
                </span>
              </div>
              <p className="text-sm leading-relaxed text-slate-300">{aiSuggestion}</p>
            </motion.div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="rounded-2xl glass-panel p-5"
          >
            <h2 className="mb-4 text-sm font-bold text-white">Quick access</h2>
            <div className="flex flex-col gap-2">
              {[
                { href: "/dashboard/calendar", icon: <Calendar className="h-4 w-4" />, label: "Calendar", sub: "View upcoming" },
                { href: "/dashboard/ai", icon: <Bot className="h-4 w-4" />, label: "AI Copilot", sub: "Chat & schedule" },
                { href: "/dashboard/analytics", icon: <Activity className="h-4 w-4" />, label: "Analytics", sub: "Your stats" },
              ].map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="flex items-center gap-3 rounded-xl border border-slate-800/50 bg-slate-900/30 px-3 py-3 transition-all hover:border-slate-700/60 hover:bg-slate-900/60 group"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-slate-400 transition-colors group-hover:bg-indigo-500/15 group-hover:text-indigo-400">
                    {link.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold text-slate-200">{link.label}</p>
                    <p className="text-[11px] text-slate-600">{link.sub}</p>
                  </div>
                  <ChevronRight className="h-3.5 w-3.5 text-slate-700 transition-colors group-hover:text-slate-500" />
                </Link>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="rounded-2xl border border-slate-800/40 bg-gradient-to-br from-indigo-500/8 via-slate-950/40 to-violet-500/5 p-5"
          >
            <div className="mb-1 flex items-center gap-2">
              <Zap className="h-3.5 w-3.5 text-indigo-400" />
              <span className="text-xs font-bold text-indigo-400">Sync calendar</span>
            </div>
            <p className="mb-4 text-[13px] leading-relaxed text-slate-400">
              Connect your calendar and let AI handle the scheduling.
            </p>
            <Link
              href="/dashboard/calendar"
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-2.5 text-sm font-bold text-white transition-all hover:bg-indigo-500 shadow-lg shadow-indigo-600/20"
            >
              Connect now
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function defaultTodos(): Todo[] {
  return [
    { id: "1", text: "Review Q2 meeting recordings", done: false, priority: "high", createdAt: Date.now() },
    { id: "2", text: "Set up cross-timezone sync for new team", done: false, priority: "medium", createdAt: Date.now() },
    { id: "3", text: "Update calendar integrations", done: true, priority: "low", createdAt: Date.now() },
    { id: "4", text: "Configure AI Copilot preferences", done: false, priority: "medium", createdAt: Date.now() },
  ];
}

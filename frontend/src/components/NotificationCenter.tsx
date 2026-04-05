"use client";

import React, { useEffect, useState, useRef } from "react";
import { Bell, X, Trash2 } from "lucide-react";
import { getNotifications, markNotification, markAllNotificationsRead, deleteNotification } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<any[]>([]);
  const ref = useRef<HTMLDivElement | null>(null);
  const router = useRouter();

  const unreadCount = items.filter((i) => !i.is_read).length;

  useEffect(() => {
    function onDoc(e: any) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    if (open) {
      document.addEventListener("click", onDoc);
      fetchItems();
    }
    return () => document.removeEventListener("click", onDoc);
  }, [open]);

  async function fetchItems() {
    setLoading(true);
    try {
      const res = await getNotifications(25, false);
      setItems(res || []);
    } catch (e) {
      console.warn("Failed to load notifications", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleMarkRead(id: number) {
    try {
      await markNotification(id, true);
      setItems((prev) => prev.map((it) => (it.id === id ? { ...it, is_read: true } : it)));
    } catch (e) {
      console.warn(e);
    }
  }

  async function handleClearAll() {
    try {
      await markAllNotificationsRead();
      setItems((prev) => prev.map((it) => ({ ...it, is_read: true })));
    } catch (e) {
      console.warn(e);
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteNotification(id);
      setItems((prev) => prev.filter((it) => it.id !== id));
    } catch (e) {
      console.warn(e);
    }
  }

  function openNotification(it: any) {
    // mark read and navigate to calendar
    handleMarkRead(it.id);
    // if event id present, go to calendar and include event id as query
    const eventId = it.data?.event_id;
    if (eventId) router.push(`/dashboard/calendar`);
    setOpen(false);
  }

  return (
    <div className="relative" ref={ref}>
      <button
        aria-label="View notifications"
        onClick={() => setOpen((s) => !s)}
        className="p-2 rounded-lg bg-white/5 border border-white/8 text-slate-400 hover:text-white hover:bg-white/8 transition-all relative"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && <span className="absolute top-1.5 right-1.5 w-3 h-3 bg-indigo-400 rounded-full text-[10px] leading-3 flex items-center justify-center text-white">{unreadCount}</span>}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-[360px] max-h-[420px] overflow-auto rounded-lg bg-[#041025] border border-white/[0.06] shadow-lg z-50 p-3">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-bold text-white">Notifications</h4>
            <div className="flex items-center gap-2">
              <button onClick={handleClearAll} className="text-xs text-slate-400 hover:text-white">Mark all read</button>
              <button aria-label="Close notifications" onClick={() => setOpen(false)} className="p-1 rounded hover:bg-white/5"><X className="w-4 h-4 text-slate-400" /></button>
            </div>
          </div>

          {loading && <div className="text-sm text-slate-400 p-4">Loading…</div>}

          {!loading && items.length === 0 && <div className="text-sm text-slate-400 p-4">No notifications</div>}

          <div className="space-y-2">
            {items.map((it) => (
              <div key={it.id} className={`p-2 rounded-lg border ${it.is_read ? "border-white/[0.03] bg-white/[0.01]" : "border-indigo-500/20 bg-white/[0.02]"}`}>
                <div className="flex items-start gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-3">
                      <p onClick={() => openNotification(it)} className="text-sm font-semibold text-white truncate cursor-pointer">{it.title}</p>
                      <div className="flex items-center gap-2">
                        <button aria-label="Delete notification" onClick={() => handleDelete(it.id)} className="p-1 rounded hover:bg-white/5"><Trash2 className="w-4 h-4 text-slate-400" /></button>
                      </div>
                    </div>
                    {it.body && <p className="text-xs text-slate-400 mt-1 truncate">{it.body}</p>}
                    <p className="text-[11px] text-slate-500 mt-1">{new Date(it.created_at).toLocaleString()}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

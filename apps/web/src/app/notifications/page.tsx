"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function NotificationsPage() {
  const [items, setItems] = useState<Array<Record<string, unknown>>>([]);
  const [unread, setUnread] = useState(0);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const data = await api.listNotifications();
    setItems(data.notifications);
    setUnread(data.unread);
  }

  useEffect(() => {
    refresh().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed"),
    );
  }, []);

  return (
    <AppShell>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-white">Alerts</h1>
          <p className="mt-2 text-slate-400">
            Workspace notifications when documents, agents, or meetings finish —{" "}
            {unread} unread.
          </p>
        </div>
        <button
          type="button"
          className="rounded-md border border-white/10 px-3 py-2 text-sm text-teal-300"
          onClick={() =>
            api.markAllNotificationsRead().then(refresh).catch(console.error)
          }
        >
          Mark all read
        </button>
      </div>
      {error && <p className="mt-3 text-rose-300">{error}</p>}
      <ul className="mt-8 space-y-3">
        {items.map((n) => (
          <li
            key={String(n.id)}
            className={`rounded-lg border px-4 py-3 ${
              n.is_read ? "border-white/10 bg-slate-950/30" : "border-teal-400/30 bg-slate-950/50"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-white">{String(n.title)}</div>
                <p className="mt-1 text-sm text-slate-400">{String(n.body)}</p>
                {n.link ? (
                  <Link href={String(n.link)} className="mt-2 inline-block text-xs text-teal-300">
                    Open
                  </Link>
                ) : null}
              </div>
              {!n.is_read && (
                <button
                  type="button"
                  className="text-xs text-slate-400 hover:text-white"
                  onClick={() =>
                    api
                      .markNotificationRead(String(n.id))
                      .then(refresh)
                      .catch(console.error)
                  }
                >
                  Mark read
                </button>
              )}
            </div>
          </li>
        ))}
        {!items.length && (
          <li className="text-slate-500">No notifications yet.</li>
        )}
      </ul>
    </AppShell>
  );
}

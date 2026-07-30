"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api, UserPublic } from "@/lib/api";

export default function AdminPage() {
  const [users, setUsers] = useState<UserPublic[]>([]);
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [me, setMe] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    const [u, s, m] = await Promise.all([
      api.adminUsers(),
      api.adminStats(),
      api.me(),
    ]);
    setUsers(u);
    setStats(s);
    setMe(m);
  }

  useEffect(() => {
    refresh()
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Admin access required"),
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <AppShell>
        <p className="text-slate-500">Loading admin…</p>
      </AppShell>
    );
  }

  if (me && me.role !== "admin") {
    return (
      <AppShell>
        <h1 className="font-display text-3xl text-white">Admin</h1>
        <p className="mt-3 text-rose-300">Admin role required.</p>
      </AppShell>
    );
  }

  const statEntries = stats
    ? Object.entries(stats).filter(
        ([, v]) => typeof v === "number" || typeof v === "string",
      )
    : [];

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Admin</h1>
      <p className="mt-2 text-slate-400">
        Platform stats and user management (activate, deactivate, promote).
      </p>
      {error && <p className="mt-3 text-rose-300">{error}</p>}

      {statEntries.length > 0 && (
        <section className="mt-8">
          <h2 className="text-sm uppercase tracking-wide text-slate-500">Stats</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {statEntries.map(([key, value]) => (
              <div
                key={key}
                className="rounded-xl border border-white/10 bg-slate-950/40 px-4 py-4"
              >
                <div className="text-xs uppercase tracking-wide text-slate-500">
                  {key.replaceAll("_", " ")}
                </div>
                <div className="mt-2 font-display text-3xl text-teal-300">
                  {String(value)}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <h2 className="mt-10 text-sm uppercase tracking-wide text-slate-500">Users</h2>
      <ul className="mt-3 space-y-3">
        {users.length === 0 && (
          <li className="text-sm text-slate-500">No users returned.</li>
        )}
        {users.map((u) => (
          <li
            key={u.id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-white/10 bg-slate-950/40 px-4 py-3"
          >
            <div>
              <div className="text-white">{u.email}</div>
              <div className="text-xs text-slate-500">
                {u.role} · {u.is_active ? "active" : "inactive"}
              </div>
            </div>
            <div className="flex gap-2 text-xs">
              <button
                type="button"
                className="rounded border border-white/10 px-2 py-1 text-teal-300"
                onClick={() =>
                  api.adminActivate(u.id).then(refresh).catch(console.error)
                }
              >
                Activate
              </button>
              <button
                type="button"
                className="rounded border border-white/10 px-2 py-1 text-rose-300"
                onClick={() =>
                  api.adminDeactivate(u.id).then(refresh).catch(console.error)
                }
              >
                Deactivate
              </button>
              <button
                type="button"
                className="rounded border border-white/10 px-2 py-1 text-slate-300"
                onClick={() =>
                  api.adminPromote(u.id).then(refresh).catch(console.error)
                }
              >
                Promote
              </button>
            </div>
          </li>
        ))}
      </ul>
    </AppShell>
  );
}

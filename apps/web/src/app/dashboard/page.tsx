"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { AuthError, api, clearTokens, DashboardSummary } from "@/lib/api";

const START_HERE = [
  {
    href: "/chat",
    title: "1. Chat",
    body: "Streaming conversation with the local AI model.",
  },
  {
    href: "/documents",
    title: "2. Documents",
    body: "Upload files and ask questions with citations (RAG).",
  },
  {
    href: "/sql",
    title: "3. SQL",
    body: "Natural language → safe SELECT on the demo database.",
  },
  {
    href: "/agents",
    title: "4. Agents",
    body: "Multi-step orchestration with a report and score.",
  },
];

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .dashboard()
      .then(setData)
      .catch((err) => {
        if (err instanceof AuthError) {
          clearTokens();
          router.replace("/login?reason=expired");
          return;
        }
        setError(err instanceof Error ? err.message : "Load failed");
      })
      .finally(() => setLoading(false));
  }, [router]);

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Home</h1>
      <p className="mt-2 max-w-2xl text-slate-400">
        Account hub for AI Workspace. Follow <span className="text-slate-200">Start here</span>{" "}
        for the core demo path, then explore Tools and Platform in the navigation.
      </p>

      {loading && <p className="mt-6 text-slate-500">Loading your workspace…</p>}
      {error && (
        <div className="mt-6 rounded-lg border border-rose-400/30 bg-rose-950/30 px-4 py-3 text-sm text-rose-200">
          {error}
          <div className="mt-2">
            <Link href="/login" className="text-teal-300 hover:underline">
              Sign in again
            </Link>
          </div>
        </div>
      )}

      <section className="mt-8">
        <h2 className="text-sm uppercase tracking-wide text-slate-500">Start here</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {START_HERE.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-xl border border-white/10 bg-slate-950/40 px-4 py-4 transition hover:border-teal-400/40"
            >
              <div className="font-medium text-white">{item.title}</div>
              <p className="mt-1 text-sm text-slate-400">{item.body}</p>
            </Link>
          ))}
        </div>
      </section>

          {data && (
        <div className="mt-10 space-y-8">
          <section>
            <h2 className="text-sm uppercase tracking-wide text-slate-500">Your inventory</h2>
            <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(data.counts).map(([key, value]) => (
                <div
                  key={key}
                  className="rounded-xl border border-white/10 bg-slate-950/40 px-4 py-5"
                >
                  <div className="text-xs uppercase tracking-wide text-slate-500">
                    {key.replaceAll("_", " ")}
                  </div>
                  <div className="mt-2 font-display text-3xl text-teal-300">{value}</div>
                </div>
              ))}
              {Object.keys(data.counts).length === 0 && (
                <p className="text-sm text-slate-500 sm:col-span-2">
                  Counts appear after you create chats, upload documents, or run tools.
                </p>
              )}
              <div className="rounded-xl border border-white/10 bg-slate-950/40 px-4 py-5">
                <div className="text-xs uppercase tracking-wide text-slate-500">storage</div>
                <div className="mt-2 font-display text-3xl text-teal-300">
                  {(((data.storage_bytes ?? 0) / 1024 / 1024) || 0).toFixed(1)} MB
                </div>
              </div>
              <div className="rounded-xl border border-white/10 bg-slate-950/40 px-4 py-5">
                <div className="text-xs uppercase tracking-wide text-slate-500">tokens</div>
                <div className="mt-2 font-display text-3xl text-teal-300">
                  {data.token_usage?.total ?? 0}
                </div>
              </div>
              <div className="rounded-xl border border-white/10 bg-slate-950/40 px-4 py-5">
                <div className="text-xs uppercase tracking-wide text-slate-500">alerts</div>
                <div className="mt-2 font-display text-3xl text-teal-300">
                  {data.unread_notifications ?? 0}
                </div>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-sm uppercase tracking-wide text-slate-500">Recent activity</h2>
            <ul className="mt-3 space-y-2 text-sm text-slate-300">
              {data.recent_activity.length === 0 && (
                <li className="text-slate-500">
                  Nothing yet — open Chat or upload a document to see activity here.
                </li>
              )}
              {data.recent_activity.map((event) => (
                <li key={event.id} className="rounded-md border border-white/10 px-3 py-2">
                  {event.event_type}
                  <span className="text-slate-500"> · {event.created_at}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-xl border border-white/10 bg-slate-950/40 p-4 text-sm text-slate-300">
            Signed in as {data.settings.email}
            {data.settings.full_name ? ` (${data.settings.full_name})` : ""} · role{" "}
            {data.settings.role}
          </section>
        </div>
      )}
    </AppShell>
  );
}

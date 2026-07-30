"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type AgentStep = {
  agent?: string;
  sql?: string;
  preview?: unknown;
  row_count?: number;
  report?: string;
  score?: number;
  answer?: string;
  advice?: string;
};

export default function AgentsPage() {
  const [task, setTask] = useState("What is total order revenue in SQL?");
  const [runs, setRuns] = useState<Array<Record<string, unknown>>>([]);
  const [active, setActive] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setRuns(await api.listAgentRuns());
  }

  useEffect(() => {
    refresh().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const run = await api.runAgents(task);
      setActive(run);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agent run failed");
    } finally {
      setBusy(false);
    }
  }

  const steps = (active?.steps_json as AgentStep[] | undefined) ?? [];
  const score = (active?.evaluation_json as { score?: number } | undefined)?.score;

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Agents</h1>
      <p className="mt-2 max-w-2xl text-slate-400">
        Planner routes to SQL / retrieval / code specialists, then writes a report and
        score. Inspect step details under{" "}
        <Link href="/observability" className="text-teal-300 hover:underline">
          Traces
        </Link>
        .
      </p>
      <form onSubmit={onSubmit} className="mt-6 flex gap-3">
        <input
          className="flex-1 rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100 outline-none focus:border-teal-400"
          value={task}
          onChange={(e) => setTask(e.target.value)}
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
        >
          {busy ? "Running…" : "Run agents"}
        </button>
      </form>
      {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
      <div className="mt-8 grid gap-6 md:grid-cols-[240px_1fr]">
        <ul className="space-y-2">
          {runs.length === 0 && (
            <li className="text-sm text-slate-500">No runs yet. Submit a task above.</li>
          )}
          {runs.map((r) => (
            <li key={String(r.id)}>
              <button
                type="button"
                className="w-full truncate rounded-md border border-white/10 px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5"
                onClick={() => setActive(r)}
              >
                {String(r.task)}
              </button>
            </li>
          ))}
        </ul>
        {!active && (
          <p className="text-sm text-slate-500">
            Select a past run or start a new one. Tip: try a SQL revenue question for a
            clear demo.
          </p>
        )}
        {active && (
          <div className="space-y-5 rounded-xl border border-white/10 bg-slate-950/40 p-5">
            <div className="text-sm text-teal-300">
              Score: {score != null ? String(score) : "—"}
            </div>
            <section>
              <h2 className="text-sm uppercase tracking-wide text-slate-500">Report</h2>
              <p className="mt-2 whitespace-pre-wrap text-slate-200">
                {String(active.report ?? "No report")}
              </p>
            </section>
            <section>
              <h2 className="text-sm uppercase tracking-wide text-slate-500">Steps</h2>
              <ol className="mt-3 space-y-3">
                {steps.map((step, i) => (
                  <li
                    key={i}
                    className="rounded-md border border-white/10 px-3 py-2 text-sm"
                  >
                    <div className="text-teal-300">{step.agent || `step ${i + 1}`}</div>
                    {step.sql && (
                      <pre className="mt-2 overflow-x-auto text-xs text-teal-100">
                        {step.sql}
                      </pre>
                    )}
                    {step.preview != null && (
                      <p className="mt-2 text-slate-400">
                        Result:{" "}
                        {Array.isArray(step.preview)
                          ? step.preview
                              .slice(0, 3)
                              .map((row) =>
                                typeof row === "object" && row
                                  ? Object.values(row as Record<string, unknown>).join(", ")
                                  : String(row),
                              )
                              .join(" · ")
                          : String(step.preview)}
                      </p>
                    )}
                    {step.advice && (
                      <p className="mt-2 text-slate-300">{step.advice}</p>
                    )}
                    {step.answer && (
                      <p className="mt-2 line-clamp-4 text-slate-300">{step.answer}</p>
                    )}
                  </li>
                ))}
              </ol>
            </section>
          </div>
        )}
      </div>
    </AppShell>
  );
}

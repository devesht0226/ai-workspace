"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type TraceSummary = {
  id: string;
  request_text: string;
  status: string;
  model_family: string | null;
  total_latency_ms: number;
  total_tokens: number;
  created_at: string | null;
};

type TraceStep = {
  agent_name?: string;
  tool_name?: string;
  latency_ms?: number;
  model_name?: string;
  output?: string;
};

export default function ObservabilityPage() {
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listTraces()
      .then((data) => setTraces(data.traces as TraceSummary[]))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed"));
  }, []);

  async function openTrace(id: string) {
    try {
      setSelected(await api.getTrace(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load trace");
    }
  }

  const steps = (selected?.steps as TraceStep[] | undefined) ?? [];

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Traces</h1>
      <p className="mt-2 max-w-2xl text-slate-400">
        Step-by-step agent execution: planner → specialists → report → evaluation,
        with latency and token estimates. Create traces from{" "}
        <Link href="/agents" className="text-teal-300 hover:underline">
          Agents
        </Link>
        .
      </p>
      {error && <p className="mt-3 text-rose-300">{error}</p>}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <ul className="space-y-2">
          {traces.map((t) => (
            <li key={t.id}>
              <button
                type="button"
                onClick={() => openTrace(t.id)}
                className="w-full rounded-lg border border-white/10 bg-slate-950/40 px-4 py-3 text-left hover:border-teal-400/40"
              >
                <div className="truncate text-sm text-white">{t.request_text}</div>
                <div className="mt-1 text-xs text-slate-500">
                  {t.status} · {t.total_latency_ms}ms · ~{t.total_tokens} tokens ·{" "}
                  {t.model_family ?? "default"}
                </div>
              </button>
            </li>
          ))}
          {!traces.length && (
            <p className="text-sm text-slate-500">
              No traces yet. Run an agent task from Agents to create one.
            </p>
          )}
        </ul>

        <section className="max-h-[70vh] overflow-auto rounded-xl border border-white/10 bg-slate-950/50 p-4">
          {!selected && (
            <p className="text-sm text-slate-500">
              Select a trace to inspect each agent step.
            </p>
          )}
          {selected && (
            <div className="space-y-4">
              <div>
                <div className="text-sm text-white">
                  {String(selected.request_text ?? "Trace")}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  status {String(selected.status ?? "—")} ·{" "}
                  {String(selected.total_latency_ms ?? 0)} ms
                </div>
              </div>
              {steps.length === 0 ? (
                <p className="text-sm text-slate-500">No step details on this trace.</p>
              ) : (
                <ol className="space-y-3">
                  {steps.map((step, i) => (
                    <li
                      key={i}
                      className="rounded-md border border-white/10 px-3 py-2 text-sm"
                    >
                      <div className="flex justify-between gap-2">
                        <span className="text-teal-300">
                          {step.agent_name || step.tool_name || `step ${i + 1}`}
                        </span>
                        <span className="text-xs text-slate-500">
                          {step.latency_ms != null ? `${step.latency_ms} ms` : ""}
                        </span>
                      </div>
                      {step.output && (
                        <p className="mt-2 line-clamp-4 text-slate-400">
                          {String(step.output)}
                        </p>
                      )}
                    </li>
                  ))}
                </ol>
              )}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}

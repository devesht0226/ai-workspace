"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

function MetricCards({ metrics }: { metrics: Record<string, unknown> }) {
  const entries = Object.entries(metrics).filter(
    ([, v]) => typeof v === "number" || typeof v === "string",
  );
  if (!entries.length) return null;
  return (
    <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {entries.map(([key, value]) => (
        <div
          key={key}
          className="rounded-xl border border-white/10 bg-slate-950/40 px-4 py-3"
        >
          <div className="text-xs uppercase tracking-wide text-slate-500">
            {key.replaceAll("_", " ")}
          </div>
          <div className="mt-1 font-display text-2xl text-teal-300">
            {typeof value === "number" ? Number(value).toFixed(3) : String(value)}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function EvalPage() {
  const [evals, setEvals] = useState<Array<Record<string, unknown>>>([]);
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [question, setQuestion] = useState("What is RAG?");
  const [answer, setAnswer] = useState(
    "RAG retrieves documents and grounds the LLM answer in those sources.",
  );
  const [context, setContext] = useState(
    "Retrieval-Augmented Generation (RAG) retrieves relevant documents to ground LLM answers.",
  );
  const [metrics, setMetrics] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listRagEvals(), api.feedbackSummary()])
      .then(([e, s]) => {
        setEvals(e.evals);
        setSummary(s);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed"));
  }, []);

  async function onScore(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const result = await api.scoreRag({
        question,
        answer,
        contexts: [context],
        retrieved_ids: ["doc-1"],
        citations: [{ snippet: context }],
      });
      setMetrics(result as Record<string, unknown>);
      const stored = await api.runRagEval({
        question,
        answer,
        contexts: [context],
        retrieved_ids: ["doc-1"],
        citations: [{ snippet: context }],
      });
      setEvals((prev) => [stored, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eval failed");
    }
  }

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Eval</h1>
      <p className="mt-2 max-w-2xl text-slate-400">
        Score how well an answer matches retrieved context — precision, faithfulness,
        hallucination risk, and more. Use this after a Documents Q&amp;A demo.
      </p>
      {summary && (
        <p className="mt-3 text-sm text-slate-400">
          Human feedback: {String(summary.good ?? 0)} good / {String(summary.bad ?? 0)}{" "}
          bad
          {summary.approval_rate != null
            ? ` (${Math.round(Number(summary.approval_rate) * 100)}% approval)`
            : ""}
        </p>
      )}
      <form onSubmit={onScore} className="mt-6 space-y-3">
        <input
          className="w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Question"
        />
        <textarea
          className="h-24 w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Answer"
        />
        <textarea
          className="h-24 w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="Retrieved context"
        />
        <button
          type="submit"
          className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950"
        >
          Score & store
        </button>
      </form>
      {error && <p className="mt-3 text-rose-300">{error}</p>}
      {metrics && (
        <section className="mt-6">
          <h2 className="text-sm uppercase tracking-wide text-slate-500">
            Latest scores
          </h2>
          <MetricCards metrics={metrics} />
        </section>
      )}
      <h2 className="mt-10 text-sm uppercase tracking-wide text-slate-500">
        Recent eval runs
      </h2>
      <ul className="mt-3 space-y-2">
        {evals.length === 0 && (
          <li className="text-sm text-slate-500">
            No runs yet. Score a question/answer pair above.
          </li>
        )}
        {evals.map((row) => (
          <li
            key={String(row.id)}
            className="rounded-lg border border-white/10 bg-slate-950/40 px-4 py-3 text-sm text-slate-300"
          >
            <div className="text-white">{String(row.question)}</div>
            <div className="mt-1 text-xs text-slate-500">
              overall={" "}
              {(row.metrics as { overall?: number } | undefined)?.overall ?? "—"}
            </div>
          </li>
        ))}
      </ul>
    </AppShell>
  );
}

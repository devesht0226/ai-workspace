"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type BenchResult = {
  family?: string;
  available?: boolean;
  error?: string;
  latency_ms?: number;
  answer?: string | null;
  scores?: { composite?: number; answer_relevance?: number };
};

export default function BenchmarkPage() {
  const [question, setQuestion] = useState(
    "Explain retrieval-augmented generation in two sentences.",
  );
  const [busy, setBusy] = useState(false);
  const [latest, setLatest] = useState<Record<string, unknown> | null>(null);
  const [history, setHistory] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listBenchmarks()
      .then((data) => setHistory(data.benchmarks))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed"));
  }, []);

  async function onRun(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.runBenchmark(question);
      setLatest(result);
      setHistory((prev) => [result, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Benchmark failed");
    } finally {
      setBusy(false);
    }
  }

  const results = (latest?.results as BenchResult[] | undefined) ?? [];
  const ranking = (latest?.ranking as string[] | undefined) ?? [];

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Benchmark</h1>
      <p className="mt-2 max-w-2xl text-slate-400">
        Ask the same question to Llama (Ollama), GPT, and Mistral. Families without
        API keys are marked unavailable. Local Llama works without cloud keys.
      </p>
      <form onSubmit={onRun} className="mt-6 flex gap-3">
        <input
          className="flex-1 rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
        >
          {busy ? "Running…" : "Benchmark"}
        </button>
      </form>
      {error && <p className="mt-3 text-rose-300">{error}</p>}

      {latest && (
        <section className="mt-8 space-y-4">
          {ranking.length > 0 && (
            <p className="text-sm text-teal-200">
              Ranking: {ranking.join(" → ")}
            </p>
          )}
          <div className="grid gap-3 md:grid-cols-3">
            {results.map((r) => (
              <article
                key={r.family}
                className="rounded-xl border border-white/10 bg-slate-950/40 p-4"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-white">{r.family}</h3>
                  <span className="text-xs text-slate-500">
                    {r.available ? `${r.latency_ms ?? 0} ms` : "n/a"}
                  </span>
                </div>
                {!r.available ? (
                  <p className="mt-3 text-sm text-rose-200/90">
                    {r.error || "Not configured"}
                  </p>
                ) : (
                  <>
                    <p className="mt-2 text-xs text-slate-500">
                      score{" "}
                      {r.scores?.composite != null
                        ? Number(r.scores.composite).toFixed(3)
                        : "—"}
                    </p>
                    <p className="mt-3 line-clamp-6 text-sm text-slate-300">
                      {r.answer || "No answer"}
                    </p>
                  </>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      <h2 className="mt-10 text-sm uppercase tracking-wide text-slate-500">History</h2>
      <ul className="mt-3 space-y-2 text-sm text-slate-400">
        {history.length === 0 && (
          <li className="text-slate-500">No benchmarks yet. Run one above.</li>
        )}
        {history.map((b) => (
          <li key={String(b.id)} className="rounded border border-white/10 px-3 py-2">
            <span className="text-slate-200">{String(b.question)}</span>
            <span className="text-slate-500">
              {" "}
              —{" "}
              {Array.isArray(b.ranking) && b.ranking.length
                ? b.ranking.join(" → ")
                : "no ranking"}
            </span>
          </li>
        ))}
      </ul>
    </AppShell>
  );
}

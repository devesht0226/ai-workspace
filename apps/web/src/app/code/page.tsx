"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function CodePage() {
  const [reviews, setReviews] = useState<Array<Record<string, unknown>>>([]);
  const [active, setActive] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const list = await api.codeReviews();
    setReviews(list);
  }

  useEffect(() => {
    refresh().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, []);

  async function onUpload(file: File | null) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const review = await api.createCodeReview(file);
      setActive(review);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  const result = (active?.result_json ?? null) as Record<string, unknown> | null;

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Code</h1>
      <p className="mt-2 text-slate-400">
        Upload a source file or ZIP. Heuristic checks catch common bugs and secrets;
        AI adds a short summary.
      </p>
      {!reviews.length && !active && (
        <p className="mt-4 text-sm text-slate-500">
          No reviews yet. Upload a small Python file with issues (eval, bare except) for
          a clear demo.
        </p>
      )}
      <input
        type="file"
        accept=".py,.ts,.tsx,.js,.zip,.txt,.md"
        disabled={busy}
        className="mt-6 block text-sm text-slate-300 file:mr-3 file:rounded-md file:border-0 file:bg-teal-400 file:px-3 file:py-1.5 file:font-semibold file:text-slate-950"
        onChange={(e) => onUpload(e.target.files?.[0] ?? null)}
      />
      {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
      <div className="mt-8 grid gap-6 md:grid-cols-[220px_1fr]">
        <ul className="space-y-2">
          {reviews.map((r) => (
            <li key={String(r.id)}>
              <button
                type="button"
                className="w-full rounded-md border border-white/10 px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5"
                onClick={() => setActive(r)}
              >
                {String(r.title)}
              </button>
            </li>
          ))}
        </ul>
        {result && (
          <div className="space-y-4 rounded-xl border border-white/10 bg-slate-950/40 p-5">
            <p className="text-slate-200">{String(result.summary ?? "")}</p>
            <h2 className="text-sm uppercase tracking-wide text-slate-500">Findings</h2>
            <ul className="space-y-2 text-sm text-slate-300">
              {((result.findings as Array<Record<string, unknown>>) || []).map((f, i) => (
                <li key={i} className="rounded-md border border-white/10 p-3">
                  <span className="text-teal-300">{String(f.severity)}</span> · {String(f.category)}
                  <div>{String(f.message)}</div>
                  <div className="text-xs text-slate-500">
                    {String(f.file)}
                    {f.line != null ? `:${String(f.line)}` : ""}
                  </div>
                </li>
              ))}
            </ul>
            {Array.isArray(result.refactoring_suggestions) && (
              <>
                <h2 className="text-sm uppercase tracking-wide text-slate-500">Refactor</h2>
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
                  {(result.refactoring_suggestions as string[]).map((tip) => (
                    <li key={tip}>{tip}</li>
                  ))}
                </ul>
              </>
            )}
            <h2 className="text-sm uppercase tracking-wide text-slate-500">Suggested tests</h2>
            <pre className="overflow-x-auto rounded-md border border-white/10 bg-slate-950 p-3 font-mono text-xs leading-relaxed text-teal-100">
              {String(result.unit_test_suggestions ?? "")}
            </pre>
            {result.complexity != null && (
              <>
                <h2 className="text-sm uppercase tracking-wide text-slate-500">Complexity</h2>
                <ul className="space-y-1 text-sm text-slate-300">
                  {Object.entries(result.complexity as Record<string, Record<string, number>>).map(
                    ([file, stats]) => (
                      <li key={file} className="rounded border border-white/10 px-3 py-2">
                        <div className="text-teal-200">{file}</div>
                        <div className="text-xs text-slate-500">
                          decisions {stats.decision_points ?? "—"} · estimate{" "}
                          {stats.cyclomatic_estimate ?? "—"}
                        </div>
                      </li>
                    ),
                  )}
                </ul>
              </>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}

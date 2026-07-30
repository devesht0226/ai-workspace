"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function SqlPage() {
  const [question, setQuestion] = useState("What is total revenue from orders?");
  const [sql, setSql] = useState("");
  const [explanation, setExplanation] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [schema, setSchema] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .sqlSchema()
      .then((s) => setSchema(String(s.schema_text ?? "")))
      .catch((err) => setError(err instanceof Error ? err.message : "Schema failed"));
  }, []);

  async function onGenerate(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const generated = await api.sqlGenerate(question);
      setSql(generated.sql);
      const [exp, opt, exec] = await Promise.all([
        api.sqlExplain(generated.sql),
        api.sqlOptimize(generated.sql),
        api.sqlExecute(generated.sql),
      ]);
      setExplanation(exp.explanation);
      setSuggestions(opt.suggestions);
      setColumns(exec.columns);
      setRows(exec.rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "SQL flow failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">SQL</h1>
      <p className="mt-2 text-slate-400">
        Ask in plain English. The assistant generates a read-only SELECT on the demo
        analytics database, then explains and runs it.
      </p>
      <details className="mt-4 rounded-xl border border-white/10 bg-slate-950/50 open:pb-0">
        <summary className="cursor-pointer px-4 py-3 text-sm text-slate-300">
          Demo schema (customers · orders · products)
        </summary>
        <pre className="overflow-x-auto border-t border-white/10 px-4 py-3 text-xs text-slate-400">
          {schema || "Loading schema…"}
        </pre>
      </details>
      <form onSubmit={onGenerate} className="mt-6 flex gap-3">
        <input
          className="flex-1 rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100 outline-none focus:border-teal-400"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
        >
          Run
        </button>
      </form>
      {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
      {sql && (
        <div className="mt-8 space-y-6">
          <section>
            <h2 className="text-sm uppercase tracking-wide text-slate-500">SQL</h2>
            <pre className="mt-2 rounded-md bg-slate-900/70 p-3 text-sm text-teal-200">{sql}</pre>
          </section>
          <section>
            <h2 className="text-sm uppercase tracking-wide text-slate-500">Explanation</h2>
            <p className="mt-2 line-clamp-6 text-slate-200">{explanation}</p>
          </section>
          <section>
            <h2 className="text-sm uppercase tracking-wide text-slate-500">Optimization</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-300">
              {suggestions.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </section>
          <section>
            <h2 className="text-sm uppercase tracking-wide text-slate-500">Results</h2>
            {rows.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">No rows returned.</p>
            ) : (
              <div className="mt-2 overflow-x-auto">
                <table className="min-w-full text-left text-sm text-slate-300">
                  <thead>
                    <tr>
                      {columns.map((c) => (
                        <th key={c} className="border-b border-white/10 px-3 py-2 text-teal-300">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, idx) => (
                      <tr key={idx}>
                        {columns.map((c) => (
                          <td key={c} className="border-b border-white/5 px-3 py-2">
                            {String(row[c] ?? "")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}
    </AppShell>
  );
}

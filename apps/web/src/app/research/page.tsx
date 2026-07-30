"use client";

import { FormEvent, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { AppShell } from "@/components/AppShell";
import { FeedbackButtons } from "@/components/FeedbackButtons";
import { API_BASE_URL, getAccessToken } from "@/lib/api";

type Citation = {
  filename?: string;
  page_number?: number | null;
  snippet?: string;
};

export default function ResearchPage() {
  const [question, setQuestion] = useState(
    "Summarize key themes in my uploaded documents",
  );
  const [family, setFamily] = useState("llama");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const token = getAccessToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/research`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ question, model_family: family }),
      });
      if (!response.ok) {
        let detail = `Research failed (${response.status})`;
        try {
          const body = await response.json();
          detail = body?.error?.message || body?.detail || detail;
        } catch {
          /* ignore */
        }
        throw new Error(detail);
      }
      setResult(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  const brief = String(result?.brief ?? "");
  const rag = (result?.rag ?? {}) as { answer?: string; citations?: Citation[] };
  const web = (result?.web_results ?? []) as Array<{
    title?: string;
    snippet?: string;
    url?: string;
  }>;
  const citations = rag.citations ?? [];

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Research</h1>
      <p className="mt-2 max-w-2xl text-slate-400">
        Combines your documents (RAG), knowledge graph, memory, and optional web
        leads into one research brief. Ask about content you have uploaded.
      </p>
      <form onSubmit={onSubmit} className="mt-6 space-y-3">
        <select
          className="rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
          value={family}
          onChange={(e) => setFamily(e.target.value)}
        >
          <option value="llama">Llama (Ollama)</option>
          <option value="gpt">GPT (OpenAI)</option>
          <option value="mistral">Mistral</option>
        </select>
        <div className="flex gap-3">
          <input
            className="flex-1 rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Research question…"
          />
          <button
            type="submit"
            disabled={busy}
            className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
          >
            {busy ? "Working…" : "Research"}
          </button>
        </div>
      </form>
      {error && <p className="mt-3 text-rose-300">{error}</p>}
      {!result && !error && (
        <p className="mt-8 text-sm text-slate-500">
          No brief yet. Run a question about your indexed documents to see results here.
        </p>
      )}
      {result && (
        <div className="mt-8 space-y-6">
          <section className="rounded-xl border border-white/10 bg-slate-950/40 p-5">
            <h2 className="text-sm uppercase tracking-wide text-slate-500">Brief</h2>
            <div className="prose prose-invert mt-3 max-w-none prose-p:text-slate-200">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{brief}</ReactMarkdown>
            </div>
            <div className="mt-2 text-xs text-slate-500">
              Model family: {String(result.model_family ?? family)}
              {result.memory_used ? " · memory used" : ""}
            </div>
            <FeedbackButtons targetType="research" answerSnapshot={brief} />
          </section>

          {citations.length > 0 && (
            <section>
              <h2 className="text-sm uppercase tracking-wide text-slate-500">
                Document citations
              </h2>
              <ul className="mt-3 space-y-2">
                {citations.map((c, i) => (
                  <li
                    key={`${c.filename}-${i}`}
                    className="rounded-md border border-white/10 px-3 py-2 text-sm text-slate-300"
                  >
                    <div className="text-teal-300">
                      {c.filename}
                      {c.page_number != null ? ` · p.${c.page_number}` : ""}
                    </div>
                    <div className="mt-1 text-slate-400">{c.snippet}</div>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {web.length > 0 && (
            <section>
              <h2 className="text-sm uppercase tracking-wide text-slate-500">
                Web leads (unverified)
              </h2>
              <ul className="mt-3 space-y-2 text-sm text-slate-400">
                {web.map((w, i) => (
                  <li key={i} className="rounded-md border border-white/10 px-3 py-2">
                    <div className="text-slate-200">{w.title}</div>
                    <div className="mt-1">{w.snippet}</div>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </AppShell>
  );
}

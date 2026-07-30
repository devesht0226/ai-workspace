"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { FeedbackButtons } from "@/components/FeedbackButtons";
import { api, Citation, DocumentItem } from "@/lib/api";

type Collection = { id: string; name: string; description?: string | null };

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [collectionId, setCollectionId] = useState<string>("");
  const [newCollection, setNewCollection] = useState("");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [evalMetrics, setEvalMetrics] = useState<Record<string, number> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const [list, cols] = await Promise.all([
      api.listDocuments(),
      api.listCollections().catch(() => []),
    ]);
    setDocs(list);
    setCollections(
      (cols as Array<Record<string, unknown>>).map((c) => ({
        id: String(c.id),
        name: String(c.name ?? "Collection"),
        description: (c.description as string | null) ?? null,
      })),
    );
    if (!activeId && list[0]) setActiveId(list[0].id);
  }

  useEffect(() => {
    refresh().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed to load documents"),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onUpload(file: File | null) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const doc = await api.uploadDocument(file, collectionId || undefined);
      await refresh();
      setActiveId(doc.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function onCreateCollection() {
    if (!newCollection.trim()) return;
    setBusy(true);
    try {
      const created = await api.createCollection(newCollection.trim());
      setNewCollection("");
      await refresh();
      setCollectionId(String(created.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Collection create failed");
    } finally {
      setBusy(false);
    }
  }

  async function onDeleteDoc(id: string) {
    if (!confirm("Delete this document?")) return;
    await api.deleteDocument(id);
    if (activeId === id) setActiveId(null);
    await refresh();
  }

  async function onAsk(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = activeId
        ? await api.queryDocument(activeId, question.trim())
        : await api.ragQuery(question.trim());
      setAnswer(result.answer);
      setCitations(result.citations);
      setEvalMetrics(result.eval_metrics ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setBusy(false);
    }
  }

  const active = docs.find((d) => d.id === activeId) ?? null;

  return (
    <AppShell>
      <div className="grid min-h-[70vh] grid-cols-1 gap-6 md:grid-cols-[280px_1fr]">
        <aside className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
          <label className="mb-3 block">
            <span className="mb-2 block text-sm text-slate-300">
              Upload (PDF, DOCX, PPTX, TXT, MD, HTML)
            </span>
            <input
              type="file"
              accept=".pdf,.docx,.pptx,.txt,.md,.html,.htm,application/pdf,text/plain,text/markdown,text/html"
              disabled={busy}
              onChange={(e) => onUpload(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-slate-300 file:mr-3 file:rounded-md file:border-0 file:bg-teal-400 file:px-3 file:py-1.5 file:font-semibold file:text-slate-950"
            />
          </label>

          <div className="mb-4 space-y-2 rounded-md border border-white/10 p-3">
            <div className="text-xs uppercase tracking-wide text-slate-500">Collections</div>
            <select
              className="w-full rounded-md border border-white/10 bg-slate-900/70 px-2 py-1.5 text-sm text-slate-100"
              value={collectionId}
              onChange={(e) => setCollectionId(e.target.value)}
            >
              <option value="">No collection</option>
              {collections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <div className="flex gap-2">
              <input
                className="flex-1 rounded-md border border-white/10 bg-slate-900/70 px-2 py-1.5 text-sm text-slate-100"
                placeholder="New collection"
                value={newCollection}
                onChange={(e) => setNewCollection(e.target.value)}
              />
              <button
                type="button"
                disabled={busy}
                onClick={() => onCreateCollection().catch(console.error)}
                className="rounded-md bg-white/10 px-2 py-1 text-xs text-teal-200"
              >
                Add
              </button>
            </div>
          </div>

          <ul className="space-y-1">
            {docs.map((doc) => (
              <li key={doc.id} className="group flex items-start gap-1">
                <button
                  type="button"
                  onClick={() => setActiveId(doc.id)}
                  className={`min-w-0 flex-1 rounded-md px-3 py-2 text-left text-sm ${
                    activeId === doc.id
                      ? "bg-white/10 text-white"
                      : "text-slate-300 hover:bg-white/5"
                  }`}
                >
                  <div className="truncate">{doc.filename}</div>
                  <div className="text-xs text-slate-500">{doc.status}</div>
                </button>
                <button
                  type="button"
                  title="Delete"
                  className="mt-2 text-xs text-rose-300 opacity-70 hover:opacity-100"
                  onClick={() =>
                    onDeleteDoc(doc.id).catch((err) =>
                      setError(err instanceof Error ? err.message : "Delete failed"),
                    )
                  }
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="rounded-xl border border-white/10 bg-slate-950/40 p-5">
          <h2 className="font-display text-2xl text-white">
            Ask about {active?.filename ?? "your documents"}
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Answers are grounded in retrieved chunks with citations (multi-format RAG).
          </p>
          <form onSubmit={onAsk} className="mt-6 flex gap-3">
            <input
              className="flex-1 rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100 outline-none focus:border-teal-400"
              placeholder="Ask about this document…"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={busy}
            />
            <button
              type="submit"
              disabled={busy}
              className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
            >
              Ask
            </button>
          </form>
          {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
          {answer && (
            <div className="mt-6 space-y-4">
              <p className="whitespace-pre-wrap text-slate-200">{answer}</p>
              <FeedbackButtons targetType="rag" answerSnapshot={answer} />
              {evalMetrics && (
                <div>
                  <h3 className="text-sm uppercase tracking-wide text-slate-500">
                    Eval metrics
                  </h3>
                  <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {Object.entries(evalMetrics).map(([key, value]) => (
                      <div
                        key={key}
                        className="rounded-md border border-white/10 px-3 py-2"
                      >
                        <div className="text-[10px] uppercase tracking-wide text-slate-500">
                          {key.replaceAll("_", " ")}
                        </div>
                        <div className="text-teal-300">
                          {typeof value === "number" ? value.toFixed(3) : String(value)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <h3 className="text-sm uppercase tracking-wide text-slate-500">Citations</h3>
              <ul className="space-y-2 text-sm text-slate-300">
                {citations.map((c) => (
                  <li key={c.chunk_id} className="rounded-md border border-white/10 p-3">
                    <div className="text-teal-300">
                      {c.filename}
                      {c.page_number != null ? ` · p.${c.page_number}` : ""}
                    </div>
                    <div className="mt-1 text-slate-400">{c.snippet}</div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}

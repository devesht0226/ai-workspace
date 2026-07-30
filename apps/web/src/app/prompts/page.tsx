"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<Array<Record<string, unknown>>>([]);
  const [name, setName] = useState("rag_grounded");
  const [content, setContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const data = await api.listPrompts();
    setPrompts(data.prompts);
  }

  useEffect(() => {
    refresh().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed to load prompts"),
    );
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await api.createPrompt({ name, content });
      setContent("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    }
  }

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Prompts</h1>
      <p className="mt-2 text-slate-400">
        Versioned prompt templates (for example RAG grounding). Publishing creates a new
        active version.
      </p>
      <form onSubmit={onCreate} className="mt-6 space-y-3">
        <input
          className="w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Prompt name"
        />
        <textarea
          className="h-28 w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="New prompt version content"
          required
        />
        <button
          type="submit"
          className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950"
        >
          Publish version
        </button>
      </form>
      {error && <p className="mt-3 text-rose-300">{error}</p>}
      <ul className="mt-8 space-y-3">
        {prompts.length === 0 && (
          <li className="text-sm text-slate-500">
            No prompts in the registry yet. Publish a version above.
          </li>
        )}
        {prompts.map((p) => (
          <li
            key={String(p.id)}
            className="rounded-lg border border-white/10 bg-slate-950/40 px-4 py-3"
          >
            <div className="flex items-center gap-3 text-sm text-white">
              <span className="font-medium">{String(p.name)}</span>
              <span className="text-slate-500">v{String(p.version)}</span>
              {p.is_active ? (
                <span className="text-teal-300">active</span>
              ) : (
                <span className="text-slate-600">inactive</span>
              )}
            </div>
            <p className="mt-2 line-clamp-4 whitespace-pre-wrap text-xs text-slate-400">
              {String(p.content)}
            </p>
          </li>
        ))}
      </ul>
    </AppShell>
  );
}

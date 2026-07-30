"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { API_BASE_URL, getAccessToken } from "@/lib/api";

type GraphNode = {
  id?: string;
  name?: string;
  type?: string;
  label?: string;
};
type GraphEdge = {
  source?: string;
  target?: string;
  relation?: string;
};
type ModelRow = {
  family?: string;
  provider?: string;
  model?: string;
  available?: boolean;
};

export default function GraphPage() {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [models, setModels] = useState<ModelRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const token = getAccessToken();
        const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};
        const [g, m] = await Promise.all([
          fetch(`${API_BASE_URL}/api/v1/knowledge-graph`, { headers }),
          fetch(`${API_BASE_URL}/api/v1/models/catalog`, { headers }),
        ]);
        if (!g.ok || !m.ok) throw new Error("Failed to load graph or model catalog");
        const graph = await g.json();
        const catalog = await m.json();
        setNodes((graph.nodes as GraphNode[]) || []);
        setEdges((graph.edges as GraphEdge[]) || []);
        const list = (catalog.models as ModelRow[]) || (catalog as ModelRow[]) || [];
        setModels(Array.isArray(list) ? list : []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Load failed");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Graph</h1>
      <p className="mt-2 max-w-2xl text-slate-400">
        Entities and relations extracted from your documents, plus which AI model
        families are configured on this workspace.
      </p>
      {error && <p className="mt-3 text-rose-300">{error}</p>}
      {loading && <p className="mt-6 text-slate-500">Loading graph…</p>}

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-white/10 bg-slate-950/40 p-5">
          <h2 className="text-sm uppercase tracking-wide text-slate-500">
            Knowledge graph
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            {nodes.length} nodes · {edges.length} edges
          </p>
          {nodes.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500">
              No entities yet. Upload and index documents to build the graph.
            </p>
          ) : (
            <ul className="mt-4 max-h-[420px] space-y-2 overflow-auto">
              {nodes.slice(0, 40).map((n) => (
                <li
                  key={String(n.id ?? n.name)}
                  className="rounded-md border border-white/10 px-3 py-2 text-sm"
                >
                  <span className="text-white">{n.name ?? n.label ?? "node"}</span>
                  <span className="ml-2 text-xs text-teal-300/80">
                    {n.type ?? "entity"}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {edges.length > 0 && (
            <p className="mt-4 text-xs text-slate-500">
              Sample relations:{" "}
              {edges
                .slice(0, 5)
                .map((e) => e.relation || "related")
                .join(", ")}
            </p>
          )}
        </section>

        <section className="rounded-xl border border-white/10 bg-slate-950/40 p-5">
          <h2 className="text-sm uppercase tracking-wide text-slate-500">
            Model router
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Available backends for chat, research, and benchmarks.
          </p>
          <ul className="mt-4 space-y-2">
            {models.length === 0 && (
              <li className="text-sm text-slate-500">No catalog entries returned.</li>
            )}
            {models.map((row) => (
              <li
                key={`${row.family}-${row.model}`}
                className="flex items-center justify-between rounded-md border border-white/10 px-3 py-2 text-sm"
              >
                <div>
                  <div className="text-white">{row.family ?? "model"}</div>
                  <div className="text-xs text-slate-500">
                    {row.provider} · {row.model}
                  </div>
                </div>
                <span
                  className={
                    row.available ? "text-xs text-teal-300" : "text-xs text-slate-500"
                  }
                >
                  {row.available ? "available" : "not configured"}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </AppShell>
  );
}

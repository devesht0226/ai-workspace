"use client";

import { FormEvent, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { EmptyState, PageHeader, Panel, SectionLabel } from "@/components/ui";
import { api } from "@/lib/api";

export default function ResumePage() {
  const [jd, setJd] = useState(
    "Python FastAPI engineer with Docker, PostgreSQL, and React experience.",
  );
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem("resume") as HTMLInputElement;
    const file = fileInput.files?.[0];
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const analysis = await api.analyzeResume(file, jd);
      setResult(analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analyze failed");
    } finally {
      setBusy(false);
    }
  }

  const payload = (result?.result_json ?? null) as Record<string, unknown> | null;
  const ats = (payload?.ats ?? {}) as { score?: number; checks?: Record<string, boolean> };
  const jobMatch = (payload?.job_match ?? {}) as {
    matched_skills?: string[];
    missing_skills?: string[];
    score?: number | null;
  };
  const skills = (payload?.skills as string[]) || [];
  const suggestions = (payload?.suggestions as string[]) || [];
  const cover = String(payload?.cover_letter ?? payload?.cover_letter_draft ?? "");

  return (
    <AppShell>
      <PageHeader
        title="Resume"
        description="Upload a resume and paste a job description for ATS-style checks, skill match, and improvement tips."
      />
      <form onSubmit={onSubmit} className="space-y-4">
        <textarea
          className="h-28 w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100 outline-none focus:border-teal-400"
          value={jd}
          onChange={(e) => setJd(e.target.value)}
          placeholder="Paste job description"
        />
        <input
          name="resume"
          type="file"
          accept=".pdf,.txt,.md"
          required
          className="block text-sm text-slate-300 file:mr-3 file:rounded-md file:border-0 file:bg-teal-400 file:px-3 file:py-1.5 file:font-semibold file:text-slate-950"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
        >
          {busy ? "Analyzing…" : "Analyze"}
        </button>
      </form>
      {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
      {!payload && !error && (
        <div className="mt-8">
          <EmptyState>
            Choose a PDF/TXT resume and run Analyze to see ATS score, matched skills, and
            suggestions.
          </EmptyState>
        </div>
      )}
      {payload && (
        <div className="mt-8 space-y-4">
          <Panel>
            <p className="text-slate-200">{String(payload.summary ?? "")}</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-white/10 px-4 py-3">
                <div className="text-xs uppercase tracking-wide text-slate-500">ATS score</div>
                <div className="mt-1 font-display text-3xl text-teal-300">
                  {ats.score ?? "—"}
                </div>
              </div>
              <div className="rounded-lg border border-white/10 px-4 py-3">
                <div className="text-xs uppercase tracking-wide text-slate-500">Job match</div>
                <div className="mt-1 font-display text-3xl text-teal-300">
                  {jobMatch.score != null ? jobMatch.score : "—"}
                </div>
              </div>
            </div>
          </Panel>

          {ats.checks && (
            <Panel>
              <SectionLabel>ATS checks</SectionLabel>
              <ul className="mt-3 grid gap-2 sm:grid-cols-2 text-sm">
                {Object.entries(ats.checks).map(([key, ok]) => (
                  <li key={key} className="rounded border border-white/10 px-3 py-2">
                    <span className={ok ? "text-teal-300" : "text-rose-300"}>
                      {ok ? "✓" : "×"}
                    </span>{" "}
                    <span className="text-slate-300">{key.replaceAll("_", " ")}</span>
                  </li>
                ))}
              </ul>
            </Panel>
          )}

          <Panel>
            <SectionLabel>Skills found</SectionLabel>
            <p className="mt-2 text-slate-300">
              {skills.length ? skills.join(", ") : "None detected"}
            </p>
            {(jobMatch.matched_skills?.length || jobMatch.missing_skills?.length) && (
              <div className="mt-4 grid gap-4 sm:grid-cols-2 text-sm">
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Matched</div>
                  <p className="mt-1 text-teal-200">
                    {(jobMatch.matched_skills || []).join(", ") || "—"}
                  </p>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-slate-500">Missing</div>
                  <p className="mt-1 text-rose-200/90">
                    {(jobMatch.missing_skills || []).join(", ") || "—"}
                  </p>
                </div>
              </div>
            )}
          </Panel>

          {suggestions.length > 0 && (
            <Panel>
              <SectionLabel>Suggestions</SectionLabel>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-300">
                {suggestions.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </Panel>
          )}

          {cover && (
            <Panel>
              <SectionLabel>Cover letter draft</SectionLabel>
              <p className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{cover}</p>
            </Panel>
          )}
        </div>
      )}
    </AppShell>
  );
}

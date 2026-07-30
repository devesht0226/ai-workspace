"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function MeetingsPage() {
  const [transcript, setTranscript] = useState(
    "Speaker A: Welcome to planning.\nAction item — ship the SQL assistant by Friday.\nSpeaker B: Follow up with design on dashboard.",
  );
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [meetings, setMeetings] = useState<Array<Record<string, unknown>>>([]);
  const [active, setActive] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setMeetings(await api.listMeetings());
  }

  useEffect(() => {
    refresh().catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const meeting = await api.createMeeting({
        title: audioFile ? `Audio: ${audioFile.name}` : "Planning notes",
        transcript: audioFile ? undefined : transcript,
        file: audioFile ?? undefined,
      });
      setActive(meeting);
      setAudioFile(null);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Meeting Notes</h1>
      <p className="mt-2 text-slate-400">
        Paste a meeting transcript (recommended for demos) or upload a text/audio file.
        The assistant returns a summary, action items, and decisions.
      </p>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <label className="block text-sm text-slate-300">
          Optional audio / transcript file
          <input
            type="file"
            accept="audio/*,.txt,.md,.vtt,.srt"
            className="mt-2 block w-full text-sm text-slate-300 file:mr-3 file:rounded-md file:border-0 file:bg-teal-400 file:px-3 file:py-1.5 file:font-semibold file:text-slate-950"
            onChange={(e) => setAudioFile(e.target.files?.[0] ?? null)}
          />
        </label>
        {!audioFile && (
          <textarea
            className="h-40 w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100 outline-none focus:border-teal-400"
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
          />
        )}
        {audioFile && (
          <p className="text-sm text-teal-200">Selected: {audioFile.name}</p>
        )}
        <button
          type="submit"
          disabled={busy || (!audioFile && !transcript.trim())}
          className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
        >
          Process notes
        </button>
      </form>
      {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
      <div className="mt-8 grid gap-6 md:grid-cols-[220px_1fr]">
        <ul className="space-y-2">
          {meetings.length === 0 && (
            <li className="text-sm text-slate-500">No meetings yet. Process notes above.</li>
          )}
          {meetings.map((m) => (
            <li key={String(m.id)}>
              <button
                type="button"
                className="w-full rounded-md border border-white/10 px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5"
                onClick={() => setActive(m)}
              >
                {String(m.title)}
              </button>
            </li>
          ))}
        </ul>
        {active && (
          <div className="space-y-4 rounded-xl border border-white/10 bg-slate-950/40 p-5">
            <h2 className="text-sm uppercase tracking-wide text-slate-500">Summary</h2>
            <p className="text-slate-200">{String(active.summary ?? "")}</p>
            <h2 className="text-sm uppercase tracking-wide text-slate-500">Action items</h2>
            <ul className="list-disc space-y-1 pl-5 text-slate-300">
              {((active.action_items_json as Array<{ text: string }>) || []).map((item) => (
                <li key={item.text}>{item.text}</li>
              ))}
            </ul>
            {Array.isArray(active.decisions_json) &&
              (active.decisions_json as unknown[]).length > 0 && (
                <>
                  <h2 className="text-sm uppercase tracking-wide text-slate-500">Decisions</h2>
                  <ul className="list-disc space-y-1 pl-5 text-slate-300">
                    {(active.decisions_json as Array<{ text?: string } | string>).map(
                      (item, i) => (
                        <li key={i}>
                          {typeof item === "string" ? item : String(item.text ?? item)}
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

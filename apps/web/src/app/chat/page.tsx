"use client";

import { FormEvent, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { AppShell } from "@/components/AppShell";
import { FeedbackButtons } from "@/components/FeedbackButtons";
import { api, ChatDetail, ChatSession } from "@/lib/api";

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ChatDetail | null>(null);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshSessions(selectId?: string) {
    const list = await api.listChats();
    setSessions(list);
    const nextId = selectId ?? activeId ?? list[0]?.id ?? null;
    setActiveId(nextId);
    if (nextId) {
      // Load list first so sidebar appears; detail follows
      void api
        .getChat(nextId)
        .then(setDetail)
        .catch((err) =>
          setError(err instanceof Error ? err.message : "Failed to load chat"),
        );
    } else {
      setDetail(null);
    }
  }

  useEffect(() => {
    refreshSessions().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed to load chats"),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createChat() {
    const created = await api.createChat();
    await refreshSessions(created.id);
  }

  async function renameActive() {
    if (!activeId) return;
    const title = prompt("Rename chat", detail?.title ?? "Chat");
    if (!title) return;
    await api.renameChat(activeId, title);
    await refreshSessions(activeId);
  }

  async function deleteActive() {
    if (!activeId) return;
    if (!confirm("Delete this chat permanently?")) return;
    await api.deleteChat(activeId);
    setActiveId(null);
    setDetail(null);
    await refreshSessions();
  }

  async function exportActive() {
    if (!activeId) return;
    const markdown = await api.exportChat(activeId);
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(detail?.title || "chat").replace(/[^\w\-]+/g, "_")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function onSend(event: FormEvent) {
    event.preventDefault();
    if (!activeId || !input.trim() || busy) return;
    const content = input.trim();
    setInput("");
    setBusy(true);
    setStreaming("");
    setError(null);
    try {
      await api.sendMessage(activeId, content, (token) => {
        setStreaming((prev) => prev + token);
      });
      setStreaming("");
      await refreshSessions(activeId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Send failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <div className="grid min-h-[70vh] grid-cols-1 gap-6 md:grid-cols-[240px_1fr]">
        <aside className="rounded-xl border border-white/10 bg-slate-950/40 p-4">
          <button
            type="button"
            onClick={() => createChat().catch(console.error)}
            className="mb-4 w-full rounded-md bg-teal-400/90 px-3 py-2 text-sm font-semibold text-slate-950"
          >
            New chat
          </button>
          <ul className="space-y-1">
            {sessions.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => {
                    setActiveId(session.id);
                    api.getChat(session.id).then(setDetail).catch(console.error);
                  }}
                  className={`w-full truncate rounded-md px-3 py-2 text-left text-sm ${
                    activeId === session.id
                      ? "bg-white/10 text-white"
                      : "text-slate-300 hover:bg-white/5"
                  }`}
                >
                  {session.title}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="flex flex-col rounded-xl border border-white/10 bg-slate-950/40">
          <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
            <div className="font-medium text-white">
              {detail?.title ?? "Select or create a chat"}
            </div>
            {activeId && (
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => renameActive().catch(console.error)}
                  className="text-xs text-teal-300"
                >
                  Rename
                </button>
                <button
                  type="button"
                  onClick={() => exportActive().catch(console.error)}
                  className="text-xs text-teal-300"
                >
                  Export
                </button>
                <button
                  type="button"
                  onClick={() =>
                    deleteActive().catch((err) =>
                      setError(err instanceof Error ? err.message : "Delete failed"),
                    )
                  }
                  className="text-xs text-rose-300"
                >
                  Delete
                </button>
              </div>
            )}
          </div>
          <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
            {detail?.messages.map((message) => (
              <div
                key={message.id}
                className={
                  message.role === "user" ? "text-teal-200" : "text-slate-200"
                }
              >
                <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">
                  {message.role}
                </div>
                {message.role === "assistant" ? (
                  <div className="prose prose-invert max-w-none prose-pre:bg-slate-900 prose-code:text-teal-200">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                )}
                {message.role === "assistant" && (
                  <FeedbackButtons
                    targetType="chat"
                    targetId={message.id}
                    answerSnapshot={message.content}
                  />
                )}
              </div>
            ))}
            {streaming && (
              <div className="text-slate-200">
                <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">
                  assistant
                </div>
                <div className="prose prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{streaming}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>
          <form onSubmit={onSend} className="border-t border-white/10 p-4">
            {error && <p className="mb-2 text-sm text-rose-300">{error}</p>}
            <div className="flex gap-3">
              <input
                className="flex-1 rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100 outline-none focus:border-teal-400"
                placeholder="Message AI Workspace…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={!activeId || busy}
              />
              <button
                type="submit"
                disabled={!activeId || busy}
                className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
              >
                Send
              </button>
            </div>
          </form>
        </section>
      </div>
    </AppShell>
  );
}

"use client";

import { useState } from "react";
import { api } from "@/lib/api";

type Props = {
  targetType: string;
  targetId?: string;
  answerSnapshot?: string;
};

export function FeedbackButtons({ targetType, targetId, answerSnapshot }: Props) {
  const [sent, setSent] = useState<"good" | "bad" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function rate(rating: 1 | -1) {
    setError(null);
    try {
      await api.submitFeedback({
        target_type: targetType,
        rating,
        target_id: targetId,
        answer_snapshot: answerSnapshot,
      });
      setSent(rating === 1 ? "good" : "bad");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feedback failed");
    }
  }

  if (sent) {
    return (
      <p className="mt-2 text-xs text-slate-400">
        Thanks — marked as {sent === "good" ? "helpful" : "not helpful"}.
      </p>
    );
  }

  return (
    <div className="mt-2 flex items-center gap-2">
      <span className="text-xs text-slate-500">Was this helpful?</span>
      <button
        type="button"
        onClick={() => rate(1)}
        className="rounded border border-white/10 px-2 py-0.5 text-xs text-teal-300 hover:bg-white/5"
        aria-label="Good"
      >
        Good
      </button>
      <button
        type="button"
        onClick={() => rate(-1)}
        className="rounded border border-white/10 px-2 py-0.5 text-xs text-rose-300 hover:bg-white/5"
        aria-label="Bad"
      >
        Bad
      </button>
      {error && <span className="text-xs text-rose-300">{error}</span>}
    </div>
  );
}

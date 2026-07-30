"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { api } from "@/lib/api";

export default function ResetPasswordPage() {
  const token = useMemo(() => {
    if (typeof window === "undefined") return "";
    return new URLSearchParams(window.location.search).get("token") ?? "";
  }, []);
  const [value, setValue] = useState(token);
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await api.confirmPasswordReset(value, password);
      setMessage("Password updated. You can sign in.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <Link href="/" className="font-display text-3xl text-white">
        AI Workspace
      </Link>
      <h1 className="mt-6 text-xl text-white">Reset password</h1>
      <form onSubmit={onSubmit} className="mt-4 space-y-4">
        <input
          className="w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Reset token"
          required
        />
        <input
          className="w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
          type="password"
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="New password"
          required
        />
        <button type="submit" className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950">
          Update password
        </button>
      </form>
      {message && <p className="mt-3 text-teal-300">{message}</p>}
      {error && <p className="mt-3 text-rose-300">{error}</p>}
      <Link href="/login" className="mt-6 text-sm text-slate-400 hover:text-teal-300">
        Back to login
      </Link>
    </main>
  );
}

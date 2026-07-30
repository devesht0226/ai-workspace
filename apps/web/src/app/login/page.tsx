"use client";

import Link from "next/link";
import { FormEvent, Suspense, useState } from "react";
import { api, setTokens } from "@/lib/api";
import { useRouter, useSearchParams } from "next/navigation";

type Mode = "login" | "register" | "forgot";

function LoginForm() {
  const router = useRouter();
  const search = useSearchParams();
  const reason = search.get("reason");
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [message, setMessage] = useState<string | null>(
    reason === "expired" || reason === "session"
      ? "Please sign in again to continue."
      : null,
  );
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      if (mode === "forgot") {
        await api.requestPasswordReset(email);
        setMessage("If that email exists, a reset link was written to the mail dump / SMTP.");
        return;
      }
      if (mode === "register") {
        await api.register({
          email,
          password,
          full_name: fullName || undefined,
        });
        setMessage("Account created — signing you in…");
      }
      const tokens = await api.login({ email, password });
      setTokens(tokens);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <Link href="/" className="font-display text-3xl text-white">
        AI Workspace
      </Link>
      <p className="mt-2 text-slate-400">
        {mode === "login" && "Sign in to your AI knowledge platform."}
        {mode === "register" && "Create an account for chat, documents, SQL, and agents."}
        {mode === "forgot" && "We will send a password reset link if the email exists."}
      </p>
      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        {mode === "register" && (
          <input
            className="w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100 outline-none focus:border-teal-400"
            placeholder="Full name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        )}
        <input
          className="w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100 outline-none focus:border-teal-400"
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        {mode !== "forgot" && (
          <input
            className="w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100 outline-none focus:border-teal-400"
            type="password"
            required
            minLength={8}
            placeholder="Password (min 8 characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        )}
        {error && <p className="text-sm text-rose-300">{error}</p>}
        {message && <p className="text-sm text-teal-300">{message}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-teal-400 px-4 py-2.5 font-semibold text-slate-950 hover:bg-teal-300 disabled:opacity-60"
        >
          {loading
            ? "Please wait…"
            : mode === "forgot"
              ? "Send reset link"
              : mode === "login"
                ? "Continue"
                : "Register"}
        </button>
      </form>
      <div className="mt-6 space-y-2 text-sm text-slate-400">
        {mode === "login" && (
          <>
            <button
              type="button"
              className="block hover:text-teal-300"
              onClick={() => setMode("register")}
            >
              Need an account? Register
            </button>
            <button
              type="button"
              className="block hover:text-teal-300"
              onClick={() => setMode("forgot")}
            >
              Forgot password?
            </button>
          </>
        )}
        {mode !== "login" && (
          <button
            type="button"
            className="block hover:text-teal-300"
            onClick={() => setMode("login")}
          >
            Back to sign in
          </button>
        )}
      </div>
      <p className="mt-8 text-xs text-slate-500">
        Tip: keep the API running on port 8000 while you use the app.
      </p>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-slate-400">
          Loading…
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}

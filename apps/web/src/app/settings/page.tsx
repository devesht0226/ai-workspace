"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api, clearTokens, UserPublic } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserPublic | null>(null);
  const [fullName, setFullName] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [sessions, setSessions] = useState<Array<Record<string, unknown>>>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.me(), api.listSessions()])
      .then(([me, s]) => {
        setUser(me);
        setFullName(me.full_name ?? "");
        setSessions(s.sessions);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, []);

  async function save() {
    setError(null);
    try {
      const updated = await api.updateProfile(fullName);
      setUser(updated);
      setMessage("Profile updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  async function onChangePassword() {
    setError(null);
    try {
      await api.changePassword(currentPassword, newPassword);
      setMessage("Password changed. Please sign in again.");
      clearTokens();
      router.push("/login?reason=expired");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password change failed");
    }
  }

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Settings</h1>
      <p className="mt-2 text-slate-400">
        Profile, password, sessions, and GDPR account deletion.
      </p>
      {user ? (
        <div className="mt-8 max-w-lg space-y-8">
          <section className="space-y-4 rounded-xl border border-white/10 bg-slate-950/40 p-5">
            <div className="text-sm text-slate-400">Email</div>
            <div className="text-slate-100">{user.email}</div>
            <div className="text-sm text-slate-400">
              Verified:{" "}
              <span className="text-teal-300">{user.email_verified ? "yes" : "no"}</span>
            </div>
            <div className="text-sm text-slate-400">Role: {user.role}</div>
            <label className="block text-sm text-slate-400">
              Full name
              <input
                className="mt-1 w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </label>
            <button
              type="button"
              onClick={() => save()}
              className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950"
            >
              Save profile
            </button>
          </section>

          <section className="space-y-3 rounded-xl border border-white/10 bg-slate-950/40 p-5">
            <h2 className="text-white">Change password</h2>
            <input
              type="password"
              placeholder="Current password"
              className="w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
            <input
              type="password"
              placeholder="New password"
              className="w-full rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <button
              type="button"
              onClick={() => onChangePassword()}
              className="rounded-md border border-white/10 px-4 py-2 text-teal-300"
            >
              Update password
            </button>
          </section>

          <section className="space-y-3 rounded-xl border border-white/10 bg-slate-950/40 p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-white">Active sessions</h2>
              <button
                type="button"
                className="text-xs text-rose-300"
                onClick={() =>
                  api
                    .logoutAll()
                    .then(() => {
                      clearTokens();
                      router.push("/login");
                    })
                    .catch(console.error)
                }
              >
                Logout all devices
              </button>
            </div>
            <ul className="space-y-2 text-sm text-slate-400">
              {sessions.map((s) => (
                <li
                  key={String(s.id)}
                  className="flex items-center justify-between rounded border border-white/10 px-3 py-2"
                >
                  <span>{String(s.created_at)}</span>
                  <button
                    type="button"
                    className="text-xs text-rose-300"
                    onClick={() =>
                      api
                        .revokeSession(String(s.id))
                        .then(() => api.listSessions())
                        .then((r) => setSessions(r.sessions))
                        .catch(console.error)
                    }
                  >
                    Revoke
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-xl border border-rose-400/30 bg-rose-950/20 p-5">
            <h2 className="text-rose-200">Privacy (GDPR)</h2>
            <p className="mt-2 text-sm text-slate-400">
              Export a portable copy of your workspace data, or permanently delete your account.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                className="rounded-md border border-white/20 px-4 py-2 text-sm text-teal-200"
                onClick={() => {
                  api
                    .exportMyData()
                    .then((data) => {
                      const blob = new Blob([JSON.stringify(data, null, 2)], {
                        type: "application/json",
                      });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = "ai-workspace-export.json";
                      a.click();
                      URL.revokeObjectURL(url);
                      setMessage("Data export downloaded.");
                    })
                    .catch((err) =>
                      setError(err instanceof Error ? err.message : "Export failed"),
                    );
                }}
              >
                Export my data
              </button>
              <button
                type="button"
                className="rounded-md bg-rose-500 px-4 py-2 font-semibold text-white"
                onClick={() => {
                  if (!confirm("Delete your account permanently?")) return;
                  api
                    .deleteAccount()
                    .then(() => {
                      clearTokens();
                      router.push("/");
                    })
                    .catch((err) =>
                      setError(err instanceof Error ? err.message : "Delete failed"),
                    );
                }}
              >
                Delete my account
              </button>
            </div>
          </section>

          {message && <p className="text-sm text-teal-300">{message}</p>}
          {error && <p className="text-sm text-rose-300">{error}</p>}
        </div>
      ) : (
        <p className="mt-8 text-slate-500">Loading settings…</p>
      )}
    </AppShell>
  );
}

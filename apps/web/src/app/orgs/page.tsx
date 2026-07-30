"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

export default function OrgsPage() {
  const [orgs, setOrgs] = useState<Array<Record<string, unknown>>>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [members, setMembers] = useState<Array<Record<string, unknown>>>([]);
  const [name, setName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const data = await api.listOrgs();
    setOrgs(data.organizations);
    if (!selected && data.organizations[0]) {
      const id = String(data.organizations[0].id);
      setSelected(id);
      const m = await api.listOrgMembers(id);
      setMembers(m.members);
    }
  }

  useEffect(() => {
    refresh().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed"),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    await api.createOrg(name);
    setName("");
    await refresh();
  }

  async function onInvite(e: FormEvent) {
    e.preventDefault();
    if (!selected) return;
    await api.inviteOrgMember(selected, inviteEmail);
    setInviteEmail("");
    const m = await api.listOrgMembers(selected);
    setMembers(m.members);
  }

  return (
    <AppShell>
      <h1 className="font-display text-3xl text-white">Orgs</h1>
      <p className="mt-2 text-slate-400">
        Multi-tenant organizations and members. Invite users who already have an account.
      </p>
      {error && <p className="mt-3 text-rose-300">{error}</p>}
      <form
        onSubmit={(e) =>
          onCreate(e).catch((err) =>
            setError(err instanceof Error ? err.message : "Create failed"),
          )
        }
        className="mt-6 flex gap-3"
      >
        <input
          className="flex-1 rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-slate-100"
          placeholder="New organization name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <button
          type="submit"
          className="rounded-md bg-teal-400 px-4 py-2 font-semibold text-slate-950"
        >
          Create
        </button>
      </form>
      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <ul className="space-y-2">
          {orgs.length === 0 && (
            <li className="text-sm text-slate-500">
              No organizations yet. Create one with the form above.
            </li>
          )}
          {orgs.map((o) => (
            <li key={String(o.id)}>
              <button
                type="button"
                className="w-full rounded-lg border border-white/10 bg-slate-950/40 px-4 py-3 text-left hover:border-teal-400/40"
                onClick={async () => {
                  const id = String(o.id);
                  setSelected(id);
                  setMembers((await api.listOrgMembers(id)).members);
                }}
              >
                <div className="text-white">{String(o.name)}</div>
                <div className="text-xs text-slate-500">
                  {String(o.role)} · {String(o.slug)}
                </div>
              </button>
            </li>
          ))}
        </ul>
        <div>
          {!selected ? (
            <p className="text-sm text-slate-500">Select an organization to manage members.</p>
          ) : (
            <>
          <h2 className="text-lg text-white">Members</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-300">
            {members.length === 0 && (
              <li className="text-slate-500">No members listed yet.</li>
            )}
            {members.map((m) => (
              <li key={String(m.user_id)} className="rounded border border-white/10 px-3 py-2">
                {String(m.email)} · {String(m.role)}
              </li>
            ))}
          </ul>
          <form
            onSubmit={(e) =>
              onInvite(e).catch((err) =>
                setError(err instanceof Error ? err.message : "Invite failed"),
              )
            }
            className="mt-4 flex gap-2"
          >
            <input
              className="flex-1 rounded-md border border-white/10 bg-slate-900/70 px-3 py-2 text-sm text-slate-100"
              placeholder="Invite email"
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              required
            />
            <button
              type="submit"
              className="rounded-md bg-teal-400 px-3 py-2 text-sm font-semibold text-slate-950"
            >
              Invite
            </button>
          </form>
            </>
          )}
        </div>
      </div>
    </AppShell>
  );
}

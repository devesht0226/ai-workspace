"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AuthError, api, clearTokens, getAccessToken } from "@/lib/api";
import { useEffect, useLayoutEffect, useState } from "react";

type NavLink = { href: string; label: string };

const primary: NavLink[] = [
  { href: "/dashboard", label: "Home" },
  { href: "/chat", label: "Chat" },
  { href: "/documents", label: "Documents" },
  { href: "/sql", label: "SQL" },
  { href: "/agents", label: "Agents" },
];

const assistants: NavLink[] = [
  { href: "/code", label: "Code" },
  { href: "/resume", label: "Resume" },
  { href: "/meetings", label: "Meetings" },
  { href: "/research", label: "Research" },
];

const platform: NavLink[] = [
  { href: "/graph", label: "Graph" },
  { href: "/observability", label: "Traces" },
  { href: "/eval", label: "Eval" },
  { href: "/prompts", label: "Prompts" },
  { href: "/benchmark", label: "Benchmark" },
  { href: "/orgs", label: "Orgs" },
];

function NavItem({
  link,
  active,
  badge,
}: {
  link: NavLink;
  active: boolean;
  badge?: string;
}) {
  return (
    <Link
      href={link.href}
      className={
        active
          ? "rounded-md bg-teal-400/10 px-2.5 py-1 text-teal-300"
          : "rounded-md px-2.5 py-1 text-slate-300 hover:bg-white/5 hover:text-white"
      }
    >
      {link.label}
      {badge ? ` ${badge}` : ""}
    </Link>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [unread, setUnread] = useState(0);
  const [isAdmin, setIsAdmin] = useState(false);

  useLayoutEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login?reason=session");
      return;
    }
    setReady(true);
  }, [router]);

  useEffect(() => {
    if (!ready) return;
    api
      .me()
      .then((me) => setIsAdmin(me.role === "admin"))
      .catch(() => undefined);
    api
      .listNotifications()
      .then((n) => setUnread(n.unread))
      .catch(() => undefined);
  }, [ready]);

  useEffect(() => {
    function onUnhandled(event: PromiseRejectionEvent) {
      if (event.reason instanceof AuthError) {
        clearTokens();
        router.replace("/login?reason=expired");
      }
    }
    window.addEventListener("unhandledrejection", onUnhandled);
    return () => window.removeEventListener("unhandledrejection", onUnhandled);
  }, [router]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-400">
        Loading workspace…
      </div>
    );
  }

  const isActive = (href: string) =>
    href === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(href);

  const platformLinks = [
    ...platform,
    ...(isAdmin ? [{ href: "/admin", label: "Admin" }] : []),
  ];

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/10 bg-slate-950/50 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
          <Link href="/dashboard" className="font-display text-xl text-white">
            AI Workspace
          </Link>
          <div className="flex items-center gap-1 text-sm">
            <NavItem
              link={{ href: "/notifications", label: "Alerts" }}
              active={isActive("/notifications")}
              badge={unread > 0 ? `(${unread})` : undefined}
            />
            <NavItem
              link={{ href: "/settings", label: "Settings" }}
              active={isActive("/settings")}
            />
            <button
              type="button"
              className="rounded-md px-2.5 py-1 text-slate-400 hover:bg-white/5 hover:text-white"
              onClick={() => {
                clearTokens();
                router.push("/login");
              }}
            >
              Logout
            </button>
          </div>
        </div>

        <div className="border-t border-white/5">
          <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-2.5 text-sm">
            <nav className="flex flex-wrap items-center gap-1">
              <span className="mr-1 text-[10px] font-medium uppercase tracking-wider text-slate-600">
                Core
              </span>
              {primary.map((link) => (
                <NavItem key={link.href} link={link} active={isActive(link.href)} />
              ))}
            </nav>
            <nav className="flex flex-wrap items-center gap-1">
              <span className="mr-1 text-[10px] font-medium uppercase tracking-wider text-slate-600">
                Tools
              </span>
              {assistants.map((link) => (
                <NavItem key={link.href} link={link} active={isActive(link.href)} />
              ))}
              <span className="mx-2 hidden h-3 w-px bg-white/10 sm:block" />
              <span className="mr-1 text-[10px] font-medium uppercase tracking-wider text-slate-600">
                Platform
              </span>
              {platformLinks.map((link) => (
                <NavItem key={link.href} link={link} active={isActive(link.href)} />
              ))}
            </nav>
          </div>
        </div>
      </header>
      <div className="mx-auto max-w-6xl px-6 py-8">{children}</div>
    </div>
  );
}

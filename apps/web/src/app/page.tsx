import Link from "next/link";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function HomePage() {
  return (
    <main className="relative mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16">
      <div className="max-w-2xl">
        <p className="font-display text-5xl leading-[1.05] text-white sm:text-6xl md:text-7xl">
          AI Workspace
        </p>
        <p className="mt-6 max-w-lg text-lg leading-relaxed text-slate-300">
          One signed-in platform for chat, document Q&amp;A with citations, SQL,
          agents, and evaluation — built like production software, runnable on
          your laptop.
        </p>
        <div className="mt-10 flex flex-wrap gap-3">
          <Link
            href="/login"
            className="rounded-md bg-teal-400 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-teal-300"
          >
            Enter workspace
          </Link>
          <a
            href={`${apiUrl}/docs`}
            className="rounded-md border border-white/15 px-5 py-2.5 text-sm font-medium text-slate-200 transition hover:border-teal-400/40 hover:text-white"
          >
            API reference
          </a>
        </div>
      </div>

      <section className="mt-20 border-t border-white/10 pt-10">
        <h2 className="text-sm font-medium tracking-[0.18em] text-slate-500 uppercase">
          Inside the product
        </h2>
        <dl className="mt-6 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {[
            {
              t: "Knowledge",
              d: "Upload PDFs and docs, ask questions, get answers with source citations.",
            },
            {
              t: "Assistants",
              d: "SQL (safe SELECT), code review, resume ATS, and meeting notes.",
            },
            {
              t: "Agents & quality",
              d: "Multi-agent runs with traces, RAG evaluation metrics, and model benchmarks.",
            },
          ].map((item) => (
            <div key={item.t}>
              <dt className="font-display text-xl text-teal-200">{item.t}</dt>
              <dd className="mt-2 text-sm leading-relaxed text-slate-400">{item.d}</dd>
            </div>
          ))}
        </dl>
      </section>

      <p className="mt-16 text-xs text-slate-500">
        Local demo: web :3000 · API :8000 · Ollama tinyllama
      </p>
    </main>
  );
}

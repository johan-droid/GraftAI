export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-6 py-16 text-center">
        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">GraftAI UI shell</h1>
        <p className="mt-6 max-w-2xl text-base text-slate-300 sm:text-lg">
          This is the minimal frontend starting point. Edit <code className="rounded bg-slate-800 px-2 py-1 text-sm text-slate-200">src/app/page.tsx</code> to begin building the UI.
        </p>

        <div className="mt-12 grid w-full gap-4 sm:grid-cols-2">
          <div className="rounded-3xl border border-slate-700/60 bg-slate-900/80 p-6 text-left shadow-xl shadow-slate-900/20">
            <h2 className="text-2xl font-semibold text-white">Start here</h2>
            <p className="mt-3 text-slate-400">Create new sections, cards, and layouts from this page.</p>
          </div>
          <div className="rounded-3xl border border-slate-700/60 bg-slate-900/80 p-6 text-left shadow-xl shadow-slate-900/20">
            <h2 className="text-2xl font-semibold text-white">Build fast</h2>
            <p className="mt-3 text-slate-400">Tailwind is ready. Use the existing global stylesheet and add components under src/app.</p>
          </div>
        </div>

        <div className="mt-12 rounded-3xl border border-slate-700/60 bg-slate-900/80 p-6 text-left text-slate-300 shadow-xl shadow-slate-900/20">
          <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Key files</p>
          <ul className="mt-3 space-y-1 text-sm">
            <li>src/app/layout.tsx</li>
            <li>src/app/page.tsx</li>
            <li>src/app/globals.css</li>
          </ul>
        </div>
      </section>
    </main>
  );
}

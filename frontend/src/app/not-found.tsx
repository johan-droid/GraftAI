import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <main className="app-shell flex min-h-screen items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-primary/10 rounded-full blur-[150px] pointer-events-none" />

      <div className="text-center z-10 max-w-md">
        <h1 className="text-8xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-fuchsia-600 mb-4">404</h1>
        <h2 className="text-2xl font-bold text-white mb-3">Page Not Found</h2>
        <p className="text-slate-400 mb-8">The page you are looking for does not exist or has been moved.</p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-medium text-white hover:bg-primary/90 transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)]"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>
      </div>
    </main>
  );
}

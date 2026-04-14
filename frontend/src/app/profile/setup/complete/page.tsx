"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { CheckCircle2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { toast } from "@/components/ui/Toast";
import { completeOnboarding, getOnboardingPreview } from "@/lib/api";

export default function SetupCompletePage() {
  const router = useRouter();
  const [previewUrl, setPreviewUrl] = useState<string>("");
  const [isCompleting, setIsCompleting] = useState(false);
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const result = await getOnboardingPreview();
        setPreviewUrl(result.bookingPageUrl);
      } catch (error) {
        console.error(error);
      }
    };
    load();
  }, []);

  useEffect(() => {
    if (!isDone) return;
    const timer = window.setTimeout(() => {
      router.push("/dashboard");
    }, 1100);

    return () => window.clearTimeout(timer);
  }, [isDone, router]);

  const handleComplete = async () => {
    setIsCompleting(true);
    try {
      const result = await completeOnboarding();
      toast.success("Onboarding complete!");
      setIsDone(true);
      if (result.redirectUrl) {
        window.history.replaceState({}, "", result.redirectUrl);
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to complete onboarding.");
    } finally {
      setIsCompleting(false);
    }
  };

  return (
    <div className="pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Final step</p>
          <h1 className="text-3xl font-semibold text-white">Setup complete</h1>
          <p className="text-sm text-slate-400">Your scheduler is now ready to go live. Confirm to finish onboarding.</p>
        </div>

        {isDone && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-5 flex items-start gap-3"
          >
            <motion.div
              initial={{ scale: 0.7, rotate: -8 }}
              animate={{ scale: [0.7, 1.05, 1], rotate: 0 }}
              transition={{ duration: 0.24, ease: "easeOut" }}
              className="mt-0.5"
            >
              <CheckCircle2 className="h-6 w-6 text-emerald-300" />
            </motion.div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-emerald-100">You’re live.</p>
              <p className="mt-1 text-sm text-emerald-200/80">Your setup is complete. Redirecting to the dashboard now.</p>
              <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-[11px] font-medium text-emerald-200">
                <Sparkles className="h-3.5 w-3.5" />
                Milestone unlocked
              </div>
            </div>
          </motion.div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Booking page preview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-slate-300">
              {previewUrl ? (
                <a href={previewUrl} target="_blank" rel="noreferrer" className="underline text-indigo-300">
                  {previewUrl}
                </a>
              ) : (
                <p>Loading preview link…</p>
              )}
            </div>
            <div className="mt-6 flex gap-3">
              <Button onClick={handleComplete} disabled={isCompleting}>{isCompleting ? "Completing..." : "Complete setup"}</Button>
              <Button variant="secondary" onClick={() => router.push("/dashboard")}>Go to dashboard</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

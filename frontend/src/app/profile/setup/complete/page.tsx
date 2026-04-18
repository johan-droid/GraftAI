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
    <div className="px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="overflow-hidden rounded-3xl border border-[#DADCE0] bg-white p-5 shadow-[0_24px_60px_-40px_rgba(32,33,36,0.28)] sm:p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-[#5F6368]">Final step</p>
          <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight text-[#202124]">Setup complete</h1>
              <p className="text-sm text-[#5F6368]">Your scheduler is now ready to go live. Confirm to finish onboarding.</p>
            </div>
            <div className="inline-flex items-center gap-2 rounded-2xl bg-[#E8F5E9] px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-[#1E8E3E]">
              <Sparkles className="h-3.5 w-3.5" />
              Ready to launch
            </div>
          </div>
        </div>

        {isDone && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            className="flex items-start gap-3 rounded-3xl border border-emerald-200 bg-emerald-50 p-5"
          >
            <motion.div
              initial={{ scale: 0.7, rotate: -8 }}
              animate={{ scale: [0.7, 1.05, 1], rotate: 0 }}
              transition={{ duration: 0.24, ease: "easeOut" }}
              className="mt-0.5"
            >
              <CheckCircle2 className="h-6 w-6 text-emerald-600" />
            </motion.div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-emerald-900">You’re live.</p>
              <p className="mt-1 text-sm text-emerald-800">Your setup is complete. Redirecting to the dashboard now.</p>
              <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-white px-3 py-1 text-[11px] font-medium text-emerald-700">
                <Sparkles className="h-3.5 w-3.5" />
                Milestone unlocked
              </div>
            </div>
          </motion.div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-[#202124]">Booking page preview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] p-6 text-sm text-[#5F6368]">
              {previewUrl ? (
                <a href={previewUrl} target="_blank" rel="noreferrer" className="break-all text-[#1A73E8] underline">
                  {previewUrl}
                </a>
              ) : (
                <p>Loading preview link…</p>
              )}
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button onClick={handleComplete} disabled={isCompleting}>{isCompleting ? "Completing..." : "Complete setup"}</Button>
              <Button variant="secondary" onClick={() => router.push("/dashboard")}>Go to dashboard</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

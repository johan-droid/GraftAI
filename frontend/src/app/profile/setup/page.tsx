"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Box } from "@mui/material";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { toast } from "@/components/ui/Toast";
import { getProfileSetupStatus } from "@/lib/api";

const steps = [
  {
    id: "profile",
    title: "Profile Setup",
    description: "Add your avatar, display name, bio and phone.",
    duration: "5 min",
  },
  {
    id: "calendar",
    title: "Calendar Connection",
    description: "Connect Google Calendar and enable conflict detection.",
    duration: "3 min",
  },
  {
    id: "availability",
    title: "Availability",
    description: "Set timezone, work hours and buffer time.",
    duration: "3 min",
  },
  {
    id: "event_type",
    title: "Create Booking Type",
    description: "Publish your first event type and preview your booking page.",
    duration: "4 min",
  },
];

export default function OnboardingChecklistPage() {
  const router = useRouter();
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const status = await getProfileSetupStatus();
        setCompletedSteps(status.completed_steps ?? []);
        setFinished(status.onboarding_completed ?? false);
      } catch (error) {
        console.error(error);
        toast.error("Unable to load onboarding status.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const percent = Math.round((completedSteps.length / steps.length) * 100);

  const getFirstIncompleteStepRoute = () => {
    const firstIncomplete = steps.find((step) => !completedSteps.includes(step.id));
    return firstIncomplete ? `/profile/setup/${firstIncomplete.id}` : "/profile/setup/complete";
  };

  return (
    <div className="space-y-6 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Post-signup setup</p>
          <h1 className="mt-3 text-3xl font-semibold text-white">Complete your scheduler profile</h1>
          <p className="mt-3 text-sm text-slate-400 max-w-2xl">
            Finish onboarding to publish your booking page, connect your calendar, and create your first event type.
          </p>
        </div>

        <Card className="mb-6">
          <CardContent>
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-slate-400">Progress</p>
                <h2 className="text-2xl font-semibold text-white">{percent}% complete</h2>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button variant="default" onClick={() => router.push(getFirstIncompleteStepRoute())}>Continue setup</Button>
                <Button variant="secondary" onClick={() => router.push("/dashboard")}>Go to dashboard</Button>
              </div>
            </div>
            <div className="mt-6 rounded-full border border-white/10 bg-white/5 overflow-hidden">
              <Box
                sx={{
                  height: 8,
                  width: `${percent}%`,
                  borderRadius: 999,
                  background: "linear-gradient(90deg, #6366f1, #22c55e)",
                  transition: "width 180ms ease",
                }}
              />
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 lg:grid-cols-2">
          {steps.map((step) => {
            const isDone = completedSteps.includes(step.id);
            return (
              <Card key={step.id} className="border-white/10">
                <CardHeader>
                  <div className="flex items-center justify-between gap-4">
                    <CardTitle>{step.title}</CardTitle>
                    <span className={isDone ? "text-emerald-400" : "text-slate-500"}>
                      {isDone ? "Completed" : step.duration}
                    </span>
                  </div>
                  <CardDescription>{step.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between gap-4">
                    <Button variant={isDone ? "secondary" : "default"} onClick={() => router.push(`/profile/setup/${step.id}`)}>
                      {isDone ? "Review" : "Start"}
                    </Button>
                    {isDone && <span className="text-xs uppercase tracking-[0.3em] text-emerald-400">✓</span>}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {finished && (
          <Card className="mt-6 border-emerald-500/20 bg-emerald-500/5">
            <CardContent>
              <h2 className="text-lg font-semibold text-emerald-200">Setup complete</h2>
              <p className="mt-2 text-sm text-slate-300">Your onboarding is finished. You can go live with your booking page now.</p>
              <div className="mt-4 flex gap-3">
                <Button variant="default" onClick={() => router.push("/profile/setup/complete")}>View completion</Button>
                <Button variant="secondary" onClick={() => router.push("/dashboard")}>Go to dashboard</Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

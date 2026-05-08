"use client";

import { useEffect, useState } from "react";
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

  const completedCount = completedSteps.length;
  const totalSteps = steps.length;
  const percent = Math.round((completedCount / totalSteps) * 100);

  const getFirstIncompleteStepRoute = () => {
    const firstIncomplete = steps.find((step) => !completedSteps.includes(step.id));
    return firstIncomplete ? `/profile/setup/${firstIncomplete.id}` : "/profile/setup/complete";
  };

  return (
    <div className="px-4 pb-12 pt-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="overflow-hidden rounded-3xl border border-[#DADCE0] bg-white p-5 shadow-[0_24px_60px_-40px_rgba(32,33,36,0.28)] sm:p-6">
          <div className="flex flex-col gap-5">
            <p className="text-xs uppercase tracking-[0.3em] text-[#5F6368]">Post-signup setup</p>
            <div className="space-y-3">
              <h1 className="text-3xl font-semibold tracking-tight text-[#202124] sm:text-4xl">Complete your scheduler profile</h1>
              <p className="max-w-2xl text-sm leading-6 text-[#5F6368]">
                Finish onboarding to publish your booking page, connect your calendar, and create your first event type.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button variant="default" onClick={() => router.push(getFirstIncompleteStepRoute())} disabled={loading}>
                {loading ? "Loading..." : "Continue setup"}
              </Button>
              <Button variant="secondary" onClick={() => router.push("/dashboard")}>Go to dashboard</Button>
            </div>
          </div>
        </div>

        <Card className="overflow-hidden">
          <CardContent className="space-y-4 p-5 sm:p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm font-medium text-[#5F6368]">Progress</p>
                <h2 className="mt-1 text-2xl font-semibold text-[#202124]">{percent}% complete</h2>
                <p className="mt-1 text-sm text-[#5F6368]">{completedCount} of {totalSteps} steps done</p>
              </div>
              <div className="inline-flex items-center rounded-2xl bg-[#E8F0FE] px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-[#1A73E8]">
                Mobile-first
              </div>
            </div>

            <div className="rounded-full bg-[#F1F3F4] p-1">
              <Box
                sx={{
                  height: 10,
                  width: `${percent}%`,
                  borderRadius: 999,
                  background: "linear-gradient(90deg, #1A73E8 0%, #34A853 100%)",
                  transition: "width 180ms ease",
                }}
              />
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          {steps.map((step, index) => {
            const isDone = completedSteps.includes(step.id);
            return (
              <Card key={step.id} className={isDone ? "border-[#CDE7D6] bg-[#F8FCF8]" : ""}>
                <CardHeader className="space-y-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2">
                      <span className="inline-flex rounded-full bg-[#F1F3F4] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-[#5F6368]">
                        Step {String(index + 1).padStart(2, "0")}
                      </span>
                      <CardTitle className="text-xl text-[#202124]">{step.title}</CardTitle>
                    </div>
                    <span className={isDone ? "rounded-full bg-[#E6F4EA] px-3 py-1 text-xs font-semibold text-[#1E8E3E]" : "rounded-full bg-[#E8F0FE] px-3 py-1 text-xs font-semibold text-[#1A73E8]"}>
                      {isDone ? "Completed" : step.duration}
                    </span>
                  </div>
                  <CardDescription className="text-[#5F6368]">{step.description}</CardDescription>
                </CardHeader>
                <CardContent className="flex items-center justify-between gap-4 pt-0">
                  <Button variant={isDone ? "secondary" : "default"} onClick={() => router.push(`/profile/setup/${step.id}`)}>
                    {isDone ? "Review step" : "Start"}
                  </Button>
                  <span className="text-xs font-medium uppercase tracking-[0.2em] text-[#5F6368]">
                    {isDone ? "Saved" : step.duration}
                  </span>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {finished && (
          <Card className="border-[#CDE7D6] bg-[#F1F8E9]">
            <CardContent className="space-y-3 p-5 sm:p-6">
              <div className="inline-flex rounded-full bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-[#1E8E3E]">
                Setup complete
              </div>
              <h2 className="text-lg font-semibold text-[#1E8E3E]">Your onboarding is finished.</h2>
              <p className="text-sm text-[#3C4043]">You can go live with your booking page now.</p>
              <div className="flex flex-col gap-3 sm:flex-row">
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

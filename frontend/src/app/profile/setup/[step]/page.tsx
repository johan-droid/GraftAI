"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { toast } from "@/components/ui/Toast";
import { getProfileSetupStatus, updateUserProfile, getGoogleCalendarAuthUrl, completeOnboardingStep, createEventType, completeOnboarding, getOnboardingPreview } from "@/lib/api";
import { useOnboarding } from "@/context/onboarding-context";
import { ProfileForm } from "@/components/profile/ProfileForm";

const steps = [
  { id: "profile", label: "Profile", next: "calendar" },
  { id: "calendar", label: "Calendar", next: "availability" },
  { id: "availability", label: "Availability", next: "event_type" },
  { id: "event_type", label: "Event Type", next: "complete" },
];

const timezones = ["UTC", "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "Europe/London", "Europe/Paris", "Asia/Tokyo", "Asia/Singapore"];
const workHourOptions = ["06:00","07:00","08:00","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00"];
const bufferOptions = [0, 15, 30, 45, 60, 90, 120];

export default function StepPage({ params }: { params: { step: string } }) {
  const router = useRouter();
  const { step } = params;
  const { markStepComplete } = useOnboarding();
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const currentStep = useMemo(() => steps.find((item) => item.id === step), [step]);
  const nextStep = currentStep?.next ?? "complete";

  useEffect(() => {
    if (!currentStep) {
      router.replace("/profile/setup");
    }
  }, [currentStep, router]);

  if (!currentStep) {
    return null;
  }

  return (
    <div className="pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Onboarding step</p>
          <h1 className="text-3xl font-semibold text-white">{currentStep.label}</h1>
          <p className="text-sm text-slate-400">Complete this step to keep your scheduler setup moving forward.</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{currentStep.label}</CardTitle>
          </CardHeader>
          <CardContent>
            {step === "profile" && <ProfileForm onCompleted={() => { markStepComplete(step); router.push(`/profile/setup/${nextStep}`); }} />}
            {step === "calendar" && <CalendarStep onCompleted={() => { markStepComplete(step); router.push(`/profile/setup/${nextStep}`); }} />}
            {step === "availability" && <AvailabilityStep onCompleted={() => { markStepComplete(step); router.push(`/profile/setup/${nextStep}`); }} />}
            {step === "event_type" && <EventTypeStep onCompleted={() => { markStepComplete(step); router.push(`/profile/setup/${nextStep}`); }} />}
            {step === "complete" && <CompleteStep />}
            {statusMessage && <div className="text-sm text-slate-300">{statusMessage}</div>}
          </CardContent>
        </Card>

        <div className="flex justify-between gap-4">
          <Button variant="secondary" onClick={() => router.back()}>Back</Button>
          <Button variant="ghost" onClick={() => router.push("/profile/setup")}>Checklist</Button>
        </div>
      </div>
    </div>
  );
}

function CalendarStep({ onCompleted }: { onCompleted: () => void }) {
  const [connecting, setConnecting] = useState(false);
  const [status, setStatus] = useState<string>("Connect your calendar provider to continue.");

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const data = await getGoogleCalendarAuthUrl();
      window.location.href = data.authUrl;
    } catch (error) {
      console.error(error);
      toast.error("Unable to initialize calendar connection.");
    } finally {
      setConnecting(false);
    }
  };

  const handleMarkConnected = async () => {
    try {
      await completeOnboardingStep("calendar");
      toast.success("Calendar step marked complete.");
      onCompleted();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not mark calendar step.");
    }
  };

  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-400">Your calendar connection is required so GraftAI can check for scheduling conflicts and publish your availability.</p>
      <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
        <p className="text-sm font-semibold text-white">Google Calendar</p>
        <p className="mt-2 text-sm text-slate-300">Connect a Google Calendar account to sync events and availability.</p>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <Button onClick={handleConnect} disabled={connecting}>{connecting ? "Opening Google..." : "Connect Google Calendar"}</Button>
          <Button variant="secondary" onClick={handleMarkConnected}>Mark as connected</Button>
        </div>
      </div>
      <div className="text-sm text-slate-300">{status}</div>
    </div>
  );
}

function AvailabilityStep({ onCompleted }: { onCompleted: () => void }) {
  const { register, handleSubmit, watch, setValue, formState: { errors, isSubmitting } } = useForm({
    defaultValues: {
      timezone: "UTC",
      start_time: "09:00",
      end_time: "17:00",
      buffer_minutes: 15,
      time_format: "12h",
    },
  });

  useEffect(() => {
    const load = async () => {
      try {
        const result = await getProfileSetupStatus();
        const profile = result.profile;
        if (profile) {
          setValue("timezone", profile.timezone || "UTC");
          setValue("start_time", profile.preferences?.work_hours?.start || "09:00");
          setValue("end_time", profile.preferences?.work_hours?.end || "17:00");
          setValue("buffer_minutes", profile.preferences?.buffer_minutes ?? 15);
          setValue("time_format", profile.time_format || "12h");
        }
      } catch (error) {
        console.error(error);
      }
    };
    load();
  }, [setValue]);

  const onSubmit = async (data: any) => {
    try {
      await updateUserProfile({
        timezone: data.timezone,
        time_format: data.time_format,
        preferences: {
          work_hours: { start: data.start_time, end: data.end_time },
          buffer_minutes: data.buffer_minutes,
        },
      });
      await completeOnboardingStep("availability");
      toast.success("Availability saved!");
      onCompleted();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to save availability.");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label htmlFor="timezone" className="block text-sm font-semibold text-slate-100">Timezone</label>
          <select id="timezone" {...register("timezone", { required: true })} className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-indigo-500">
            {timezones.map((tz) => (<option key={tz} value={tz}>{tz}</option>))}
          </select>
          {errors.timezone && <p className="text-sm text-red-400">Timezone is required.</p>}
        </div>
        <div className="space-y-2">
          <label htmlFor="buffer_minutes" className="block text-sm font-semibold text-slate-100">Buffer Time</label>
          <select id="buffer_minutes" {...register("buffer_minutes", { required: true, valueAsNumber: true })} className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-indigo-500">
            {bufferOptions.map((minutes) => (<option key={minutes} value={minutes}>{minutes} minutes</option>))}
          </select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <label htmlFor="start_time" className="block text-sm font-semibold text-slate-100">Work start</label>
          <select id="start_time" {...register("start_time", { required: true })} className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-indigo-500">
            {workHourOptions.map((time) => <option key={time} value={time}>{time}</option>)}
          </select>
        </div>
        <div className="space-y-2">
          <label htmlFor="end_time" className="block text-sm font-semibold text-slate-100">Work end</label>
          <select id="end_time" {...register("end_time", { required: true })} className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-indigo-500">
            {workHourOptions.map((time) => <option key={time} value={time}>{time}</option>)}
          </select>
        </div>
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-100">Time preference</label>
          <div className="grid grid-cols-2 gap-2">
            {(["12h", "24h"] as const).map((value) => (
              <label key={value} className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm">
                <input type="radio" value={value} {...register("time_format")} />
                <span>{value}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Saving..." : "Save availability"}</Button>
      </div>
    </form>
  );
}

function EventTypeStep({ onCompleted }: { onCompleted: () => void }) {
  const { register, handleSubmit, watch, setValue, formState: { errors, isSubmitting } } = useForm({
    defaultValues: {
      name: "Discovery Call",
      slug: "discovery-call",
      duration_minutes: 30,
      description: "A quick introduction call to discuss your scheduling needs.",
      color: "#3b82f6",
    },
  });

  const nameValue = watch("name");

  useEffect(() => {
    const slug = nameValue
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    if (slug) {
      const currentSlug = watch("slug");
      if (!currentSlug || currentSlug === "discovery-call" || currentSlug.startsWith(nameValue.toLowerCase().split(" ")[0])) {
        // Only update when user hasn't customized the slug heavily.
        setValue("slug", slug);
      }
    }
  }, [nameValue, watch, setValue]);

  const onSubmit = async (data: any) => {
    try {
      await createEventType({
        name: data.name,
        slug: data.slug,
        duration_minutes: Number(data.duration_minutes),
        description: data.description,
        color: data.color,
      });
      await completeOnboardingStep("event_type");
      toast.success("Event type created!");
      onCompleted();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to create event type.");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label htmlFor="name" className="block text-sm font-semibold text-slate-100">Event name</label>
          <Input id="name" {...register("name", { required: "Event name is required", maxLength: { value: 50, message: "Event name must be 1-50 characters" } })} />
          {errors.name && <p className="text-sm text-red-400">{errors.name.message}</p>}
        </div>
        <div className="space-y-2">
          <label htmlFor="slug" className="block text-sm font-semibold text-slate-100">Slug</label>
          <Input id="slug" {...register("slug", { required: "Slug is required", pattern: { value: /^[a-z0-9\-]{1,50}$/, message: "Slug may only contain lowercase letters, numbers and hyphens." } })} />
          {errors.slug && <p className="text-sm text-red-400">{errors.slug.message}</p>}
        </div>
      </div>

      <div className="space-y-2">
        <label htmlFor="duration_minutes" className="block text-sm font-semibold text-slate-100">Duration</label>
        <select id="duration_minutes" {...register("duration_minutes", { required: true })} className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-indigo-500">
          {[15, 30, 45, 60, 90, 120, 180].map((minutes) => (<option key={minutes} value={minutes}>{minutes} minutes</option>))}
        </select>
      </div>

      <div className="space-y-2">
        <label htmlFor="description" className="block text-sm font-semibold text-slate-100">Description</label>
        <textarea id="description" {...register("description", { maxLength: { value: 250, message: "Description must be under 250 characters" } })} rows={4} className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-indigo-500" />
        {errors.description && <p className="text-sm text-red-400">{errors.description.message}</p>}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 items-end">
        <div className="space-y-2">
          <label htmlFor="color" className="block text-sm font-semibold text-slate-100">Picker color</label>
          <Input id="color" type="color" {...register("color")} className="h-12 rounded-lg p-0" />
        </div>
        <div className="text-slate-400 text-sm">
          <p>Booking page will publish with this event type. You can always update it later.</p>
        </div>
      </div>

      <div className="flex justify-end">
        <Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Creating..." : "Create event type"}</Button>
      </div>
    </form>
  );
}

function CompleteStep() {
  const [finished, setFinished] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

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

  const handleComplete = async () => {
    try {
      const result = await completeOnboarding();
      toast.success("Onboarding complete!");
      setFinished(true);
      window.location.href = result.redirectUrl;
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to complete onboarding.");
    }
  };

  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-400">You are one step away from going live. Complete the setup to activate your scheduler flow.</p>
      {previewUrl && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
          <p className="text-sm text-slate-100">Preview booking page URL</p>
          <p className="mt-2 text-sm font-medium text-white">{previewUrl}</p>
        </div>
      )}
      <div className="flex justify-end gap-3">
        <Button onClick={handleComplete} disabled={finished}>{finished ? "Redirecting..." : "Complete setup"}</Button>
      </div>
    </div>
  );
}

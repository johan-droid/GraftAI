"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Controller, useForm } from "react-hook-form";
import { Box, FormControl, InputLabel, MenuItem, Select } from "@mui/material";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
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
const labelClass = "block text-sm font-semibold text-[#202124]";
const helperClass = "text-sm text-[#5F6368]";
const fieldClass = "w-full rounded-xl border border-[#DADCE0] bg-white px-3 py-2 text-sm text-[#202124] outline-none transition-colors placeholder:text-[#80868B] focus:border-[#1A73E8] focus:ring-2 focus:ring-[#D2E3FC]";

export default function StepPage() {
  const router = useRouter();
  const params = useParams<{ step: string }>();
  const step = params.step;
  const { markStepComplete } = useOnboarding();

  const currentStep = useMemo(() => steps.find((item) => item.id === step), [step]);
  const nextStep = currentStep?.next ?? "complete";
  const currentStepIndex = currentStep ? steps.findIndex((item) => item.id === currentStep.id) : -1;
  const currentStepPosition = currentStepIndex >= 0 ? currentStepIndex + 1 : 1;
  const progress = Math.round((currentStepPosition / steps.length) * 100);

  useEffect(() => {
    if (!currentStep) {
      router.replace("/profile/setup");
    }
  }, [currentStep, router]);

  if (!currentStep) {
    return null;
  }

  return (
    <div className="px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="overflow-hidden rounded-3xl border border-[#DADCE0] bg-white p-5 shadow-[0_24px_60px_-40px_rgba(32,33,36,0.28)] sm:p-6">
          <p className="text-xs uppercase tracking-[0.3em] text-[#5F6368]">Onboarding step</p>
          <div className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight text-[#202124]">{currentStep.label}</h1>
              <p className="max-w-2xl text-sm leading-6 text-[#5F6368]">
                Complete this step to keep your scheduler setup moving forward.
              </p>
            </div>
            <div className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.2em] text-[#5F6368]">Step {currentStepPosition} of {steps.length}</p>
              <p className="mt-1 text-sm font-semibold text-[#202124]">{progress}% complete</p>
            </div>
          </div>

          <div className="mt-4 rounded-full bg-[#F1F3F4] p-1">
            <Box
              sx={{
                height: 8,
                width: `${progress}%`,
                borderRadius: 999,
                background: "linear-gradient(90deg, #1A73E8 0%, #34A853 100%)",
                transition: "width 180ms ease",
              }}
            />
          </div>
        </div>

        <Card className="overflow-hidden">
          <CardHeader className="space-y-2">
            <CardTitle className="text-[#202124]">{currentStep.label}</CardTitle>
            <CardDescription className="text-[#5F6368]">
              Complete this step to keep your scheduler setup moving forward.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {step === "profile" && <ProfileForm onCompleted={() => { markStepComplete(step); router.push(`/profile/setup/${nextStep}`); }} />}
            {step === "calendar" && <CalendarStep onCompleted={() => { markStepComplete(step); router.push(`/profile/setup/${nextStep}`); }} />}
            {step === "availability" && <AvailabilityStep onCompleted={() => { markStepComplete(step); router.push(`/profile/setup/${nextStep}`); }} />}
            {step === "event_type" && <EventTypeStep onCompleted={() => { markStepComplete(step); router.push(`/profile/setup/${nextStep}`); }} />}
            {step === "complete" && <CompleteStep />}
          </CardContent>
        </Card>

        <div className="flex flex-col gap-3 sm:flex-row sm:justify-between">
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
      <p className={helperClass}>Your calendar connection is required so GraftAI can check for scheduling conflicts and publish your availability.</p>
      <div className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] p-5">
        <p className="text-sm font-semibold text-[#202124]">Google Calendar</p>
        <p className="mt-2 text-sm text-[#5F6368]">Connect a Google Calendar account to sync events and availability.</p>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <Button onClick={handleConnect} disabled={connecting}>{connecting ? "Opening Google..." : "Connect Google Calendar"}</Button>
          <Button variant="secondary" onClick={handleMarkConnected}>Mark as connected</Button>
        </div>
      </div>
      <div className="text-sm text-[#5F6368]">{status}</div>
    </div>
  );
}

function AvailabilityStep({ onCompleted }: { onCompleted: () => void }) {
  const { control, register, handleSubmit, watch, setValue, formState: { errors, isSubmitting } } = useForm({
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
          <label htmlFor="timezone" className={labelClass}>Timezone</label>
          <Controller
            control={control}
            name="timezone"
            rules={{ required: true }}
            render={({ field }) => (
              <FormControl fullWidth>
                <InputLabel id="availability-timezone-label">Timezone</InputLabel>
                <Select labelId="availability-timezone-label" id="timezone" label="Timezone" {...field}>
                  {timezones.map((tz) => (<MenuItem key={tz} value={tz}>{tz}</MenuItem>))}
                </Select>
              </FormControl>
            )}
          />
          {errors.timezone && <p className="text-sm text-red-500">Timezone is required.</p>}
        </div>
        <div className="space-y-2">
          <label htmlFor="buffer_minutes" className={labelClass}>Buffer Time</label>
          <Controller
            control={control}
            name="buffer_minutes"
            rules={{ required: true }}
            render={({ field }) => (
              <FormControl fullWidth>
                <InputLabel id="availability-buffer-label">Buffer Time</InputLabel>
                <Select
                  labelId="availability-buffer-label"
                  id="buffer_minutes"
                  label="Buffer Time"
                  value={field.value}
                  onChange={(event) => field.onChange(Number(event.target.value))}
                >
                  {bufferOptions.map((minutes) => (<MenuItem key={minutes} value={minutes}>{minutes} minutes</MenuItem>))}
                </Select>
              </FormControl>
            )}
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <label htmlFor="start_time" className={labelClass}>Work start</label>
          <Controller
            control={control}
            name="start_time"
            rules={{ required: true }}
            render={({ field }) => (
              <FormControl fullWidth>
                <InputLabel id="availability-start-label">Work start</InputLabel>
                <Select labelId="availability-start-label" id="start_time" label="Work start" {...field}>
                  {workHourOptions.map((time) => <MenuItem key={time} value={time}>{time}</MenuItem>)}
                </Select>
              </FormControl>
            )}
          />
        </div>
        <div className="space-y-2">
          <label htmlFor="end_time" className={labelClass}>Work end</label>
          <Controller
            control={control}
            name="end_time"
            rules={{ required: true }}
            render={({ field }) => (
              <FormControl fullWidth>
                <InputLabel id="availability-end-label">Work end</InputLabel>
                <Select labelId="availability-end-label" id="end_time" label="Work end" {...field}>
                  {workHourOptions.map((time) => <MenuItem key={time} value={time}>{time}</MenuItem>)}
                </Select>
              </FormControl>
            )}
          />
        </div>
        <div className="space-y-2">
          <label className={labelClass}>Time preference</label>
          <div className="grid grid-cols-2 gap-2">
            {(["12h", "24h"] as const).map((value) => (
              <label key={value} className="inline-flex items-center gap-2 rounded-xl border border-[#DADCE0] bg-[#F8F9FA] px-3 py-2 text-sm text-[#202124]">
                <input type="radio" value={value} {...register("time_format")} className="accent-[#1A73E8]" />
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
  const { register, handleSubmit, watch, setValue, control, formState: { errors, isSubmitting } } = useForm({
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
          <label htmlFor="name" className={labelClass}>Event name</label>
          <Input id="name" {...register("name", { required: "Event name is required", maxLength: { value: 50, message: "Event name must be 1-50 characters" } })} />
          {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
        </div>
        <div className="space-y-2">
          <label htmlFor="slug" className={labelClass}>Slug</label>
          <Input id="slug" {...register("slug", { required: "Slug is required", pattern: { value: /^[a-z0-9\-]{1,50}$/, message: "Slug may only contain lowercase letters, numbers and hyphens." } })} />
          {errors.slug && <p className="text-sm text-red-500">{errors.slug.message}</p>}
        </div>
      </div>

      <div className="space-y-2">
        <label htmlFor="duration_minutes" className={labelClass}>Duration</label>
        <Controller
          control={control}
          name="duration_minutes"
          rules={{ required: true }}
          render={({ field }) => (
            <FormControl fullWidth>
              <InputLabel id="event-type-duration-label">Duration</InputLabel>
              <Select
                labelId="event-type-duration-label"
                id="duration_minutes"
                label="Duration"
                value={field.value}
                onChange={(event) => field.onChange(Number(event.target.value))}
              >
                {[15, 30, 45, 60, 90, 120, 180].map((minutes) => (<MenuItem key={minutes} value={minutes}>{minutes} minutes</MenuItem>))}
              </Select>
            </FormControl>
          )}
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="description" className={labelClass}>Description</label>
        <textarea id="description" {...register("description", { maxLength: { value: 250, message: "Description must be under 250 characters" } })} rows={4} className={`${fieldClass} min-h-[112px]`} />
        {errors.description && <p className="text-sm text-red-500">{errors.description.message}</p>}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 items-end">
        <div className="space-y-2">
          <label htmlFor="color" className={labelClass}>Picker color</label>
          <Input id="color" type="color" {...register("color")} className="h-12 rounded-xl p-1" />
        </div>
        <div className={helperClass}>
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
      <p className={helperClass}>You are one step away from going live. Complete the setup to activate your scheduler flow.</p>
      {previewUrl && (
        <div className="rounded-2xl border border-[#DADCE0] bg-[#F8F9FA] p-5">
          <p className="text-sm font-semibold text-[#202124]">Preview booking page URL</p>
          <p className="mt-2 break-all text-sm font-medium text-[#1A73E8]">{previewUrl}</p>
        </div>
      )}
      <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
        <Button onClick={handleComplete} disabled={finished}>{finished ? "Redirecting..." : "Complete setup"}</Button>
      </div>
    </div>
  );
}

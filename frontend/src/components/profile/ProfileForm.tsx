"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { toast } from "@/components/ui/Toast";
import { completeOnboardingStep, getProfileSetupStatus, saveUserProfile, uploadProfileAvatar } from "@/lib/api";

interface ProfileFormValues {
  display_name: string;
  bio: string;
  phone: string;
  timezone: string;
  time_format: "12h" | "24h";
  theme: "system" | "light" | "dark";
}

const timezones = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Asia/Tokyo",
  "Asia/Singapore",
];

interface ProfileFormProps {
  onCompleted: () => void;
}

export function ProfileForm({ onCompleted }: ProfileFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormValues>({
    defaultValues: {
      display_name: "",
      bio: "",
      phone: "",
      timezone: "UTC",
      time_format: "12h",
      theme: "system",
    },
  });

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);

  useEffect(() => {
    return () => {
      if (previewUrl?.startsWith("blob:")) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const status = await getProfileSetupStatus();
        const profile = status.profile;
        setValue("display_name", profile.display_name ?? "");
        setValue("bio", profile.bio ?? "");
        setValue("phone", profile.phone ?? "");
        setValue("timezone", profile.timezone ?? "UTC");
        setValue("time_format", profile.time_format === "24h" ? "24h" : "12h");
        setValue("theme", (profile.theme as ProfileFormValues["theme"]) ?? "system");
        if (profile.avatar_url) {
          setPreviewUrl(profile.avatar_url);
        }
      } catch (error) {
        console.error(error);
        toast.error("Unable to load profile data.");
      }
    };
    loadProfile();
  }, [setValue]);

  const handleAvatarChange = (file?: File) => {
    if (!file) {
      setAvatarFile(null);
      return;
    }
    if (previewUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl);
    }
    setAvatarFile(file);
    const preview = URL.createObjectURL(file);
    setPreviewUrl(preview);
  };

  const onSubmit = async (data: ProfileFormValues) => {
    try {
      if (avatarFile) {
        await uploadProfileAvatar(avatarFile);
      }
      await saveUserProfile({
        display_name: data.display_name.trim(),
        bio: data.bio.trim(),
        phone: data.phone.trim() || undefined,
        timezone: data.timezone,
        time_format: data.time_format,
        theme: data.theme,
      });
      await completeOnboardingStep("profile");
      toast.success("Profile saved!");
      onCompleted();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to save profile.");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <label htmlFor="display_name" className="block text-sm font-semibold text-slate-100">Display Name</label>
          <Input
            id="display_name"
            {...register("display_name", {
              required: "Name is required",
              minLength: { value: 1, message: "Name must be 1-100 characters" },
              maxLength: { value: 100, message: "Name must be 1-100 characters" },
              pattern: {
                value: /^[A-Za-z0-9 '\-]+$/,
                message: "Name may only contain letters, numbers, spaces, apostrophes, or hyphens",
              },
            })}
          />
          {errors.display_name && <p className="text-sm text-red-400">{errors.display_name.message}</p>}
        </div>

        <div className="space-y-2 sm:col-span-2">
          <label htmlFor="bio" className="block text-sm font-semibold text-slate-100">Bio</label>
          <textarea
            id="bio"
            {...register("bio", {
              maxLength: { value: 500, message: "Bio must be under 500 characters" },
            })}
            rows={4}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {errors.bio && <p className="text-sm text-red-400">{errors.bio.message}</p>}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <label htmlFor="phone" className="block text-sm font-semibold text-slate-100">Phone</label>
          <Input
            id="phone"
            {...register("phone", {
              pattern: {
                value: /^\+?[1-9]\d{1,14}$/,
                message: "Enter a valid international phone number",
              },
            })}
            placeholder="+1234567890"
          />
          {errors.phone && <p className="text-sm text-red-400">{errors.phone.message}</p>}
        </div>

        <div className="space-y-2">
          <label htmlFor="timezone" className="block text-sm font-semibold text-slate-100">Timezone</label>
          <select
            id="timezone"
            {...register("timezone", { required: "Timezone is required" })}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {timezones.map((tz) => (
              <option key={tz} value={tz}>
                {tz}
              </option>
            ))}
          </select>
          {errors.timezone && <p className="text-sm text-red-400">{errors.timezone.message}</p>}
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-100">Time Format</label>
          <div className="grid grid-cols-2 gap-2">
            {(["12h", "24h"] as const).map((option) => (
              <label key={option} className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm">
                <input type="radio" value={option} {...register("time_format")} className="accent-indigo-500" />
                <span>{option}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <label htmlFor="theme" className="block text-sm font-semibold text-slate-100">Theme</label>
          <select
            id="theme"
            {...register("theme")}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>

        <div className="space-y-2">
          <label htmlFor="avatar" className="block text-sm font-semibold text-slate-100">Avatar</label>
          <input
            id="avatar"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(event) => handleAvatarChange(event.target.files?.[0])}
            className="block w-full text-sm text-slate-200 file:rounded-full file:border-0 file:bg-indigo-500 file:px-3 file:py-2 file:text-sm file:text-white"
          />
        </div>

        <div className="space-y-2">
          <p className="text-sm font-semibold text-slate-100">Preview</p>
          <div className="h-24 w-24 rounded-full bg-white/5 overflow-hidden border border-white/10">
            {previewUrl ? (
              <img src={previewUrl} alt="Avatar preview" className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full items-center justify-center text-xs uppercase text-slate-500">No image</div>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : "Save and continue"}
        </Button>
      </div>
    </form>
  );
}

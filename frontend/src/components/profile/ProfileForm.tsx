"use client";

import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";
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
const fieldClass = "w-full rounded-xl border border-[#DADCE0] bg-white px-3 py-2 text-sm text-[#202124] outline-none transition-colors placeholder:text-[#80868B] focus:border-[#1A73E8] focus:ring-2 focus:ring-[#D2E3FC]";
const labelClass = "block text-sm font-semibold text-[#202124]";
const radioClass = "inline-flex items-center gap-2 rounded-xl border border-[#DADCE0] bg-[#F8F9FA] px-3 py-2 text-sm text-[#202124]";

interface ProfileFormProps {
  onCompleted: () => void;
}

export function ProfileForm({ onCompleted }: ProfileFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    control,
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
          <label htmlFor="display_name" className={labelClass}>Display Name</label>
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
          {errors.display_name && <p className="text-sm text-red-500">{errors.display_name.message}</p>}
        </div>

        <div className="space-y-2 sm:col-span-2">
          <label htmlFor="bio" className={labelClass}>Bio</label>
          <textarea
            id="bio"
            {...register("bio", {
              maxLength: { value: 500, message: "Bio must be under 500 characters" },
            })}
            rows={4}
            className={`${fieldClass} min-h-[112px]`}
          />
          {errors.bio && <p className="text-sm text-red-500">{errors.bio.message}</p>}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <label htmlFor="phone" className={labelClass}>Phone</label>
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
          {errors.phone && <p className="text-sm text-red-500">{errors.phone.message}</p>}
        </div>

        <div className="space-y-2">
          <label htmlFor="timezone" className={labelClass}>Timezone</label>
          <Controller
            name="timezone"
            control={control}
            rules={{ required: "Timezone is required" }}
            render={({ field }) => (
              <FormControl fullWidth>
                <InputLabel id="timezone-label">Timezone</InputLabel>
                <Select labelId="timezone-label" id="timezone" label="Timezone" {...field}>
                  {timezones.map((tz) => (
                    <MenuItem key={tz} value={tz}>
                      {tz}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          />
          {errors.timezone && <p className="text-sm text-red-500">{errors.timezone.message}</p>}
        </div>

        <div className="space-y-2">
          <label className={labelClass}>Time Format</label>
          <div className="grid grid-cols-2 gap-2">
            {(["12h", "24h"] as const).map((option) => (
              <label key={option} className={radioClass}>
                <input type="radio" value={option} {...register("time_format")} className="accent-[#1A73E8]" />
                <span>{option}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <label htmlFor="theme" className={labelClass}>Theme</label>
          <Controller
            name="theme"
            control={control}
            render={({ field }) => (
              <FormControl fullWidth>
                <InputLabel id="theme-label">Theme</InputLabel>
                <Select labelId="theme-label" id="theme" label="Theme" {...field}>
                  <MenuItem value="system">System</MenuItem>
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="dark">Dark</MenuItem>
                </Select>
              </FormControl>
            )}
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="avatar" className={labelClass}>Avatar</label>
          <input
            id="avatar"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(event) => handleAvatarChange(event.target.files?.[0])}
            className="block w-full text-sm text-[#5F6368] file:rounded-full file:border-0 file:bg-[#1A73E8] file:px-3 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-[#1558B0]"
          />
        </div>

        <div className="space-y-2">
          <p className={labelClass}>Preview</p>
          <div className="h-24 w-24 overflow-hidden rounded-full border border-[#DADCE0] bg-[#F8F9FA]">
            {previewUrl ? (
              <img src={previewUrl} alt="Avatar preview" className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full items-center justify-center text-xs uppercase text-[#80868B]">No image</div>
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

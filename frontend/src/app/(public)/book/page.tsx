"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Clock, Video, Globe, Calendar as CalendarIcon,
  ArrowLeft, User, Mail, MessageSquare, CheckCircle2, Loader2
} from "lucide-react";
import Link from "next/link";

const MOCK_EVENT = {
  hostName: "John Doe",
  title: "15 Min Quick Chat",
  duration: "15 min",
  location: "Google Meet",
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
};

function BookingForm() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const dateParam = searchParams.get("date");
  const timeParam = searchParams.get("time");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    notes: "",
  });

  const formattedDate = dateParam
    ? new Date(dateParam).toLocaleDateString("default", {
        weekday: "long",
        month: "long",
        day: "numeric",
      })
    : "No date selected";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await new Promise((resolve) => setTimeout(resolve, 1200));
      setIsSuccess(true);
    } catch {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white border border-[#DADCE0] rounded-3xl shadow-sm p-10 md:p-16 text-center max-w-2xl mx-auto w-full"
      >
        <div className="w-20 h-20 bg-[#E6F4EA] rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle2 className="w-10 h-10 text-[#137333]" />
        </div>
        <h1 className="text-3xl font-semibold text-[#202124] tracking-tight mb-4">
          You are scheduled!
        </h1>
        <p className="text-base text-[#5F6368] mb-8 leading-relaxed max-w-md mx-auto">
          A calendar invitation has been sent to your email address. If you need to reschedule or cancel, you can use the link in the email.
        </p>

        <div className="bg-[#F8F9FA] border border-[#DADCE0] rounded-2xl p-6 text-left max-w-sm mx-auto mb-8">
          <h3 className="font-semibold text-[#202124] mb-4">{MOCK_EVENT.title}</h3>
          <div className="space-y-3 text-sm text-[#5F6368]">
            <div className="flex items-center gap-3">
              <CalendarIcon size={18} className="text-[#1A73E8]" />
              {formattedDate}
            </div>
            <div className="flex items-center gap-3">
              <Clock size={18} className="text-[#1A73E8]" />
              {timeParam}
            </div>
            <div className="flex items-center gap-3">
              <Video size={18} className="text-[#137333]" />
              {MOCK_EVENT.location}
            </div>
          </div>
        </div>

        <Link href="/" className="text-sm font-medium text-[#1A73E8] hover:underline">
          Return to home
        </Link>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-[#DADCE0] rounded-3xl shadow-sm overflow-hidden flex flex-col md:flex-row w-full"
    >
      <div className="w-full md:w-[40%] bg-[#F8F9FA] p-8 md:p-10 border-b md:border-b-0 md:border-r border-[#DADCE0] flex flex-col">
        <button
          type="button"
          aria-label="Go back"
          title="Go back"
          onClick={() => router.back()}
          className="w-10 h-10 rounded-full flex items-center justify-center bg-white border border-[#DADCE0] text-[#5F6368] hover:text-[#202124] hover:bg-[#F1F3F4] transition-colors mb-8 shadow-sm"
        >
          <ArrowLeft size={20} />
        </button>

        <p className="text-sm font-semibold text-[#5F6368] uppercase tracking-wider mb-1">
          {MOCK_EVENT.hostName}
        </p>
        <h2 className="text-2xl font-semibold text-[#202124] tracking-tight mb-6">
          {MOCK_EVENT.title}
        </h2>

        <div className="space-y-4 text-[15px] font-medium text-[#5F6368] bg-white border border-[#DADCE0] p-5 rounded-2xl shadow-sm">
          <div className="flex items-start gap-3">
            <CalendarIcon size={20} className="text-[#1A73E8] shrink-0 mt-0.5" />
            <span className="leading-snug">
              {formattedDate}
              <br />
              {timeParam}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Globe size={20} className="text-[#E37400] shrink-0" />
            {MOCK_EVENT.timezone}
          </div>
          <div className="flex items-center gap-3">
            <Video size={20} className="text-[#137333] shrink-0" />
            {MOCK_EVENT.location}
          </div>
        </div>
      </div>

      <div className="w-full md:w-[60%] p-8 md:p-10">
        <h2 className="text-xl font-semibold text-[#202124] mb-6">Enter Details</h2>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2 flex items-center gap-2">
              <User size={14} /> Full Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full bg-[#F8F9FA] border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/20 focus:border-[#1A73E8] transition-all placeholder:text-[#9AA0A6]"
              placeholder="e.g. Jane Doe"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2 flex items-center gap-2">
              <Mail size={14} /> Email Address *
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full bg-[#F8F9FA] border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/20 focus:border-[#1A73E8] transition-all placeholder:text-[#9AA0A6]"
              placeholder="jane@company.com"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-2 flex items-center gap-2">
              <MessageSquare size={14} /> Additional Notes
            </label>
            <textarea
              rows={3}
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full bg-[#F8F9FA] border border-[#DADCE0] rounded-xl px-4 py-3 text-[#202124] focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/20 focus:border-[#1A73E8] transition-all resize-none placeholder:text-[#9AA0A6]"
              placeholder="Please share anything that will help prepare for our meeting..."
            />
          </div>

          <div className="pt-4 mt-6 border-t border-[#F1F3F4]">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full sm:w-auto flex items-center justify-center gap-2 text-sm font-medium bg-[#1A73E8] text-white hover:bg-[#1557B0] px-8 py-3.5 rounded-full transition-colors shadow-sm disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <><Loader2 size={18} className="animate-spin" /> Scheduling...</>
              ) : (
                "Schedule Event"
              )}
            </button>
          </div>
        </form>
      </div>
    </motion.div>
  );
}

export default function BookPage() {
  return (
    <Suspense
      fallback={
        <div className="w-full min-h-[500px] flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-[#1A73E8] animate-spin" />
        </div>
      }
    >
      <BookingForm />
    </Suspense>
  );
}

"use client";

import { motion } from "framer-motion";
import {
  Zap,
  Plus,
  Mail,
  MessageSquare,
  Webhook,
  Clock,
  CalendarCheck,
  CalendarX,
  ArrowRight,
  MoreVertical,
} from "lucide-react";
import { useAutomations } from "@/hooks/useAutomations";

const MOCK_AUTOMATIONS = [
  { id: "1", trigger: "booking_created", action: "send_email", payload: { subject: "Confirmation" }, active: true },
  { id: "2", trigger: "reminder_24h", action: "send_email", payload: { subject: "Reminder" }, active: true },
  { id: "3", trigger: "reminder_1h", action: "send_sms", payload: { message: "Starting soon" }, active: false },
  { id: "4", trigger: "booking_cancelled", action: "webhook", payload: { url: "https://crm.com/update" }, active: true },
];

function getTriggerDisplay(trigger: string) {
  switch (trigger) {
    case "booking_created":
      return {
        icon: <CalendarCheck size={16} />,
        label: "New Booking Created",
        color: "text-[#137333] bg-[#E6F4EA]",
      };
    case "booking_cancelled":
      return {
        icon: <CalendarX size={16} />,
        label: "Booking Cancelled",
        color: "text-[#D93025] bg-[#FCE8E6]",
      };
    case "reminder_24h":
      return {
        icon: <Clock size={16} />,
        label: "24 Hours Before",
        color: "text-[#E37400] bg-[#FEF7E0]",
      };
    case "reminder_1h":
      return {
        icon: <Clock size={16} />,
        label: "1 Hour Before",
        color: "text-[#E37400] bg-[#FEF7E0]",
      };
    default:
      return {
        icon: <Zap size={16} />,
        label: trigger,
        color: "text-[#5F6368] bg-[#F1F3F4]",
      };
  }
}

function getActionDisplay(action: string) {
  switch (action) {
    case "send_email":
      return { icon: <Mail size={16} />, label: "Send Email" };
    case "send_sms":
      return { icon: <MessageSquare size={16} />, label: "Send SMS" };
    case "webhook":
      return { icon: <Webhook size={16} />, label: "Trigger Webhook" };
    default:
      return { icon: <Zap size={16} />, label: action };
  }
}

export default function WorkflowsPage() {
  const { automations, isLoading, toggleAutomation } = useAutomations();
  const displayData = automations?.length ? automations : MOCK_AUTOMATIONS;

  if (isLoading) {
    return (
      <div className="p-6 md:p-10 max-w-6xl mx-auto w-full">
        <div className="flex h-40 items-center justify-center rounded-3xl border border-[#DADCE0] bg-white shadow-sm">
          <p className="text-sm text-[#5F6368]">Loading workflows…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto w-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-10 pb-6 border-b border-[#DADCE0]">
        <div>
          <h1 className="text-3xl font-medium text-[#202124] tracking-tight mb-2">Workflows</h1>
          <p className="text-[#5F6368] text-base max-w-xl">
            Automate your scheduling process. Trigger emails, SMS reminders, and webhooks automatically.
          </p>
        </div>
        <button className="inline-flex items-center justify-center gap-2 bg-[#1A73E8] text-white hover:bg-[#1557B0] px-6 py-2.5 rounded-full text-sm font-medium transition-colors shadow-sm shrink-0">
          <Plus size={18} />
          Create Workflow
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {displayData.map((rule, i) => {
          const trigger = getTriggerDisplay(rule.trigger);
          const action = getActionDisplay(rule.action);

          return (
            <motion.div
              key={rule.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`bg-white border border-[#DADCE0] rounded-3xl p-6 shadow-sm hover:shadow-md transition-all ${!rule.active ? "opacity-60 grayscale-[0.3]" : ""}`}
            >
              <div className="flex items-start justify-between mb-8">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${trigger.color}`}>
                    {trigger.icon}
                  </div>
                  <ArrowRight size={16} className="text-[#DADCE0]" />
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#E8F0FE] text-[#1A73E8]">
                    {action.icon}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    aria-label={rule.active ? "Disable workflow" : "Enable workflow"}
                    title={rule.active ? "Disable workflow" : "Enable workflow"}
                    onClick={() => toggleAutomation(rule.id, !rule.active)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${rule.active ? "bg-[#1A73E8]" : "bg-[#DADCE0]"}`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm ${rule.active ? "translate-x-6" : "translate-x-1"}`} />
                  </button>
                  <button
                    type="button"
                    aria-label="Workflow actions"
                    title="Workflow actions"
                    className="text-[#5F6368] hover:bg-[#F1F3F4] p-1.5 rounded-full transition-colors"
                  >
                    <MoreVertical size={18} />
                  </button>
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-1">When this happens</p>
                <p className="text-lg font-medium text-[#202124] mb-4">{trigger.label}</p>

                <div className="h-px w-full bg-[#F1F3F4] mb-4" />

                <p className="text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-1">Do this</p>
                <p className="text-[15px] font-medium text-[#1A73E8] flex items-center gap-2">{action.label}</p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

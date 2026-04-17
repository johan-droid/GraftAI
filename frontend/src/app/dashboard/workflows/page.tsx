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

function humanizeIdentifier(value: string) {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getRuleTypeDisplay(ruleType: string) {
  switch (ruleType) {
    case "auto_accept":
      return {
        icon: <CalendarCheck size={16} />,
        label: "Auto Accept",
        color: "text-[#137333] bg-[#E6F4EA]",
      };
    case "auto_decline":
      return {
        icon: <CalendarX size={16} />,
        label: "Auto Decline",
        color: "text-[#D93025] bg-[#FCE8E6]",
      };
    case "auto_reschedule":
      return {
        icon: <Clock size={16} />,
        label: "Auto Reschedule",
        color: "text-[#E37400] bg-[#FEF7E0]",
      };
    case "smart_scheduling":
      return {
        icon: <Zap size={16} />,
        label: "Smart Scheduling",
        color: "text-[#1A73E8] bg-[#E8F0FE]",
      };
    case "conflict_resolution":
      return {
        icon: <Zap size={16} />,
        label: "Conflict Resolution",
        color: "text-[#5F6368] bg-[#F1F3F4]",
      };
    case "team_coordination":
      return {
        icon: <CalendarCheck size={16} />,
        label: "Team Coordination",
        color: "text-[#0B8043] bg-[#E6F4EA]",
      };
    case "reminder_scheduling":
      return {
        icon: <Clock size={16} />,
        label: "Reminder Scheduling",
        color: "text-[#E37400] bg-[#FEF7E0]",
      };
    case "resource_allocation":
      return {
        icon: <Zap size={16} />,
        label: "Resource Allocation",
        color: "text-[#5F6368] bg-[#F1F3F4]",
      };
    default:
      return {
        icon: <Zap size={16} />,
        label: humanizeIdentifier(ruleType),
        color: "text-[#5F6368] bg-[#F1F3F4]",
      };
  }
}

function getActionDisplay(actions: Record<string, unknown>) {
  const explicitAction = typeof actions.action === "string"
    ? actions.action
    : typeof actions.type === "string"
      ? actions.type
      : undefined;

  const primaryAction = explicitAction || Object.keys(actions)[0] || "configured_action";

  switch (primaryAction) {
    case "send_email":
    case "accept":
    case "auto_accept":
      return { icon: <Mail size={16} />, label: "Send Email" };
    case "send_sms":
    case "notify":
      return { icon: <MessageSquare size={16} />, label: "Send SMS" };
    case "webhook":
      return { icon: <Webhook size={16} />, label: "Trigger Webhook" };
    case "reschedule":
    case "auto_reschedule":
      return { icon: <Clock size={16} />, label: "Reschedule Booking" };
    default:
      return { icon: <Zap size={16} />, label: humanizeIdentifier(primaryAction) };
  }
}

export default function WorkflowsPage() {
  const { automations, isLoading, error, toggleAutomation } = useAutomations();
  const displayData = automations;

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

      {error ? (
        <div className="rounded-3xl border border-[#FCE8E6] bg-[#FFF8F8] p-8 text-center shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#D93025] mb-2">Automation rules unavailable</p>
          <p className="text-sm text-[#5F6368]">
            {error instanceof Error ? error.message : "Failed to load automation rules from the server."}
          </p>
        </div>
      ) : displayData.length === 0 ? (
        <div className="rounded-3xl border border-[#DADCE0] bg-white p-10 text-center shadow-sm">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#E8F0FE] text-[#1A73E8]">
            <Zap size={22} />
          </div>
          <h2 className="text-2xl font-medium text-[#202124] mb-2">No automation rules yet</h2>
          <p className="mx-auto max-w-lg text-sm text-[#5F6368]">
            Create a workflow rule to automate booking confirmations, reminders, or webhook actions.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {displayData.map((rule, i) => {
            const trigger = getRuleTypeDisplay(rule.rule_type);
            const action = getActionDisplay(rule.actions);
            const confidenceLabel = `${Math.round(rule.confidence_threshold)}% confidence`;

            return (
              <motion.div
                key={rule.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className={`bg-white border border-[#DADCE0] rounded-3xl p-6 shadow-sm hover:shadow-md transition-all ${!rule.is_enabled ? "opacity-60 grayscale-[0.3]" : ""}`}
              >
                <div className="flex items-start justify-between gap-4 mb-6">
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-1">Automation rule</p>
                    <p className="text-lg font-medium text-[#202124] truncate">{rule.name}</p>
                    <p className="text-sm text-[#5F6368] mt-1">{rule.description || "No description provided."}</p>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      <span className="rounded-full bg-[#F1F3F4] px-2.5 py-1 font-medium text-[#5F6368]">
                        {trigger.label}
                      </span>
                      <span className="rounded-full bg-[#E8F0FE] px-2.5 py-1 font-medium text-[#1A73E8]">
                        {confidenceLabel}
                      </span>
                      <span className="rounded-full bg-[#F1F3F4] px-2.5 py-1 font-medium text-[#5F6368]">
                        Priority {rule.priority}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <button
                      type="button"
                      aria-label={rule.is_enabled ? "Disable workflow" : "Enable workflow"}
                      title={rule.is_enabled ? "Disable workflow" : "Enable workflow"}
                      onClick={() => toggleAutomation(rule.id, !rule.is_enabled)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${rule.is_enabled ? "bg-[#1A73E8]" : "bg-[#DADCE0]"}`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm ${rule.is_enabled ? "translate-x-6" : "translate-x-1"}`} />
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
                </div>

                <div>
                  <p className="text-xs font-semibold text-[#5F6368] uppercase tracking-wider mb-1">Do this</p>
                  <p className="text-[15px] font-medium text-[#1A73E8] flex items-center gap-2">{action.label}</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}

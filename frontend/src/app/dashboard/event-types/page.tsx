"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  createEventType,
  deleteEventType,
  EventTypePayload,
  EventTypeResponse,
  listEventTypes,
  updateEventType,
} from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Sparkles, CreditCard, ShieldCheck } from "lucide-react";

const defaultFormState: EventTypePayload = {
  name: "",
  description: "",
  slug: "",
  duration_minutes: 60,
  meeting_provider: "",
  is_public: true,
  buffer_before_minutes: 0,
  buffer_after_minutes: 0,
  minimum_notice_minutes: 0,
  availability: {},
  exceptions: [],
  recurrence_rule: "",
  custom_questions: [],
  requires_attendee_confirmation: false,
  travel_time_before_minutes: 0,
  travel_time_after_minutes: 0,
  requires_payment: false,
  payment_amount: 0,
  payment_currency: "USD",
  team_assignment_method: "host_only",
};

interface EventTypeItem extends EventTypeResponse {}

const defaultEmptyFormState: EventTypePayload = defaultFormState;

export default function EventTypesPage() {
  const [eventTypes, setEventTypes] = useState<EventTypeItem[]>([]);
  const [selectedEventTypeId, setSelectedEventTypeId] = useState<string | null>(null);
  const [form, setForm] = useState<EventTypePayload>(defaultEmptyFormState);
  const [customQuestions, setCustomQuestions] = useState<Array<{ id: string; question: string; type: string; required: boolean; options?: string[] }>>((defaultEmptyFormState.custom_questions as any) || []);
  const [exceptionsText, setExceptionsText] = useState<string>((defaultEmptyFormState.exceptions as string[] || []).join(", ") || "");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadEventTypes();
  }, []);

  async function loadEventTypes() {
    setLoading(true);
    setError(null);

    try {
      const data = await listEventTypes();
      setEventTypes(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load event types");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmitEventType(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const exceptions = exceptionsText
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);

      const parsedCustomQuestions = customQuestions.map((question) => ({
        id: question.id,
        question: question.question,
        type: question.type,
        required: question.required,
        options: question.options?.filter(Boolean),
      }));

      const payload: EventTypePayload = {
        ...form,
        team_assignment_method: "host_only",
        availability: form.availability,
        exceptions,
        custom_questions: parsedCustomQuestions,
        duration_minutes: Number(form.duration_minutes),
        travel_time_before_minutes: Number(form.travel_time_before_minutes),
        travel_time_after_minutes: Number(form.travel_time_after_minutes),
        payment_amount: form.requires_payment ? Number(form.payment_amount) : null,
        payment_currency: form.payment_currency?.toUpperCase() || "USD",
      };

      if (selectedEventTypeId) {
        await updateEventType(selectedEventTypeId, payload);
        setSuccess("Event type updated successfully.");
      } else {
        await createEventType(payload);
        setSuccess("Event type created successfully.");
      }

      setSelectedEventTypeId(null);
      setForm(defaultEmptyFormState);
      setCustomQuestions((defaultEmptyFormState.custom_questions as any) || []);
      setExceptionsText(((defaultEmptyFormState.exceptions as string[]) || []).join(", "));
      await loadEventTypes();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save event type");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteEventType(eventTypeId: string) {
    if (!confirm("Delete this event type? This cannot be undone.")) {
      return;
    }
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await deleteEventType(eventTypeId);
      setSuccess("Event type deleted successfully.");
      if (selectedEventTypeId === eventTypeId) {
        setSelectedEventTypeId(null);
        setForm(defaultEmptyFormState);
      }
      await loadEventTypes();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete event type");
    } finally {
      setSaving(false);
    }
  }

  function handleEditEventType(eventType: EventTypeItem) {
    setSelectedEventTypeId(eventType.id);
    setForm({
      name: eventType.name,
      description: eventType.description || "",
      slug: eventType.slug,
      duration_minutes: eventType.duration_minutes,
      meeting_provider: eventType.meeting_provider || "",
      is_public: eventType.is_public,
      buffer_before_minutes: eventType.buffer_before_minutes || 0,
      buffer_after_minutes: eventType.buffer_after_minutes || 0,
      minimum_notice_minutes: eventType.minimum_notice_minutes || 0,
      availability: eventType.availability || {},
      exceptions: eventType.exceptions || [],
      recurrence_rule: eventType.recurrence_rule || "",
      custom_questions: eventType.custom_questions || [],
      requires_attendee_confirmation: eventType.requires_attendee_confirmation,
      travel_time_before_minutes: eventType.travel_time_before_minutes || 0,
      travel_time_after_minutes: eventType.travel_time_after_minutes || 0,
      requires_payment: eventType.requires_payment,
      payment_amount: eventType.payment_amount || 0,
      payment_currency: eventType.payment_currency || "USD",
      team_assignment_method: "host_only",
    });
    setCustomQuestions(
      (eventType.custom_questions || []).map((question: any, index: number) => ({
        id: String(question.id || question.question || `q-${index}`),
        question: String(question.question || ""),
        type: String(question.type || "text"),
        required: Boolean(question.required),
        options: Array.isArray(question.options) ? question.options.map(String) : [],
      }))
    );
    setExceptionsText((eventType.exceptions || []).join(", "));
    setError(null);
    setSuccess(null);
  }

  function handleCancelEdit() {
    setSelectedEventTypeId(null);
    setForm(defaultEmptyFormState);
    setCustomQuestions((defaultEmptyFormState.custom_questions as any) || []);
    setExceptionsText(((defaultEmptyFormState.exceptions as string[]) || []).join(", "));
    setError(null);
    setSuccess(null);
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white">Event Types</h1>
          <p className="mt-2 text-sm text-slate-400 max-w-2xl">
            Create and manage your public booking pages, availability rules, and payment settings for one-to-one meetings.
          </p>
        </div>
        <Button variant="outline" onClick={loadEventTypes} disabled={loading}>
          Refresh list
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Existing event types</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="min-h-[220px] flex items-center justify-center text-slate-400">Loading event types…</div>
              ) : eventTypes.length === 0 ? (
                <div className="min-h-[220px] rounded-2xl border border-dashed border-white/10 bg-white/5 p-8 text-center text-slate-400">
                  No event types have been created yet.
                </div>
              ) : (
                <div className="space-y-4">
                  {eventTypes.map((type) => (
                    <div key={type.id} className="rounded-3xl border border-white/10 bg-slate-950/60 p-5 shadow-xl shadow-black/10">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                          <p className="text-lg font-semibold text-white">{type.name}</p>
                          <p className="text-sm text-slate-500">/{type.slug}</p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-medium text-slate-300">{type.duration_minutes} min</span>
                          {type.is_public && <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">Public</span>}
                          {!type.is_public && <span className="rounded-full bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300">Private</span>}
                          {type.requires_payment && <span className="rounded-full bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-300">Paid</span>}
                        </div>
                      </div>

                      <div className="mt-4 grid gap-3 sm:grid-cols-2">
                        <div className="space-y-1">
                          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Meeting mode</p>
                          <p className="text-sm text-slate-300">One-to-one (host only)</p>
                        </div>
                        <div className="space-y-1">
                          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Requires confirmation</p>
                          <p className="text-sm text-slate-300">{type.requires_attendee_confirmation ? "Yes" : "No"}</p>
                        </div>
                      </div>

                      <div className="mt-4 grid gap-3 sm:grid-cols-2">
                        <div className="space-y-1">
                          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Travel buffer</p>
                          <p className="text-sm text-slate-300">{type.travel_time_before_minutes}m before · {type.travel_time_after_minutes}m after</p>
                        </div>
                        {type.requires_payment && (
                          <div className="space-y-1">
                            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Price</p>
                            <p className="text-sm text-slate-300">{type.payment_amount?.toFixed(2)} {type.payment_currency}</p>
                          </div>
                        )}
                      </div>

                      {type.recurrence_rule && (
                        <div className="mt-4 rounded-2xl border border-white/10 bg-slate-900/60 p-4 text-sm text-slate-400">
                          <p className="font-medium text-slate-200">Recurrence rule</p>
                          <p>{type.recurrence_rule}</p>
                        </div>
                      )}

                      <div className="mt-4 flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => handleEditEventType(type)}
                          className="rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 transition hover:bg-white/10"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteEventType(type.id)}
                          className="rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-200 transition hover:bg-red-500/20"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Create a new event type</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-5" onSubmit={handleSubmitEventType}>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-200" htmlFor="name">Name</label>
                  <input
                    id="name"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                    placeholder="30 minute discovery call"
                    required
                  />
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-200" htmlFor="slug">Slug</label>
                    <input
                      id="slug"
                      value={form.slug}
                      onChange={(e) => setForm({ ...form, slug: e.target.value })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                      placeholder="discovery"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-200" htmlFor="duration">Duration</label>
                    <input
                      id="duration"
                      type="number"
                      value={form.duration_minutes}
                      min={15}
                      onChange={(e) => setForm({ ...form, duration_minutes: Math.max(15, Number(e.target.value)) })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-200" htmlFor="description">Description</label>
                  <textarea
                    id="description"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    rows={3}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                    placeholder="Short description shown on your booking page"
                  />
                </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                    <label className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white">
                      <input
                        type="checkbox"
                        checked={form.is_public}
                        onChange={(e) => setForm({ ...form, is_public: e.target.checked })}
                        className="h-4 w-4 rounded border-white/20 bg-slate-900 text-indigo-500 focus:ring-indigo-500"
                      />
                      Public booking page
                    </label>
                    <label className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white">
                      <input
                        type="checkbox"
                        checked={form.requires_attendee_confirmation}
                        onChange={(e) => setForm({ ...form, requires_attendee_confirmation: e.target.checked })}
                        className="h-4 w-4 rounded border-white/20 bg-slate-900 text-indigo-500 focus:ring-indigo-500"
                      />
                      Attendee confirmation
                    </label>
                  </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-200" htmlFor="travel_before">Travel before (minutes)</label>
                    <input
                      id="travel_before"
                      type="number"
                      min={0}
                      value={form.travel_time_before_minutes}
                      onChange={(e) => setForm({ ...form, travel_time_before_minutes: Number(e.target.value) })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-200" htmlFor="travel_after">Travel after (minutes)</label>
                    <input
                      id="travel_after"
                      type="number"
                      min={0}
                      value={form.travel_time_after_minutes}
                      onChange={(e) => setForm({ ...form, travel_time_after_minutes: Number(e.target.value) })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-200" htmlFor="recurrence_rule">Recurrence rule</label>
                  <input
                    id="recurrence_rule"
                    value={form.recurrence_rule ?? ""}
                    onChange={(e) => setForm({ ...form, recurrence_rule: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                    placeholder="FREQ=WEEKLY;BYDAY=MO,WE,FR"
                  />
                </div>

                <div className="space-y-4 rounded-3xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <label className="text-sm font-medium text-slate-200">Availability</label>
                    <span className="text-xs text-slate-500">Weekly grid</span>
                  </div>
                  {[
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                  ].map((day) => {
                    const value = form.availability?.[day]?.[0] || "";
                    return (
                      <div key={day} className="grid grid-cols-[110px_1fr] gap-3 items-center">
                        <span className="capitalize text-sm text-slate-300">{day}</span>
                        <input
                          type="text"
                          value={value}
                          onChange={(e) => {
                            const range = e.target.value;
                            setForm((prev) => ({
                              ...prev,
                              availability: {
                                ...(prev.availability || {}),
                                [day]: range ? [range] : [],
                              },
                            }));
                          }}
                          placeholder="09:00-17:00"
                          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                        />
                      </div>
                    );
                  })}
                  <p className="text-xs text-slate-500">Enter a single time range per day in HH:MM-HH:MM format. Leave blank to disable that day.</p>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-200" htmlFor="exceptions">Exceptions</label>
                  <textarea
                    id="exceptions"
                    rows={2}
                    value={exceptionsText}
                    onChange={(e) => setExceptionsText(e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                    placeholder="2025-05-12, 2025-05-19"
                  />
                  <p className="text-xs text-slate-500">Enter exception dates comma-separated in YYYY-MM-DD format.</p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-4">
                    <label className="text-sm font-medium text-slate-200">Custom questions</label>
                    <button
                      type="button"
                      onClick={() => setCustomQuestions((prev) => [
                        ...prev,
                        { id: `q-${Date.now()}`, question: "", type: "text", required: false, options: [] },
                      ])}
                      className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200 hover:bg-white/10"
                    >
                      Add question
                    </button>
                  </div>
                  <div className="space-y-3">
                    {customQuestions.length === 0 ? (
                      <p className="text-sm text-slate-500">Add questions to capture extra booking details.</p>
                    ) : null}
                    {customQuestions.map((question, index) => (
                      <div key={question.id} className="rounded-2xl border border-white/10 bg-slate-900/40 p-4">
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-sm font-semibold text-white">Question {index + 1}</span>
                          <button
                            type="button"
                            onClick={() => setCustomQuestions((prev) => prev.filter((item) => item.id !== question.id))}
                            className="text-xs text-rose-300 hover:text-rose-100"
                          >
                            Remove
                          </button>
                        </div>
                        <div className="grid gap-3 sm:grid-cols-2 mt-4">
                          <div className="space-y-2">
                            <label htmlFor={`question-text-${question.id}`} className="text-sm text-slate-200">Question text</label>
                            <input
                              id={`question-text-${question.id}`}
                              value={question.question}
                              onChange={(e) => setCustomQuestions((prev) => prev.map((item) => item.id === question.id ? { ...item, question: e.target.value } : item))}
                              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                            />
                          </div>
                          <div className="space-y-2">
                            <label htmlFor={`question-type-${question.id}`} className="text-sm text-slate-200">Type</label>
                            <select
                              id={`question-type-${question.id}`}
                              value={question.type}
                              onChange={(e) => setCustomQuestions((prev) => prev.map((item) => item.id === question.id ? { ...item, type: e.target.value } : item))}
                              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                            >
                              <option value="text">Text</option>
                              <option value="textarea">Textarea</option>
                              <option value="checkbox">Checkbox</option>
                              <option value="select">Select</option>
                            </select>
                          </div>
                        </div>
                        <div className="grid gap-3 sm:grid-cols-3 mt-4">
                          <label className="flex items-center gap-2 text-sm text-slate-200">
                            <input
                              type="checkbox"
                              checked={question.required}
                              onChange={(e) => setCustomQuestions((prev) => prev.map((item) => item.id === question.id ? { ...item, required: e.target.checked } : item))}
                              className="h-4 w-4 rounded border-white/20 bg-slate-900 text-indigo-500 focus:ring-indigo-500"
                            />
                            Required
                          </label>
                          {question.type === "select" ? (
                            <div className="space-y-2 sm:col-span-2">
                              <label htmlFor={`question-options-${question.id}`} className="text-sm text-slate-200">Options</label>
                              <input
                                id={`question-options-${question.id}`}
                                value={(question.options || []).join(", ")}
                                onChange={(e) => setCustomQuestions((prev) => prev.map((item) => item.id === question.id ? { ...item, options: e.target.value.split(",").map((opt) => opt.trim()).filter(Boolean) } : item))}
                                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                                placeholder="Option 1, Option 2"
                              />
                            </div>
                          ) : null}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-4">
                    <label className="text-sm font-medium text-slate-200" htmlFor="payment_amount">Payment</label>
                    <span className="text-xs text-slate-500">Optional</span>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-[1fr_120px]">
                    <input
                      id="payment_amount"
                      type="number"
                      min={0}
                      step={0.01}
                      value={form.payment_amount ?? ""}
                      onChange={(e) => setForm({ ...form, payment_amount: Number(e.target.value) })}
                      disabled={!form.requires_payment}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                      placeholder="Amount"
                    />
                    <input
                      id="payment_currency"
                      value={form.payment_currency}
                      onChange={(e) => setForm({ ...form, payment_currency: e.target.value.toUpperCase() })}
                      disabled={!form.requires_payment}
                      placeholder="USD"
                      title="Payment currency"
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </div>
                  <label className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white">
                    <input
                      type="checkbox"
                      checked={form.requires_payment}
                      onChange={(e) => setForm({ ...form, requires_payment: e.target.checked })}
                      className="h-4 w-4 rounded border-white/20 bg-slate-900 text-indigo-500 focus:ring-indigo-500"
                    />
                    Enable payment requirements
                  </label>
                </div>

                {error && <p className="rounded-2xl bg-red-500/10 px-4 py-3 text-sm text-red-200">{error}</p>}
                {success && <p className="rounded-2xl bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">{success}</p>}

                <div className="flex flex-wrap items-center gap-3">
                  <Button type="submit" disabled={saving}>
                    {saving ? "Saving…" : selectedEventTypeId ? "Update event type" : "Create event type"}
                  </Button>
                  <Button type="button" variant="outline" onClick={handleCancelEdit}>
                    {selectedEventTypeId ? "Cancel edit" : "Reset form"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>What&apos;s next</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-slate-400">
              <div className="flex items-center gap-3">
                <Sparkles className="h-4 w-4 text-indigo-400" />
                <span>Public booking pages will use these event type definitions.</span>
              </div>
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-4 w-4 text-slate-400" />
                <span>Scheduling is intentionally locked to one-to-one host-only meetings for simpler operations.</span>
              </div>
              <div className="flex items-center gap-3">
                <CreditCard className="h-4 w-4 text-slate-400" />
                <span>Checkout and payment flow wiring is the next step after admin creation.</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

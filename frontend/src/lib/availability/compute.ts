export interface AvailabilityParams {
  username: string;
  eventType: string;
  month: string;
  timezone?: string;
  minNoticeMinutes?: number;
}

export interface EventTypeUser {
  credentials?: Array<{ type: string; [key: string]: unknown }>;
}

export interface AvailabilityConfig {
  id: string;
  durationMinutes: number;
  bufferBeforeMinutes: number;
  bufferAfterMinutes: number;
  minimumNoticeMinutes: number;
  availability: Record<string, string[]>;
  exceptions?: string[];
  timeZone: string;
  user: EventTypeUser;
}

export interface CalendarBusyTime {
  start: string;
  end: string;
}

export interface TimeSlot {
  start: Date;
  end: Date;
  timeZone?: string;
}

export interface ComputeInput {
  config: AvailabilityConfig;
  existingBookings: TimeSlot[];
  calendarBusyTimes: CalendarBusyTime[];
  params: AvailabilityParams;
}

const DAY_NAMES = [
  "sunday",
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
];

export function computeAvailability(input: ComputeInput): TimeSlot[] {
  const { config, existingBookings, calendarBusyTimes, params } = input;
  const dateRange = buildMonthRange(params.month);
  const minNoticeMinutes = params.minNoticeMinutes ?? config.minimumNoticeMinutes ?? 0;
  const nowUtc = new Date();
  const minTime = new Date(nowUtc.getTime() + minNoticeMinutes * 60 * 1000);

  const busyTimes = mergeBusyTimes([
    ...calendarBusyTimes,
    ...existingBookings.map((booking) => ({ start: booking.start.toISOString(), end: booking.end.toISOString() })),
  ]);

  const slots: TimeSlot[] = [];

  for (const day of dateRange) {
    const dayName = DAY_NAMES[day.getUTCDay()];
    const workingHours = config.availability?.[dayName] || [];
    if (!workingHours?.length) {
      continue;
    }

    for (const range of workingHours) {
      const intervals = breakIntoIntervals(day, range, 15, config.durationMinutes, config.timeZone);
      for (const slot of intervals) {
        if (slot.end <= minTime) continue;
        if (hasConflict(slot, busyTimes)) continue;
        slots.push(slot);
      }
    }
  }

  return slots;
}

export function breakIntoIntervals(
  day: Date,
  range: string,
  intervalMinutes: number,
  durationMinutes: number,
  timeZone: string
): TimeSlot[] {
  const [startString, endString] = range.split("-").map((part) => part.trim());
  if (!startString || !endString) return [];

  const start = buildUtcDateFromLocalTime(day, startString, timeZone);
  const end = buildUtcDateFromLocalTime(day, endString, timeZone);

  const slots: TimeSlot[] = [];
  let cursor = new Date(start.getTime());
  while (cursor.getTime() + durationMinutes * 60 * 1000 <= end.getTime()) {
    const next = new Date(cursor.getTime() + durationMinutes * 60 * 1000);
    slots.push({ start: new Date(cursor), end: next, timeZone });
    cursor = new Date(cursor.getTime() + intervalMinutes * 60 * 1000);
  }

  return slots;
}

function buildUtcDateFromLocalTime(day: Date, time: string, timeZone: string): Date {
  const [hours, minutes] = time.split(":").map(Number);
  const local = new Date(Date.UTC(day.getUTCFullYear(), day.getUTCMonth(), day.getUTCDate(), hours, minutes));
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
  const parts = formatter.formatToParts(local).reduce((acc, part) => {
    acc[part.type] = part.value;
    return acc;
  }, {} as Record<string, string>);

  return new Date(`${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:00${getOffsetString(timeZone, local)}`);
}

function getOffsetString(timeZone: string, date: Date): string {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    timeZoneName: "shortOffset",
  });
  const parts = formatter.formatToParts(date);
  const tzPart = parts.find((part) => part.type === "timeZoneName")?.value || "+00:00";
  const normalized = tzPart.replace("GMT", "").replace("UTC", "");
  return normalized || "+00:00";
}

export function hasConflict(slot: TimeSlot, busyTimes: CalendarBusyTime[]): boolean {
  return busyTimes.some((busy) => {
    const busyStart = new Date(busy.start).getTime();
    const busyEnd = new Date(busy.end).getTime();
    return slot.start.getTime() < busyEnd && busyStart < slot.end.getTime();
  });
}

export function mergeBusyTimes(values: CalendarBusyTime[]): CalendarBusyTime[] {
  const sorted = values
    .slice()
    .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
  const merged: CalendarBusyTime[] = [];
  for (const item of sorted) {
    if (!merged.length) {
      merged.push(item);
      continue;
    }
    const last = merged[merged.length - 1];
    if (new Date(item.start).getTime() <= new Date(last.end).getTime()) {
      last.end = new Date(Math.max(new Date(last.end).getTime(), new Date(item.end).getTime())).toISOString();
    } else {
      merged.push(item);
    }
  }
  return merged;
}

function buildMonthRange(month: string): Date[] {
  const [year, monthNumber] = month.split("-").map(Number);
  const range: Date[] = [];
  const start = new Date(Date.UTC(year, monthNumber - 1, 1));
  const nextMonth = new Date(Date.UTC(year, monthNumber - 1, 1));
  nextMonth.setUTCMonth(nextMonth.getUTCMonth() + 1);

  const cursor = new Date(start);
  while (cursor < nextMonth) {
    range.push(new Date(cursor));
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }
  return range;
}

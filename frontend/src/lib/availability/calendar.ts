import { AvailabilityConfig, CalendarBusyTime } from "./compute";

interface CalendarCredential {
  type: "google_calendar" | "outlook_calendar" | "caldav";
  [key: string]: unknown;
}

export async function getCalendarBusyTimes(config: AvailabilityConfig): Promise<CalendarBusyTime[]> {
  const busyTimes: CalendarBusyTime[] = [];

  for (const credential of (config.user.credentials || []) as CalendarCredential[]) {
    if (credential.type === "google_calendar") {
      busyTimes.push(...(await getGoogleCalendarBusy()));
    }
    if (credential.type === "outlook_calendar") {
      busyTimes.push(...(await getOutlookCalendarBusy()));
    }
    if (credential.type === "caldav") {
      busyTimes.push(...(await getCalDAVBusy()));
    }
  }

  return mergeAndDeduplicate(busyTimes);
}

async function getGoogleCalendarBusy(): Promise<CalendarBusyTime[]> {
  // Placeholder: move actual busy time fetching to backend if credentials are not available in the browser.
  return [];
}

async function getOutlookCalendarBusy(): Promise<CalendarBusyTime[]> {
  return [];
}

async function getCalDAVBusy(): Promise<CalendarBusyTime[]> {
  return [];
}

function mergeAndDeduplicate(busyTimes: CalendarBusyTime[]): CalendarBusyTime[] {
  const sorted = busyTimes
    .slice()
    .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

  const merged: CalendarBusyTime[] = [];
  for (const item of sorted) {
    const start = new Date(item.start);
    const end = new Date(item.end);
    if (!merged.length) {
      merged.push({ start: start.toISOString(), end: end.toISOString() });
      continue;
    }
    const last = merged[merged.length - 1];
    const lastEnd = new Date(last.end);
    if (start.getTime() <= lastEnd.getTime()) {
      if (end.getTime() > lastEnd.getTime()) {
        last.end = end.toISOString();
      }
    } else {
      merged.push({ start: start.toISOString(), end: end.toISOString() });
    }
  }

  return merged;
}

import { getPublicEventDetails } from "@/lib/api";
import { computeAvailability, AvailabilityConfig, TimeSlot } from "./compute";
import { getCalendarBusyTimes } from "./calendar";
import { convertSlotToTimezone } from "./timezone";

export interface AvailabilityParams {
  username: string;
  eventType: string;
  month: string;
  timezone?: string;
}

export interface AvailabilityResult {
  start: string;
  end: string;
  displayStart: string;
  displayEnd: string;
  timeZone: string;
}

export async function getEventTypeConfig(
  username: string,
  eventType: string
): Promise<AvailabilityConfig> {
  const details = await getPublicEventDetails(username, eventType);
  return {
    id: `${username}/${eventType}`,
    durationMinutes: details.duration_minutes,
    bufferBeforeMinutes: 0,
    bufferAfterMinutes: 0,
    minimumNoticeMinutes: 0,
    availability: {},
    exceptions: [],
    timeZone: details.timezone,
    user: {
      credentials: [],
    },
  };
}

export async function getExistingBookings(_params?: AvailabilityParams): Promise<TimeSlot[]> {
  // Public availability pages do not expose raw booking details.
  // Existing bookings are already reconciled by backend availability responses.
  return [];
}

export async function getAvailability(params: AvailabilityParams) {
  const config = await getEventTypeConfig(params.username, params.eventType);
  const existingBookings = await getExistingBookings(params);
  const calendarBusyTimes = await getCalendarBusyTimes(config);

  const slots = computeAvailability({
    config,
    existingBookings,
    calendarBusyTimes,
    params,
  });

  return formatForClient(slots, params.timezone || config.timeZone);
}

export function formatForClient(slots: TimeSlot[], displayTimezone: string): AvailabilityResult[] {
  return slots.map((slot) => {
    const converted = convertSlotToTimezone(slot, slot.timeZone || "UTC", displayTimezone);
    return {
      start: slot.start.toISOString(),
      end: slot.end.toISOString(),
      displayStart: converted.start.toISOString(),
      displayEnd: converted.end.toISOString(),
      timeZone: displayTimezone,
    };
  });
}

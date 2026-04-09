import { TimeSlot } from "./compute";

export function convertSlotToTimezone(
  slot: TimeSlot,
  fromTz: string,
  toTz: string
): TimeSlot {
  const start = convertDateToTimezone(slot.start, fromTz, toTz);
  const end = convertDateToTimezone(slot.end, fromTz, toTz);
  return { ...slot, start, end };
}

function convertDateToTimezone(date: Date, fromTz: string, toTz: string): Date {
  const iso = date.toISOString();
  const fromFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone: fromTz,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
  const parts = fromFormatter.formatToParts(new Date(iso));
  const dateParts = parts.reduce((acc, part) => {
    if (part.type !== "literal") acc[part.type] = part.value;
    return acc;
  }, {} as Record<string, string>);

  const localString = `${dateParts.year}-${dateParts.month}-${dateParts.day}T${dateParts.hour}:${dateParts.minute}:${dateParts.second}`;
  const tzOffset = getTimeZoneOffset(toTz, date);
  return new Date(`${localString}${tzOffset}`);
}

function getTimeZoneOffset(timeZone: string, date: Date): string {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    timeZoneName: "shortOffset",
  });
  const parts = formatter.formatToParts(date);
  const tzPart = parts.find((part) => part.type === "timeZoneName")?.value || "+00:00";
  const normalized = tzPart.replace("GMT", "").replace("UTC", "");
  return normalized || "+00:00";
}

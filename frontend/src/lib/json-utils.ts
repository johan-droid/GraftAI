/**
 * Safely parses a JSON string into a Record.
 * If parsing fails, logs a warning and returns the raw text in a special object.
 */
export function parseJsonSafe(text: string, status?: number): Record<string, unknown> {
  if (!text || text.trim() === "") {
    return {};
  }

  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch (e) {
    const preview = text.substring(0, 400) + (text.length > 400 ? "..." : "");
    console.warn(`[API] Failed to parse JSON response (Status: ${status || "unknown"}):`, {
      error: e instanceof Error ? e.message : String(e),
      preview,
    });
    return { __raw_text: preview };
  }
}

import { decode } from "msgpackr";

/**
 * High-Efficiency Binary Decoder for GraftAI.
 * Synchronizes with the backend's MessagePack-first architecture.
 */
export const msgpack = {
  /**
   * Decodes a binary buffer (ArrayBuffer, Uint8Array) into a JS Object.
   * Gracefully handles JSON fallbacks for legacy or mixed-mode streams.
   */
  decode: <T = unknown>(data: unknown): T => {
    try {
      // If it's already an object/string, return it (JSON fallback)
      if (typeof data === "string" || (typeof data === "object" && !(data instanceof ArrayBuffer) && !ArrayBuffer.isView(data))) {
        return typeof data === "string" ? JSON.parse(data) : data;
      }

      // Ensure we have a Uint8Array for msgpackr
      const buffer = data instanceof ArrayBuffer ? new Uint8Array(data) : data;
      return decode(buffer) as T;
    } catch (error) {
      console.warn("⚠️ Binary decoding failed, attempting raw return:", error);
      return data as T;
    }
  },

  /**
   * Safe JSON-or-Binary parser for EventSource (SSE) data.
   */
  parseEventData: <T = unknown>(eventData: string | Blob): Promise<T> => {
    return new Promise((resolve) => {
      if (eventData instanceof Blob) {
        const reader = new FileReader();
        reader.onload = () => {
          resolve(msgpack.decode<T>(reader.result));
        };
        reader.readAsArrayBuffer(eventData);
      } else {
        // SSE standard data: strings (could be base64 if we want, but usually it's JSON)
        try {
          resolve(JSON.parse(eventData));
        } catch {
          resolve(eventData as unknown as T);
        }
      }
    });
  }
};

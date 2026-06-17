"use client";

import { useCallback, useState } from "react";
import {
  PublicPaymentConfirmationResponse,
  PublicPaymentIntentResponse,
} from "@/lib/api";

interface PaymentOrchestratorState {
  intent: PublicPaymentIntentResponse | null;
  confirmed: boolean;
  loading: boolean;
  error: string | null;
  mode: "disabled" | "test" | "production" | "unknown";
}

interface UsePaymentOrchestratorReturn extends PaymentOrchestratorState {
  createIntent: (username: string, eventType: string) => Promise<PublicPaymentIntentResponse | null>;
  confirmIntent: (username: string, eventType: string, paymentMethod?: string) => Promise<boolean>;
  reset: () => void;
}

function isPaymentDisabledResponse(resp: unknown): boolean {
  if (!resp || typeof resp !== "object") return false;
  const r = resp as Record<string, unknown>;
  return r.payment_intent_id === "" || r.mode === "disabled" || r.status === "disabled";
}

export function usePaymentOrchestrator(): UsePaymentOrchestratorReturn {
  const [state, setState] = useState<PaymentOrchestratorState>({
    intent: null,
    confirmed: false,
    loading: false,
    error: null,
    mode: "unknown",
  });

  const createIntent = useCallback(
    async (username: string, eventType: string): Promise<PublicPaymentIntentResponse | null> => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const { createPublicPaymentIntent } = await import("@/lib/api");
        const intent = await createPublicPaymentIntent(username, eventType);
        if (isPaymentDisabledResponse(intent)) {
          setState((prev) => ({ ...prev, loading: false, mode: "disabled", error: "Payments are disabled for this deployment." }));
          return null;
        }
        const mode: "test" | "production" | "disabled" | "unknown" =
          intent.status === "initiated" || intent.status === "requires_confirmation"
            ? "test"
            : "production";
        setState((prev) => ({ ...prev, loading: false, intent, mode, error: null }));
        return intent;
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to create payment intent.";
        setState((prev) => ({ ...prev, loading: false, error: msg }));
        return null;
      }
    },
    []
  );

  const confirmIntent = useCallback(
    async (username: string, eventType: string, paymentMethod?: string): Promise<boolean> => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const { confirmPublicPaymentIntent } = await import("@/lib/api");
        const confirmation = await confirmPublicPaymentIntent(username, eventType, {
          payment_intent_id: state.intent?.payment_intent_id ?? "",
          payment_method: paymentMethod ?? "simulated_card",
        });
        if (confirmation.success && confirmation.payment_status === "succeeded") {
          setState((prev) => ({ ...prev, loading: false, confirmed: true }));
          return true;
        }
        setState((prev) => ({ ...prev, loading: false, error: "Payment confirmation failed." }));
        return false;
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Payment confirmation failed.";
        setState((prev) => ({ ...prev, loading: false, error: msg }));
        return false;
      }
    },
    [state.intent]
  );

  const reset = useCallback(() => {
    setState({ intent: null, confirmed: false, loading: false, error: null, mode: "unknown" });
  }, []);

  return { ...state, createIntent, confirmIntent, reset };
}

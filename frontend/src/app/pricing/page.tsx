"use client";

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Check,
  Cpu,
  Crown,
  Globe,
  Loader2,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { useAuth } from "@/app/providers/auth-provider";
import { enhancedApiClient } from "@/lib/api-client-enhanced";
import {
  MarketingCard,
  MarketingHero,
  MarketingSectionHeading,
  MarketingShell,
} from "@/components/marketing/MarketingShell";

type Tier = {
  id: string;
  name: string;
  price: string;
  amount?: number;
  currency?: string;
  description: string;
  features: string[];
  highlight: boolean;
  cta: string;
  icon: ReactNode;
};

interface BillingPlan {
  id: string;
  name?: string;
  price?: number | string;
  currency?: string;
  description?: string;
  features?: string[];
}

interface RazorpayCheckoutResponse {
  mode?: string;
  message?: string;
  order_id?: string;
  key?: string;
  amount?: number;
  currency?: string;
}

interface BillingMode {
  payment_mode?: string;
  can_simulate?: boolean;
  gateways?: Record<string, unknown>;
}

interface RazorpayHandlerResponse {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
}

interface RazorpayCheckoutOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  handler: (response: RazorpayHandlerResponse) => Promise<void>;
  prefill: { name: string; email: string };
  theme: { color: string };
}

interface RazorpayCheckoutInstance {
  on: (event: string, callback: (...args: unknown[]) => void) => void;
  open: () => void;
}

interface RazorpayWindow extends Window {
  Razorpay?: new (options: RazorpayCheckoutOptions) => RazorpayCheckoutInstance;
}

const TIERS: Tier[] = [
  {
    id: "free",
    name: "Standard",
    price: "$0",
    amount: 0,
    currency: "USD",
    description: "Perfect for managing your personal schedule and trying out AI assistance.",
    features: [
      "10 AI assistant messages per day",
      "Sync with Google and Outlook",
      "Standard processing speed",
      "Community support",
    ],
    highlight: false,
    cta: "Get started",
    icon: <Zap size={18} />,
  },
  {
    id: "pro",
    name: "Professional",
    price: "$19",
    amount: 19,
    currency: "USD",
    description: "The productivity engine for operators, consultants, and fast-moving individual teams.",
    features: [
      "200 AI assistant messages per day",
      "Priority processing speed",
      "Advanced time analytics",
      "Custom meeting templates",
      "Priority support",
    ],
    highlight: true,
    cta: "Upgrade to Pro",
    icon: <Crown size={18} />,
  },
  {
    id: "elite",
    name: "Enterprise",
    price: "$49",
    amount: 49,
    currency: "USD",
    description: "For teams that want deeper control, larger quotas, and a more tailored onboarding path.",
    features: [
      "Unlimited AI messages",
      "Unlimited tool access",
      "Early feature access",
      "Dedicated support",
      "Custom privacy controls",
    ],
    highlight: false,
    cta: "Contact us",
    icon: <Sparkles size={18} />,
  },
];

export default function PricingPage() {
  const [loadingTier, setLoadingTier] = useState<string | null>(null);
  const [billingMessage, setBillingMessage] = useState<string | null>(null);
  const [region, setRegion] = useState<"US" | "IN">("US");
  const { user } = useAuth();
  const [tiers, setTiers] = useState<Tier[]>(TIERS);
  const [billingInterval, setBillingInterval] = useState<"monthly" | "yearly">("monthly");
  const [billingMode, setBillingMode] = useState<null | BillingMode>(null);

  const getIconFor = (id: string) => {
    if (id === "free") return <Zap size={18} />;
    if (id === "pro") return <Crown size={18} />;
    return <Sparkles size={18} />;
  };

  const getPrice = useCallback(
    (tierId: string) => {
      if (tierId === "free") return "$0";
      if (region === "IN") return tierId === "pro" ? "₹499" : "₹1499";
      return tierId === "pro" ? "$19" : "$49";
    },
    [region],
  );

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const data = await enhancedApiClient.get<BillingPlan[]>("/billing/plans");
        if (Array.isArray(data) && data.length) {
          const mapped = data.map((plan) => ({
            id: plan.id,
            name: plan.name ?? plan.id,
            amount: typeof plan.price === "number" ? plan.price : undefined,
            currency: plan.currency ?? "USD",
            price:
              typeof plan.price === "number" && plan.currency
                ? plan.currency.toUpperCase() === "INR"
                  ? `₹${plan.price}`
                  : `$${plan.price}`
                : getPrice(plan.id),
            description: plan.description ?? "",
            features: Array.isArray(plan.features) ? plan.features : [],
            highlight: plan.id === "pro",
            cta:
              plan.id === "elite"
                ? "Contact us"
                : plan.id === "free"
                  ? "Get started"
                  : "Upgrade to Pro",
            icon: getIconFor(plan.id),
          }));
          setTiers(mapped);
        }
      } catch (error) {
        console.warn("Failed to fetch plans from backend, using fallback", error);
      }
    };

    fetchPlans();
  }, [getPrice]);

  const currencySymbol = (currency?: string) => {
    if (!currency) return "$";
    if (currency.toUpperCase() === "INR") return "₹";
    if (currency.toUpperCase() === "USD") return "$";
    return `${currency} `;
  };

  const formatPrice = (tier: Tier) => {
    const amount = (tier.amount ?? Number(String(tier.price).replace(/[^0-9.]/g, ""))) || 0;
    const currency = tier.currency ?? "USD";
    if (billingInterval === "monthly") {
      return `${currencySymbol(currency)}${amount}`;
    }
    const yearly = Math.round(amount * 12 * 0.83);
    return `${currencySymbol(currency)}${yearly}`;
  };

  useEffect(() => {
    const detectRegion = async () => {
      try {
        const response = await fetch("https://ipapi.co/json/");
        const data = await response.json();
        if (data.country_code === "IN") setRegion("IN");
      } catch (error) {
        console.warn("Failed to detect region:", error);
      }
    };

    const fetchBillingMode = async () => {
      try {
        const response = await fetch("/billing/mode");
        if (response.ok) {
          const data = await response.json();
          setBillingMode(data);
        }
      } catch {
        // Ignore mode fetch failures in the marketing shell.
      }
    };

    detectRegion();
    fetchBillingMode();
  }, []);

  const handleSelectTier = async (tierId: string) => {
    if (tierId === "free") {
      window.location.href = "/dashboard";
      return;
    }

    if (tierId === "elite") {
      setBillingMessage("Enterprise onboarding starts with a quick conversation with our team.");
      return;
    }

    if (!user) {
      window.location.href = `/login?redirect=${encodeURIComponent("/pricing")}`;
      return;
    }

    setLoadingTier(tierId);

    try {
      if (region === "IN") {
        const response = await enhancedApiClient.post<RazorpayCheckoutResponse>("/billing/razorpay/checkout", {
          tier: tierId,
        });

        if (response?.mode === "disabled" || response?.mode === "manual") {
          setBillingMessage(response?.message || "Payments are not available for this deployment.");
          return;
        }

        if (response?.mode === "simulation") {
          try {
            await enhancedApiClient.post("/billing/razorpay/verify", {
              razorpay_payment_id: `${response.order_id}_sim_pay`,
              razorpay_order_id: response.order_id,
              razorpay_signature: "sim_signature",
            });
            window.location.assign("/dashboard/settings/billing?success=true");
            return;
          } catch {
            setBillingMessage("Simulation verification failed. Please refresh and try again.");
            return;
          }
        }

        const loadRazorpay = () =>
          new Promise<boolean>((resolve, reject) => {
            if (typeof window === "undefined") return reject(false);
            const windowRazorpay = window as RazorpayWindow;
            if (windowRazorpay.Razorpay) return resolve(true);

            const existingScript = document.getElementById("razorpay-sdk");
            if (existingScript) return resolve(true);

            const script = document.createElement("script");
            script.id = "razorpay-sdk";
            script.src = "https://checkout.razorpay.com/v1/checkout.js";
            script.onload = () => resolve(true);
            script.onerror = () => reject(false);
            document.body.appendChild(script);
          });

        await loadRazorpay();

        if (!response.key || typeof response.amount !== "number" || !response.order_id) {
          throw new Error("Razorpay checkout response is missing required payment information.");
        }

        const options: RazorpayCheckoutOptions = {
          key: response.key,
          amount: response.amount,
          currency: response.currency || "INR",
          name: "GraftAI",
          description: tierId === "pro" ? "Professional Subscription" : "Enterprise Subscription",
          order_id: response.order_id,
          handler: async (handlerResponse: RazorpayHandlerResponse) => {
            try {
              await enhancedApiClient.post("/billing/razorpay/verify", handlerResponse);
              window.location.assign("/dashboard/settings/billing?success=true");
            } catch {
              setBillingMessage("Payment verification failed. Contact support.");
            }
          },
          prefill: { name: user?.full_name ?? "", email: user?.email ?? "" },
          theme: { color: "#1A73E8" },
        };

        const windowRazorpay = window as RazorpayWindow;
        if (!windowRazorpay.Razorpay) {
          throw new Error("Razorpay script failed to load.");
        }

        const checkout = new windowRazorpay.Razorpay(options);
        checkout.on("payment.failed", () => {
          setBillingMessage("Payment failed or was cancelled.");
        });
        checkout.open();
        return;
      }

      const response = await enhancedApiClient.post<{ checkout_url: string; session_id: string }>(
        "/billing/stripe/create-checkout-session",
      );
      if (!response.checkout_url) {
        throw new Error("Stripe checkout is not available right now.");
      }
      window.location.assign(response.checkout_url);
    } catch (error: unknown) {
      const resolvedError =
        error instanceof Error ? error : new Error("Connection issue during checkout. Please try again.");
      setBillingMessage(resolvedError.message);
    } finally {
      setLoadingTier(null);
    }
  };

  return (
    <MarketingShell currentPath="/pricing">
      <MarketingHero
        eyebrow="Pricing"
        title="Plans that keep the premium feel without turning the math into work."
        description="The pricing page now matches the same cinematic product surface as the landing and documentation pages, while still preserving real region-aware checkout logic, quota framing, and trust signals."
        primaryAction={
          <Link
            href="/signup"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-[#1A73E8] px-6 py-3 text-sm font-semibold text-white shadow-[0_16px_34px_-22px_rgba(26,115,232,0.9)] transition-all hover:bg-[#1557B0]"
          >
            Start for free <ArrowRight size={16} />
          </Link>
        }
        secondaryAction={
          <Link
            href="/docs"
            className="inline-flex items-center justify-center rounded-full border border-[#DADCE0] bg-white px-6 py-3 text-sm font-semibold text-[#5F6368] transition-colors hover:bg-[#F8F9FA] hover:text-[#202124]"
          >
            Explore documentation
          </Link>
        }
        stats={[
          { label: "Free plan", value: "10 AI / day" },
          { label: "Pro plan", value: "200 AI / day" },
          { label: "Checkout", value: region === "IN" ? "Razorpay" : "Stripe" },
        ]}
        aside={
          <MarketingCard className="h-full">
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
              Billing controls
            </p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[#202124]">
              Regional pricing, annual savings, and deployment mode at a glance.
            </h2>

            <div className="mt-6 space-y-5">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                  Region
                </p>
                <div className="mt-3 flex gap-2">
                  {[
                    { value: "US", label: "Global" },
                    { value: "IN", label: "India" },
                  ].map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setRegion(option.value as "US" | "IN")}
                      className={`rounded-full px-4 py-2 text-sm font-semibold transition-all ${
                        region === option.value
                          ? "bg-[#202124] text-white shadow-sm"
                          : "border border-[#DADCE0] bg-white text-[#5F6368] hover:bg-[#F8F9FA] hover:text-[#202124]"
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
                  Billing cadence
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {[
                    { value: "monthly", label: "Monthly" },
                    { value: "yearly", label: "Yearly" },
                  ].map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setBillingInterval(option.value as "monthly" | "yearly")}
                      className={`rounded-full px-4 py-2 text-sm font-semibold transition-all ${
                        billingInterval === option.value
                          ? "bg-[#202124] text-white shadow-sm"
                          : "border border-[#DADCE0] bg-white text-[#5F6368] hover:bg-[#F8F9FA] hover:text-[#202124]"
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="rounded-[28px] border border-[#DADCE0] bg-[#202124] p-5 text-white shadow-[0_30px_70px_-44px_rgba(32,33,36,0.86)]">
                <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-white/60">
                  Environment
                </p>
                <div className="mt-4 grid gap-3">
                  <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-white/90">
                    {billingMode?.payment_mode === "test"
                      ? "Sandbox mode enabled for safe checkout testing."
                      : billingMode?.payment_mode === "disabled"
                        ? "Payments are disabled for this deployment."
                        : "Live billing path available for supported regions."}
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-white/90">
                    {billingInterval === "yearly"
                      ? "Annual billing applies an approximate 17% savings."
                      : "Monthly billing keeps the entry point lighter for new teams."}
                  </div>
                </div>
              </div>

              {billingMessage ? (
                <div className="rounded-[24px] border border-[#D2E3FC] bg-[#EDF4FF] px-4 py-4 text-sm font-medium text-[#1967D2]">
                  {billingMessage}
                </div>
              ) : null}
            </div>
          </MarketingCard>
        }
      />

      <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-12">
        <MarketingSectionHeading
          kicker="Plan lineup"
          title="Clear tiers, stronger hierarchy, and less visual friction."
          description="Each plan card now lives inside the same premium public design system, with the featured tier standing out through depth and motion rather than noise."
        />

        {(billingMode?.payment_mode === "test" || billingMode?.payment_mode === "disabled") && (
          <MarketingCard className="mt-8">
            <p className="text-sm font-semibold text-[#202124]">
              {billingMode.payment_mode === "test"
                ? "Sandbox mode is active."
                : "Payments are disabled for this deployment."}
            </p>
            <p className="mt-2 text-sm leading-relaxed text-[#5F6368]">
              {billingMode.payment_mode === "test"
                ? "No real charges will be processed. Use this mode to validate checkout and webhook flows safely."
                : "You can still review plans and request a manual upgrade path while checkout remains unavailable."}
            </p>
          </MarketingCard>
        )}

        <div className="mt-10 grid gap-4 lg:grid-cols-3">
          {tiers.map((tier, index) => (
            <motion.div
              key={tier.id}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.45, delay: index * 0.06 }}
            >
              <MarketingCard
                className={`h-full ${tier.highlight ? "border-[#D2E3FC] bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(237,244,255,0.9))]" : ""}`}
              >
                {tier.highlight ? (
                  <div className="mb-5 inline-flex rounded-full bg-[#202124] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.28em] text-white">
                    Most popular
                  </div>
                ) : null}

                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-[#E8F0FE] text-[#1967D2]">
                      {tier.icon}
                    </div>
                    <h3 className="mt-5 text-2xl font-semibold tracking-tight text-[#202124]">{tier.name}</h3>
                  </div>
                  {tier.highlight ? (
                    <div className="rounded-full border border-[#D2E3FC] bg-white px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#1967D2]">
                      Recommended
                    </div>
                  ) : null}
                </div>

                <div className="mt-5 flex items-end gap-2">
                  <p className="text-4xl font-semibold tracking-tight text-[#202124]">{formatPrice(tier)}</p>
                  <p className="pb-1 text-sm text-[#5F6368]">
                    {billingInterval === "monthly" ? "/ month" : "/ year"}
                  </p>
                </div>
                {billingInterval === "yearly" && tier.amount && tier.amount > 0 ? (
                  <p className="mt-2 text-sm font-medium text-[#1967D2]">Billed annually for a lighter effective monthly rate.</p>
                ) : null}
                <p className="mt-4 text-sm leading-relaxed text-[#5F6368]">{tier.description}</p>

                <div className="mt-6 grid gap-2">
                  {tier.features.map((feature) => (
                    <div
                      key={feature}
                      className="flex items-start gap-3 rounded-2xl border border-[#E5EAF1] bg-white/85 px-4 py-3"
                    >
                      <div className="mt-0.5 text-[#1A73E8]">
                        <Check size={16} />
                      </div>
                      <p className="text-sm font-medium text-[#202124]">{feature}</p>
                    </div>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => handleSelectTier(tier.id)}
                  disabled={!!loadingTier}
                  className={`mt-8 inline-flex w-full items-center justify-center gap-2 rounded-full px-5 py-3 text-sm font-semibold transition-all ${
                    tier.highlight
                      ? "bg-[#1A73E8] text-white shadow-[0_16px_34px_-22px_rgba(26,115,232,0.9)] hover:bg-[#1557B0]"
                      : "border border-[#DADCE0] bg-white text-[#202124] hover:bg-[#F8F9FA]"
                  } disabled:cursor-not-allowed disabled:opacity-70`}
                >
                  {loadingTier === tier.id ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
                  {tier.cta}
                </button>
              </MarketingCard>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-12 sm:px-6 sm:pb-16">
        <div className="grid gap-4 lg:grid-cols-3">
          {[
            {
              icon: ShieldCheck,
              title: "Privacy first",
              text: "Keep billing trust aligned with the rest of the product story through encrypted handling, secure cookies, and guarded token flows.",
            },
            {
              icon: Cpu,
              title: "Fast sync",
              text: "High-frequency calendar updates and automation handoffs keep scheduling state feeling current instead of stale.",
            },
            {
              icon: Globe,
              title: "Works globally",
              text: "Regional checkout paths, timezone-aware scheduling, and stable availability make the platform usable across geographies.",
            },
          ].map((item, index) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.45, delay: index * 0.05 }}
              >
                <MarketingCard className="h-full">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#E8F0FE] text-[#1967D2]">
                    <Icon size={20} />
                  </div>
                  <h3 className="mt-5 text-xl font-semibold tracking-tight text-[#202124]">{item.title}</h3>
                  <p className="mt-4 text-sm leading-relaxed text-[#5F6368]">{item.text}</p>
                </MarketingCard>
              </motion.div>
            );
          })}
        </div>

        <div className="mt-10 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <MarketingCard>
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
              Market view
            </p>
            <h3 className="mt-3 text-2xl font-semibold tracking-tight text-[#202124]">
              Value stays legible against typical alternatives.
            </h3>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-[#5F6368]">
              This comparison is illustrative, but it helps show where GraftAI’s AI quota and scheduling polish land
              relative to common market pricing bands.
            </p>
            <div className="mt-6 grid gap-3 md:grid-cols-3">
              {[
                { name: "GraftAI Pro", price: "$19 / month", text: "200 AI messages per day, priority processing, analytics, integrations." },
                { name: "Competitor A", price: "$29 / month", text: "Similar AI framing, but a higher entry price for comparable workflow depth." },
                { name: "Competitor B", price: "$24 / month", text: "Mid-range feature set with less generous AI usage at the same level." },
              ].map((plan) => (
                <div
                  key={plan.name}
                  className="rounded-[28px] border border-[#E5EAF1] bg-white/90 px-5 py-5 shadow-[0_14px_34px_-28px_rgba(32,33,36,0.32)]"
                >
                  <p className="text-sm font-semibold text-[#202124]">{plan.name}</p>
                  <p className="mt-2 text-sm font-medium text-[#1967D2]">{plan.price}</p>
                  <p className="mt-3 text-sm leading-relaxed text-[#5F6368]">{plan.text}</p>
                </div>
              ))}
            </div>
          </MarketingCard>

          <MarketingCard>
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-[#5F6368]">
              Need a custom path?
            </p>
            <h3 className="mt-3 text-2xl font-semibold tracking-tight text-[#202124]">
              Manual onboarding still has a clean home.
            </h3>
            <p className="mt-4 text-sm leading-relaxed text-[#5F6368]">
              Teams that need procurement help, policy review, or a custom rollout can continue through the manual
              request flow without losing the polished public journey.
            </p>
            <div className="mt-6 rounded-[28px] border border-[#DADCE0] bg-[#202124] p-5 text-white">
              <div className="grid gap-3">
                {["Custom rollout support", "Billing environment review", "Enterprise onboarding handoff"].map((item) => (
                  <div
                    key={item}
                    className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-white/90"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </div>
            <Link
              href="/pricing/manual-request"
              className="mt-6 inline-flex items-center gap-2 rounded-full bg-[#1A73E8] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#1557B0]"
            >
              Open manual request <ArrowRight size={16} />
            </Link>
          </MarketingCard>
        </div>
      </section>
    </MarketingShell>
  );
}


"use client";

import type { ComponentPropsWithoutRef, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

type BentoTone = "blue" | "green" | "amber" | "violet" | "slate";

const toneStyles: Record<
  BentoTone,
  {
    accent: string;
    badge: string;
    eyebrow: string;
  }
> = {
  blue: {
    accent: "bg-[#1A73E8]",
    badge: "bg-[#E8F0FE] text-[#1967D2]",
    eyebrow: "text-[#1967D2]",
  },
  green: {
    accent: "bg-[#34A853]",
    badge: "bg-[#E6F4EA] text-[#137333]",
    eyebrow: "text-[#137333]",
  },
  amber: {
    accent: "bg-[#E37400]",
    badge: "bg-[#FEF7E0] text-[#E37400]",
    eyebrow: "text-[#E37400]",
  },
  violet: {
    accent: "bg-[#D93025]",
    badge: "bg-[#FDE7E9] text-[#D93025]",
    eyebrow: "text-[#D93025]",
  },
  slate: {
    accent: "bg-[#5F6368]",
    badge: "bg-[#F1F3F4] text-[#5F6368]",
    eyebrow: "text-[#5F6368]",
  },
};

interface BentoCardProps extends ComponentPropsWithoutRef<"article"> {
  title: string;
  description?: string;
  eyebrow?: string;
  icon?: LucideIcon;
  tone?: BentoTone;
  children?: ReactNode;
}

export function BentoCard({
  title,
  description,
  eyebrow,
  icon: Icon,
  tone = "slate",
  children,
  className = "",
  ...props
}: BentoCardProps) {
  const palette = toneStyles[tone];

  return (
    <article
      className={`relative overflow-hidden rounded-[36px] border border-[#DADCE0] bg-white/90 p-6 shadow-[0_28px_90px_-56px_rgba(32,33,36,0.46)] backdrop-blur-2xl ${className}`}
      {...props}
    >
      <div className={`absolute inset-x-0 top-0 h-1 ${palette.accent}`} />
      <div className="relative z-10">
        <div className="flex items-start gap-4">
          {Icon ? (
            <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-[18px] ${palette.badge}`}>
              <Icon size={18} />
            </div>
          ) : null}

          <div className="min-w-0 flex-1">
            {eyebrow ? (
              <p className={`text-[10px] font-semibold uppercase tracking-[0.28em] ${palette.eyebrow}`}>
                {eyebrow}
              </p>
            ) : null}
            <h3 className="mt-2 text-lg font-medium tracking-tight text-[#202124] sm:text-xl">
              {title}
            </h3>
          </div>
        </div>

        {description ? (
          <p className="mt-4 text-sm leading-relaxed text-[#5F6368]">
            {description}
          </p>
        ) : null}

        {children ? <div className="mt-5">{children}</div> : null}
      </div>
    </article>
  );
}

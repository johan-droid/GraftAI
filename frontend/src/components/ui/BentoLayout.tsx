"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export type BentoLayoutProps = React.HTMLAttributes<HTMLDivElement>;

export const BentoLayout = React.forwardRef<HTMLDivElement, BentoLayoutProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "grid gap-4 auto-rows-min",
          "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

BentoLayout.displayName = "BentoLayout";

export default BentoLayout;

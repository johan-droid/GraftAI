"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface BentoItemProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: string;
}

export const BentoItem = React.forwardRef<HTMLDivElement, BentoItemProps>(
  ({ className, children, cols, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "min-h-[120px] flex flex-col",
          cols,
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

BentoItem.displayName = "BentoItem";

export default BentoItem;

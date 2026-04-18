import * as React from "react"
import { cn } from "@/lib/utils"

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-xl border border-[#DADCE0] bg-white px-3 py-2 text-sm text-[#202124] ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-[#80868B] focus-visible:outline-none focus-visible:border-[#1A73E8] focus-visible:ring-2 focus-visible:ring-[#D2E3FC] disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }

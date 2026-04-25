import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { Loader2 } from "lucide-react"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 relative",
  {
    variants: {
      variant: {
        default: "bg-[#1A73E8] text-white shadow-sm hover:bg-[#1558B0] active:bg-[#174EA6]",
        destructive: "bg-red-500 text-white hover:bg-red-600 shadow-sm",
        outline: "border border-[#DADCE0] bg-white text-[#202124] hover:bg-[#F8F9FA]",
        secondary: "border border-transparent bg-[#F1F3F4] text-[#202124] hover:bg-[#E8EAED]",
        ghost: "text-[#5F6368] hover:bg-[#F1F3F4] hover:text-[#202124]",
        link: "text-[#1A73E8] underline-offset-4 hover:underline",
        primary: "bg-[#1A73E8] text-white shadow-sm hover:bg-[#1558B0] active:bg-[#174EA6]",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-11 rounded-xl px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => Promise<void> | void
  loadingText?: string
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, onClick, disabled, loadingText, ...props }, ref) => {
    const [isInternalLoading, setIsInternalLoading] = React.useState(false)

    const handleClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
      if (!onClick || isInternalLoading || disabled) return

      try {
        const result = onClick(e)
        // If the onClick is an async function (returns a promise), await it
        if (result instanceof Promise) {
          setIsInternalLoading(true)
          await result
        }
      } catch (error: any) {
        // Automatically catch unhandled UI errors
        console.error("Action failed:", error)
        // Note: Toast notification requires toast hook, which would need to be passed in
        // For now, we'll just log to console
      } finally {
        setIsInternalLoading(false)
      }
    }

    const isLoading = isInternalLoading
    const isDisabled = disabled || isLoading
    const showLoadingUI = isLoading && !asChild

    const Comp = asChild ? Slot : "button"
    
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        onClick={handleClick}
        disabled={isDisabled}
        {...props}
      >
        {showLoadingUI && (
          <Loader2 className="absolute left-4 w-4 h-4 animate-spin" />
        )}
        
        <span className={cn(showLoadingUI ? 'opacity-0' : 'opacity-100', 'transition-opacity')}>
          {props.children}
        </span>

        {showLoadingUI && (
          <span className="absolute">
            {loadingText || "Processing..."}
          </span>
        )}
      </Comp>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }

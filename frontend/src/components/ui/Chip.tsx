/**
 * Material Design 3 Chip Component
 * 
 * Chips are compact elements that represent an input, attribute, or action.
 * 
 * Types:
 * - Assist: Guides users through a task (e.g., category selection)
 * - Filter: Allows selection from a set of options
 * - Input: Represents user-provided information
 * - Suggestion: Offers suggestions based on user input
 * 
 * @see https://m3.material.io/components/chips/overview
 */

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { X, Check } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";

type ChipType = "assist" | "filter" | "input" | "suggestion";
type ChipSize = "small" | "medium" | "large";

interface ChipProps {
  label: string;
  type?: ChipType;
  size?: ChipSize;
  selected?: boolean;
  disabled?: boolean;
  elevated?: boolean;
  icon?: React.ReactNode;
  avatar?: React.ReactNode;
  onClick?: () => void;
  onRemove?: () => void;
  className?: string;
}

export function Chip({
  label,
  type = "assist",
  size = "medium",
  selected = false,
  disabled = false,
  elevated = false,
  icon,
  avatar,
  onClick,
  onRemove,
  className = "",
}: ChipProps) {
  const { mode } = useTheme();
  const isDark = mode === "dark";
  const [isPressed, setIsPressed] = useState(false);

  // Size configurations (following M3 touch targets)
  const sizeStyles = {
    small: {
      height: "h-7",
      padding: "px-2",
      text: "text-xs",
      icon: "w-4 h-4",
      gap: "gap-1",
    },
    medium: {
      height: "h-8",
      padding: "px-3",
      text: "text-sm",
      icon: "w-4 h-4",
      gap: "gap-1.5",
    },
    large: {
      height: "h-10",
      padding: "px-4",
      text: "text-sm",
      icon: "w-5 h-5",
      gap: "gap-2",
    },
  };

  const styles = sizeStyles[size];

  // Type-specific styling
  const getTypeStyles = () => {
    const base = `inline-flex items-center justify-center rounded-lg transition-all duration-150 select-none ${styles.height} ${styles.padding} ${styles.gap} ${styles.text} font-medium`;
    
    if (disabled) {
      return `${base} cursor-not-allowed opacity-38 ${
        isDark 
          ? "bg-[#49454F]/30 text-[#E6E1E5]/50" 
          : "bg-[#E6E1E5]/50 text-[#1D1B20]/50"
      }`;
    }

    if (type === "input" && onRemove) {
      return `${base} cursor-pointer ${
        isDark 
          ? "bg-[#49454F] text-[#E6E1E5] hover:bg-[#5A5662] active:bg-[#6B6670]" 
          : "bg-[#E6E1E5] text-[#1D1B20] hover:bg-[#D8D3D8] active:bg-[#CAC5CA]"
      }`;
    }

    if (type === "filter" || type === "suggestion") {
      if (selected) {
        return `${base} cursor-pointer ${
          isDark 
            ? "bg-[#004878] text-[#D7E3FC] border border-[#AAC7FF]" 
            : "bg-[#1A73E8] text-white border border-[#1A73E8]"
        }`;
      }
      return `${base} cursor-pointer border ${
        isDark 
          ? "bg-[#1C1B1F] text-[#E6E1E5] border-[#49454F] hover:bg-[#2D2D30] active:bg-[#3D3D40]" 
          : "bg-white text-[#1D1B20] border-[#DADCE0] hover:bg-[#F8F9FA] active:bg-[#F1F3F4]"
      }`;
    }

    // Assist chip (default)
    return `${base} cursor-pointer border ${
      elevated 
        ? isDark 
          ? "bg-[#1C1B1F] text-[#E6E1E5] border-transparent shadow-md shadow-black/20" 
          : "bg-white text-[#1D1B20] border-transparent shadow-md shadow-black/10"
        : isDark 
          ? "bg-[#1C1B1F] text-[#E6E1E5] border-[#49454F] hover:bg-[#2D2D30] active:bg-[#3D3D40]" 
          : "bg-white text-[#1D1B20] border-[#DADCE0] hover:bg-[#F8F9FA] active:bg-[#F1F3F4]"
    }`;
  };

  const showCheckmark = (type === "filter" || type === "suggestion") && selected;
  const showRemove = type === "input" && onRemove;

  return (
    <motion.button
      type="button"
      disabled={disabled}
      onClick={onClick}
      onTapStart={() => setIsPressed(true)}
      onTap={() => setIsPressed(false)}
      whileTap={!disabled ? { scale: 0.97 } : undefined}
      className={`${getTypeStyles()} ${className}`}
      style={{ minWidth: "48px" }}
    >
      {/* Leading Icon or Avatar */}
      {showCheckmark ? (
        <motion.span
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className={`${styles.icon} ${isDark ? "text-[#D7E3FC]" : "text-white"}`}
        >
          <Check size={16} strokeWidth={2.5} />
        </motion.span>
      ) : avatar ? (
        <span className="shrink-0">{avatar}</span>
      ) : icon ? (
        <span className={`${styles.icon} shrink-0 ${isDark ? "text-[#AAC7FF]" : "text-[#1A73E8]"}`}>
          {icon}
        </span>
      ) : null}

      {/* Label */}
      <span className="truncate max-w-[120px]">{label}</span>

      {/* Remove Button (for input chips) */}
      {showRemove && (
        <motion.button
          type="button"
          whileTap={{ scale: 0.8 }}
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className={`
            -mr-1 p-0.5 rounded-full transition-colors
            ${isDark 
              ? "hover:bg-[#E6E1E5]/20 text-[#E6E1E5]/70" 
              : "hover:bg-[#1D1B20]/10 text-[#1D1B20]/70"
            }
          `}
          aria-label={`Remove ${label}`}
        >
          <X size={14} strokeWidth={2} />
        </motion.button>
      )}
    </motion.button>
  );
}

// Chip Group Component for managing multiple chips
interface ChipGroupProps {
  children: React.ReactNode;
  direction?: "horizontal" | "vertical";
  wrap?: boolean;
  gap?: "small" | "medium" | "large";
  className?: string;
}

export function ChipGroup({
  children,
  direction = "horizontal",
  wrap = true,
  gap = "small",
  className = "",
}: ChipGroupProps) {
  const gapStyles = {
    small: direction === "horizontal" ? "gap-1.5" : "gap-1.5",
    medium: direction === "horizontal" ? "gap-2" : "gap-2",
    large: direction === "horizontal" ? "gap-3" : "gap-3",
  };

  const directionStyles = {
    horizontal: "flex-row",
    vertical: "flex-col",
  };

  return (
    <div
      className={`
        flex ${directionStyles[direction]} ${gapStyles[gap]} ${wrap ? "flex-wrap" : ""}
        ${className}
      `}
      role="group"
    >
      {children}
    </div>
  );
}

// Filter Chip Group with single/multiple selection support
interface FilterChipGroupProps {
  options: Array<{ value: string; label: string; icon?: React.ReactNode }>;
  selected: string[];
  onChange: (selected: string[]) => void;
  multiple?: boolean;
  size?: ChipSize;
  className?: string;
}

export function FilterChipGroup({
  options,
  selected,
  onChange,
  multiple = false,
  size = "medium",
  className = "",
}: FilterChipGroupProps) {
  const handleSelect = (value: string) => {
    if (multiple) {
      if (selected.includes(value)) {
        onChange(selected.filter((v) => v !== value));
      } else {
        onChange([...selected, value]);
      }
    } else {
      onChange(selected.includes(value) ? [] : [value]);
    }
  };

  return (
    <ChipGroup wrap className={className}>
      {options.map((option) => (
        <Chip
          key={option.value}
          label={option.label}
          type="filter"
          size={size}
          selected={selected.includes(option.value)}
          icon={option.icon}
          onClick={() => handleSelect(option.value)}
        />
      ))}
    </ChipGroup>
  );
}

export default Chip;

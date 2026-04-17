/**
 * Material Design 3 List Item Component
 * 
 * List items display a row of information with optional leading/trailing elements.
 * Optimized for mobile with 48dp+ touch targets.
 * 
 * @see https://m3.material.io/components/lists/overview
 */

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useTheme } from "@/contexts/ThemeContext";

type ListItemType = "oneLine" | "twoLine" | "threeLine";
type ListItemVariant = "default" | "active" | "disabled";

interface ListItemProps {
  // Content
  headline: React.ReactNode;
  supportingText?: React.ReactNode;
  overline?: React.ReactNode;
  
  // Visual elements
  leadingElement?: React.ReactNode;
  trailingElement?: React.ReactNode;
  
  // Configuration
  type?: ListItemType;
  variant?: ListItemVariant;
  selected?: boolean;
  disabled?: boolean;
  
  // Interaction
  onClick?: () => void;
  href?: string;
  
  // Styling
  className?: string;
  
  // Swipe actions (mobile)
  swipeLeft?: {
    icon: React.ReactNode;
    color: string;
    onSwipe: () => void;
    label?: string;
  };
  swipeRight?: {
    icon: React.ReactNode;
    color: string;
    onSwipe: () => void;
    label?: string;
  };
}

export function ListItem({
  headline,
  supportingText,
  overline,
  leadingElement,
  trailingElement,
  type = "oneLine",
  variant = "default",
  selected = false,
  disabled = false,
  onClick,
  href,
  className = "",
}: ListItemProps) {
  const { mode } = useTheme();
  const isDark = mode === "dark";
  const [isPressed, setIsPressed] = useState(false);

  // Container styles based on variant
  const getContainerStyles = () => {
    const base = "group flex items-center w-full transition-all duration-150";
    
    if (disabled) {
      return `${base} cursor-not-allowed opacity-38 ${
        isDark ? "text-[#E6E1E5]/50" : "text-[#1D1B20]/50"
      }`;
    }

    if (selected) {
      return `${base} cursor-pointer ${
        isDark 
          ? "bg-[#004878]/30 text-[#D7E3FC]" 
          : "bg-[#1A73E8]/10 text-[#1A73E8]"
      }`;
    }

    if (variant === "active") {
      return `${base} cursor-pointer ${
        isDark 
          ? "bg-[#1C1B1F] text-[#E6E1E5] hover:bg-[#2D2D30] active:bg-[#3D3D40]" 
          : "bg-white text-[#1D1B20] hover:bg-[#F8F9FA] active:bg-[#F1F3F4]"
      }`;
    }

    // Default
    return `${base} cursor-pointer ${
      isDark 
        ? "text-[#E6E1E5] hover:bg-[#2D2D30]/50 active:bg-[#3D3D40]/50" 
        : "text-[#1D1B20] hover:bg-[#F8F9FA] active:bg-[#F1F3F4]"
    }`;
  };

  // Height based on type (M3 specifications)
  const heightStyles = {
    oneLine: "min-h-[56px] sm:min-h-[48px] py-2",
    twoLine: "min-h-[72px] py-3",
    threeLine: "min-h-[88px] py-3",
  };

  // Padding and gap
  const layoutStyles = "px-4 gap-3 sm:gap-4";

  // Render content based on href or onClick
  const Component = href ? motion.a : motion.button;
  const componentProps = href 
    ? { href } 
    : { onClick, type: "button" as const };

  return (
    <Component
      {...componentProps}
      disabled={disabled}
      whileTap={!disabled ? { scale: 0.995 } : undefined}
      onTapStart={() => setIsPressed(true)}
      onTap={() => setIsPressed(false)}
      className={`
        ${getContainerStyles()}
        ${heightStyles[type]}
        ${layoutStyles}
        ${className}
      `}
      style={{ touchAction: "manipulation" }}
    >
      {/* Leading Element */}
      {leadingElement && (
        <div className="shrink-0 flex items-center justify-center">
          {leadingElement}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 min-w-0 flex flex-col justify-center">
        {/* Overline */}
        {overline && (
          <span className={`
            text-xs font-medium uppercase tracking-wide mb-0.5
            ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}
          `}>
            {overline}
          </span>
        )}

        {/* Headline */}
        <div className={`
          font-medium truncate
          ${type === "oneLine" ? "text-sm sm:text-base" : "text-sm sm:text-base"}
        `}>
          {headline}
        </div>

        {/* Supporting Text */}
        {supportingText && type !== "oneLine" && (
          <div className={`
            truncate text-sm mt-0.5
            ${isDark ? "text-[#C9C5CA]" : "text-[#5F6368]"}
            ${type === "threeLine" ? "line-clamp-2" : ""}
          `}>
            {supportingText}
          </div>
        )}
      </div>

      {/* Trailing Element */}
      {trailingElement && (
        <div className="shrink-0 flex items-center">
          {trailingElement}
        </div>
      )}
    </Component>
  );
}

// List Group Component
interface ListGroupProps {
  children: React.ReactNode;
  className?: string;
  divider?: boolean;
}

export function ListGroup({
  children,
  className = "",
  divider = true,
}: ListGroupProps) {
  const { mode } = useTheme();
  const isDark = mode === "dark";

  return (
    <div 
      className={`
        rounded-xl overflow-hidden
        ${isDark ? "bg-[#1C1B1F]" : "bg-white"}
        ${className}
      `}
      role="list"
    >
      {children}
    </div>
  );
}

// List Section with Header
interface ListSectionProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function ListSection({
  title,
  children,
  className = "",
  collapsible = false,
  defaultExpanded = true,
}: ListSectionProps) {
  const { mode } = useTheme();
  const isDark = mode === "dark";
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div className={className}>
      {title && (
        <div className="px-4 py-3">
          <h3 className={`
            text-sm font-medium uppercase tracking-wide
            ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}
          `}>
            {title}
          </h3>
        </div>
      )}
      <ListGroup>
        {children}
      </ListGroup>
    </div>
  );
}

// Simple one-line list item shorthand
export function SimpleListItem({
  text,
  secondaryText,
  icon,
  onClick,
  className,
}: {
  text: string;
  secondaryText?: string;
  icon?: React.ReactNode;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <ListItem
      headline={text}
      supportingText={secondaryText}
      leadingElement={icon}
      type={secondaryText ? "twoLine" : "oneLine"}
      onClick={onClick}
      className={className}
    />
  );
}

export default ListItem;

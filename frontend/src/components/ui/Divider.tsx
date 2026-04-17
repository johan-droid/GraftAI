/**
 * Material Design 3 Divider Component
 * 
 * Dividers are thin lines that group content in lists and layouts.
 * 
 * Types:
 * - Full-width: Extends the full width of the container
 * - Inset: Indented from the left edge (for lists with icons/avatars)
 * - Middle: Centered and shorter width (for separating sections)
 * 
 * @see https://m3.material.io/components/dividers/overview
 */

"use client";

import { useTheme } from "@/contexts/ThemeContext";

type DividerType = "fullWidth" | "inset" | "middle";
type DividerThickness = "thin" | "thick";

interface DividerProps {
  type?: DividerType;
  thickness?: DividerThickness;
  vertical?: boolean;
  className?: string;
  
  // Text divider variant
  text?: string;
  textPosition?: "left" | "center" | "right";
}

export function Divider({
  type = "fullWidth",
  thickness = "thin",
  vertical = false,
  className = "",
  text,
  textPosition = "center",
}: DividerProps) {
  const { mode } = useTheme();
  const isDark = mode === "dark";

  // Thickness styles
  const thicknessStyles = {
    thin: "h-px",
    thick: "h-0.5",
  };

  const verticalThicknessStyles = {
    thin: "w-px",
    thick: "w-0.5",
  };

  // Color styles
  const colorStyles = isDark 
    ? "bg-[#49454F]" 
    : "bg-[#DADCE0]";

  // Type styles (for horizontal dividers)
  const typeStyles = {
    fullWidth: "w-full",
    inset: "ml-16 mr-0 w-[calc(100%-4rem)]",
    middle: "w-4/5 mx-auto",
  };

  // Vertical styles
  if (vertical) {
    return (
      <div
        className={`
          ${verticalThicknessStyles[thickness]}
          ${colorStyles}
          self-stretch
          ${className}
        `}
        role="separator"
        aria-orientation="vertical"
      />
    );
  }

  // Text divider variant
  if (text) {
    const textPositionStyles = {
      left: "",
      center: "justify-center",
      right: "justify-end",
    };

    return (
      <div 
        className={`
          flex items-center gap-4
          ${textPositionStyles[textPosition]}
          ${className}
        `}
        role="separator"
      >
        <div className={`flex-1 h-px ${colorStyles}`} />
        <span className={`
          text-xs font-medium uppercase tracking-wide shrink-0
          ${isDark ? "text-[#938F99]" : "text-[#5F6368]"}
        `}>
          {text}
        </span>
        {textPosition === "center" && <div className={`flex-1 h-px ${colorStyles}`} />}
      </div>
    );
  }

  // Standard horizontal divider
  return (
    <div
      className={`
        ${typeStyles[type]}
        ${thicknessStyles[thickness]}
        ${colorStyles}
        ${className}
      `}
      role="separator"
      aria-orientation="horizontal"
    />
  );
}

// List Divider - commonly used in list views
interface ListDividerProps {
  inset?: boolean;
  className?: string;
}

export function ListDivider({ inset = false, className = "" }: ListDividerProps) {
  return (
    <Divider 
      type={inset ? "inset" : "fullWidth"} 
      className={className} 
    />
  );
}

// Section Divider with optional title
interface SectionDividerProps {
  title?: string;
  className?: string;
}

export function SectionDivider({ title, className = "" }: SectionDividerProps) {
  const { mode } = useTheme();
  const isDark = mode === "dark";

  if (!title) {
    return <Divider type="fullWidth" thickness="thick" className={className} />;
  }

  return (
    <div className={`py-4 ${className}`}>
      <Divider text={title} textPosition="left" />
    </div>
  );
}

export default Divider;

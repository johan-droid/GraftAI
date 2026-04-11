import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center text-center py-16 px-6",
      "rounded-xl border border-dashed",
      className
    )}
    style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}
    >
      <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
        style={{ background: "var(--bg-hover)" }}>
        <Icon className="w-7 h-7" style={{ color: "var(--text-faint)" }} />
      </div>
      <h3 className="text-base font-semibold mb-1" style={{ color: "var(--text)" }}>{title}</h3>
      <p className="text-sm max-w-xs" style={{ color: "var(--text-muted)" }}>{description}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

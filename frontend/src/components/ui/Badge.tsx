import { cn, typeBadgeColor } from "@/lib/utils";

export function Badge({
  type,
  children,
  className,
}: {
  type?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-1.5 py-0.5 rounded text-xs font-mono border",
        type ? typeBadgeColor(type) : "bg-gray-800 text-gray-300 border-gray-700",
        className
      )}
    >
      {children}
    </span>
  );
}

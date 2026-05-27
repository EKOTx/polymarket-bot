import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={cn(
        "rounded border border-[#30363d] bg-[#1c2128] p-4",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h2 className="text-sm font-semibold text-[#e6edf3]">{title}</h2>
        {subtitle && (
          <p className="text-xs text-[#6e7681] mt-0.5">{subtitle}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

export function Stat({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string | number;
  sub?: string;
  color?: string;
}) {
  return (
    <div>
      <p className="text-xs text-[#6e7681] uppercase tracking-wider mb-1">
        {label}
      </p>
      <p className={cn("text-xl font-mono font-semibold", color ?? "text-[#e6edf3]")}>
        {value}
      </p>
      {sub && <p className="text-xs text-[#6e7681] mt-0.5">{sub}</p>}
    </div>
  );
}

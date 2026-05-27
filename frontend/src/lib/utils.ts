import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPct(value: number, decimals = 1): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(decimals)}%`;
}

export function formatUsd(value: number, decimals = 2): string {
  const abs = Math.abs(value).toFixed(decimals);
  return `${value < 0 ? "-" : ""}$${abs}`;
}

export function formatEdge(edge: number): string {
  return `${edge.toFixed(1)}%`;
}

export function formatConfidence(conf: number): string {
  return `${(conf * 100).toFixed(0)}%`;
}

export function formatTs(ts: string): string {
  return new Date(ts).toLocaleString();
}

export function typeColor(oppType: string): string {
  switch (oppType.toUpperCase()) {
    case "VALUE":
      return "text-emerald-400";
    case "SPREAD":
      return "text-blue-400";
    case "HIGH_VIG":
      return "text-amber-400";
    case "TOURNAMENT_ARB":
      return "text-purple-400";
    default:
      return "text-gray-400";
  }
}

export function typeBadgeColor(oppType: string): string {
  switch (oppType.toUpperCase()) {
    case "VALUE":
      return "bg-emerald-900/40 text-emerald-300 border-emerald-700";
    case "SPREAD":
      return "bg-blue-900/40 text-blue-300 border-blue-700";
    case "HIGH_VIG":
      return "bg-amber-900/40 text-amber-300 border-amber-700";
    case "TOURNAMENT_ARB":
      return "bg-purple-900/40 text-purple-300 border-purple-700";
    default:
      return "bg-gray-800 text-gray-300 border-gray-700";
  }
}

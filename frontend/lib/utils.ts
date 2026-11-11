import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility: merge Tailwind class names with conflict resolution.
 * Usage: cn("px-2 py-1", isActive && "bg-blue-500", className)
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format an identity account address for UI display.
 * Tech-Invisible: never expose raw "wallet address" terminology in UI.
 * @param account  Full 42-char hex address
 * @param chars    Chars to show each side (default 4)
 */
export function formatAccount(account: string, chars = 4): string {
  if (!account || account.length < chars * 2 + 2) return account;
  return `${account.slice(0, chars + 2)}…${account.slice(-chars)}`;
}

/**
 * Clamp a value between min and max (inclusive).
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Convert pixel coordinates to percentage-based bounding box
 * given the container dimensions.
 */
export function pixelToPercent(
  px: number,
  py: number,
  pw: number,
  ph: number,
  containerWidth: number,
  containerHeight: number
): { xPct: number; yPct: number; widthPct: number; heightPct: number } {
  return {
    xPct: clamp((px / containerWidth) * 100, 0, 100),
    yPct: clamp((py / containerHeight) * 100, 0, 100),
    widthPct: clamp((pw / containerWidth) * 100, 0, 100),
    heightPct: clamp((ph / containerHeight) * 100, 0, 100),
  };
}

/**
 * Convert percentage bounding box back to pixel coordinates.
 */
export function percentToPixel(
  xPct: number,
  yPct: number,
  widthPct: number,
  heightPct: number,
  containerWidth: number,
  containerHeight: number
): { x: number; y: number; width: number; height: number } {
  return {
    x: (xPct / 100) * containerWidth,
    y: (yPct / 100) * containerHeight,
    width: (widthPct / 100) * containerWidth,
    height: (heightPct / 100) * containerHeight,
  };
}

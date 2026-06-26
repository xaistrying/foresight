export function cssVar(name: string): string {
  if (typeof window === "undefined") return "";
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

/* ── Icon ─────────────────────────────────────────────────── */
export const iconColors = {
  default: "var(--color-icon-default)",
  active:  "var(--color-icon-active)",
  muted:   "var(--color-icon-muted)",
} as const;

/* ── Text ─────────────────────────────────────────────────── */
export const textColors = {
  primary:   "var(--color-text-primary)",
  secondary: "var(--color-text-secondary)",
  muted:     "var(--color-text-muted)",
} as const;

/* ── Background ───────────────────────────────────────────── */
export const bgColors = {
  base:     "var(--color-bg-base)",
  surface:  "var(--color-bg-surface)",
  elevated: "var(--color-bg-elevated)",
  hover:    "var(--color-bg-hover)",
  active:   "var(--color-bg-active)",
  selected: "var(--color-bg-selected)",
} as const;

/* ── Accent ───────────────────────────────────────────────── */
export const accentColors = {
  default: "var(--color-accent)",
  success: "var(--color-accent-success)",
  danger:  "var(--color-accent-danger)",
  warning: "var(--color-accent-warning)",
} as const;

/* ── Backward-compat (giữ lại để không break code cũ) ─────── */
/** @deprecated Dùng `iconColors.default` thay thế */
export const colors = {
  icon: {
    default: iconColors.default,
  },
} as const;

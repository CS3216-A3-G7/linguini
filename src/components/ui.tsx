import type { ButtonHTMLAttributes, ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeftIcon, HelpIcon } from "./icons";
import "./ui.css";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "quiet";
  block?: boolean;
};

export function Button({ variant = "primary", block, className = "", ...rest }: ButtonProps) {
  const classes = ["btn", `btn--${variant}`, block ? "btn--block" : "", className]
    .filter(Boolean)
    .join(" ");
  return <button type="button" className={classes} {...rest} />;
}

export function IconButton({
  label,
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; children: ReactNode }) {
  return (
    <button type="button" className="icon-btn" aria-label={label} {...rest}>
      {children}
    </button>
  );
}

export function Card({
  children,
  lifted,
  plain,
  className = "",
}: {
  children: ReactNode;
  lifted?: boolean;
  plain?: boolean;
  className?: string;
}) {
  const classes = ["card", lifted ? "card--lifted" : "", plain ? "card--plain" : "", className]
    .filter(Boolean)
    .join(" ");
  return <div className={classes}>{children}</div>;
}

export function TopBar({
  title,
  onBack,
  help,
  right,
}: {
  title: string;
  onBack?: () => void;
  help?: string;
  right?: ReactNode;
}) {
  const navigate = useNavigate();
  return (
    <div className="topbar">
      <IconButton label="Go back" onClick={onBack ?? (() => navigate(-1))}>
        <ArrowLeftIcon />
      </IconButton>
      <span className="topbar__title">{title}</span>
      {right}
      {help ? (
        <IconButton label="What happens here?" title={help} onClick={() => window.alert(help)}>
          <HelpIcon />
        </IconButton>
      ) : null}
    </div>
  );
}

export function Wordmark({ size = 26 }: { size?: number }) {
  return (
    <span className="wordmark" style={{ fontSize: size }}>
      Linguini
      <svg className="wordmark__noodle" viewBox="0 0 120 10" fill="none" role="presentation">
        <path
          d="M3 6c10-6 18 6 28 1s18-6 28 0 18 6 28 1 10-4 30-2"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}

/** Persistent yellow Linguini wordmark shown at the top of every screen. */
export function BrandBar() {
  return (
    <header className="brandbar" aria-label="Linguini">
      <img className="brandbar__wordmark" src="/linguini-wordmark.png" alt="Linguini" />
    </header>
  );
}

export function ProgressTrail({
  value,
  total,
  label,
}: {
  value: number;
  total: number;
  label?: string;
}) {
  const pct = total === 0 ? 0 : Math.min(100, Math.round((value / total) * 100));
  return (
    <div className="trail">
      <div className="trail__track">
        <div className="trail__fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="trail__label">{label ?? `${value} of ${total}`}</span>
    </div>
  );
}

export function StatusPill({ status }: { status: "new" | "learning" | "mastered" }) {
  const copy = { new: "New", learning: "Learning", mastered: "Mastered" }[status];
  return <span className={`pill pill--${status}`}>{copy}</span>;
}

export function XpPill({ xp }: { xp: number }) {
  return <span className="pill pill--xp">+{xp} XP</span>;
}

export function Tabs<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { id: T; label: string }[];
  value: T;
  onChange: (id: T) => void;
}) {
  return (
    <div className="tabs" role="tablist">
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          role="tab"
          className="tab"
          aria-selected={option.id === value}
          onClick={() => onChange(option.id)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function Noodle({ className = "noodle-divider" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 240 20" fill="none" role="presentation">
      <path
        d="M4 14c18-14 34 8 52 0s26-14 44-6 28 14 46 6 24-10 40-2"
        stroke="#E85D32"
        strokeWidth="6"
        strokeLinecap="round"
      />
      <path
        d="M4 14c18-14 34 8 52 0s26-14 44-6 28 14 46 6 24-10 40-2"
        stroke="#F9B233"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function Mascot({ size = 96 }: { size?: number }) {
  return (
    <img
      className="mascot"
      src="/linguini-logo.svg"
      width={size}
      height={size}
      alt="Linguini mascot"
    />
  );
}

export function Feedback({
  tone = "good",
  children,
}: {
  tone?: "good" | "warn";
  children: ReactNode;
}) {
  return <div className={`feedback${tone === "warn" ? " feedback--warn" : ""}`}>{children}</div>;
}

export function Sheet({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="sheet-backdrop" role="dialog" aria-modal="true" aria-label={title}>
      <div className="sheet">
        <div className="spread" style={{ marginBottom: "var(--space-4)" }}>
          <h2>{title}</h2>
          <Button variant="quiet" onClick={onClose}>
            Close
          </Button>
        </div>
        {children}
      </div>
    </div>
  );
}

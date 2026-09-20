import { useEffect, useId, useRef, useState, type ButtonHTMLAttributes, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeftIcon, CloseIcon, HelpIcon } from "./icons";
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
  className = "",
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; children: ReactNode }) {
  return (
    <button type="button" className={["icon-btn", className].filter(Boolean).join(" ")} aria-label={label} {...rest}>
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
  help,
  right,
}: {
  title: string;
  help?: string;
  right?: ReactNode;
}) {
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const titleId = useId();
  const modalRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!isHelpOpen) return;

    modalRef.current?.querySelector<HTMLButtonElement>("button")?.focus();
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsHelpOpen(false);
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [isHelpOpen]);

  return (
    <>
      <div className="topbar">
        <span className="topbar__title">{title}</span>
        {right}
        {help ? (
          <IconButton
            label="What happens here?"
            aria-haspopup="dialog"
            aria-expanded={isHelpOpen}
            onClick={() => setIsHelpOpen(true)}
          >
            <HelpIcon />
          </IconButton>
        ) : null}
      </div>

      {help && isHelpOpen ? (
        <div className="help-modal__backdrop" onMouseDown={() => setIsHelpOpen(false)}>
          <section
            ref={modalRef}
            className="help-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="help-modal__header">
              <h2 id={titleId}>About this step</h2>
              <IconButton
                label="Close information"
                onClick={() => setIsHelpOpen(false)}
              >
                <CloseIcon />
              </IconButton>
            </div>
            <p>{help}</p>
            <Button block onClick={() => setIsHelpOpen(false)}>
              Got it
            </Button>
          </section>
        </div>
      ) : null}
    </>
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

/** Centered Linguini wordmark in the shared brand strip at the top of every screen. */
export function BrandBar({ back = false, onBack, backLabel }: { back?: boolean; onBack?: () => void; backLabel?: string }) {
  const navigate = useNavigate();
  return (
    <header className="brandbar" aria-label="Linguini">
      {back ? (
        <IconButton className="brandbar__back" label={backLabel ?? "Go back"} onClick={onBack ?? (() => navigate(-1))}>
          <ChevronLeftIcon />
        </IconButton>
      ) : null}
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

export function StatusPill({ status }: { status: "new" | "learning" | "familiar" | "mastered" }) {
  const copy = { new: "New", learning: "Learning", familiar: "Familiar", mastered: "Mastered" }[status];
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
    <svg className={className} viewBox="-25 0 240 20" fill="none" role="presentation">
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

export function Mascot({ size = 96, expression = "happy" }: { size?: number; expression?: "happy" | "sad" }) {
  const isSad = expression === "sad";

  return (
    <img
      className="mascot"
      src={isSad ? "/linguini-logo-sad.svg" : "/linguini-logo.svg"}
      width={size}
      height={size}
      alt={`Linguini mascot, ${expression}`}
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
  return <div className={`feedback feedback--${tone}`}>{children}</div>;
}

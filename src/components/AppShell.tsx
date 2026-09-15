import { NavLink, Outlet } from "react-router-dom";
import { BookIcon, CameraIcon, HomeIcon, PersonIcon, TrendIcon } from "./icons";

const items = [
  { to: "/home", label: "Home", Icon: HomeIcon },
  { to: "/practice", label: "Practice", Icon: CameraIcon },
  { to: "/journal", label: "Journal", Icon: BookIcon },
  { to: "/progress", label: "Progress", Icon: TrendIcon },
  { to: "/profile", label: "Profile", Icon: PersonIcon },
];

export function AppShell() {
  return (
    <div className="shell">
      <main className="shell__content">
        <Outlet />
      </main>
      <nav className="bottom-nav" aria-label="Main">
        {items.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `bottom-nav__item${isActive ? " is-active" : ""}`}
          >
            <Icon />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

/** Full-bleed shell for focused flows (onboarding, practice steps, I-Spy). */
export function FocusShell() {
  return (
    <div className="shell">
      <main className="shell__content" style={{ paddingBottom: "var(--space-8)" }}>
        <Outlet />
      </main>
    </div>
  );
}

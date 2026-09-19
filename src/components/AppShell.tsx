import { NavLink, Outlet, useLocation } from "react-router-dom";
import { BookIcon, CameraIcon, HomeIcon, JournalIcon, PersonIcon } from "./icons";
import { BrandBar } from "./ui";

const items = [
  { to: "/home", label: "Home", Icon: HomeIcon },
  { to: "/practice", label: "Practice", Icon: CameraIcon },
  { to: "/vocabulary", label: "Vocabulary", Icon: BookIcon },
  { to: "/journal", label: "Journal", Icon: JournalIcon },
  { to: "/profile", label: "Profile", Icon: PersonIcon },
];

export function AppShell() {
  const { pathname } = useLocation();
  const isDetailPage =
    pathname === "/journal/new" ||
    /^\/journal\/[^/]+$/.test(pathname) ||
    pathname === "/profile/edit";

  return (
    <div className="shell">
      <BrandBar back={isDetailPage} />
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
  const { pathname } = useLocation();

  return (
    <div className="shell">
      <BrandBar back={pathname !== "/"} />
      <main className="shell__content" style={{ paddingBottom: "var(--space-8)" }}>
        <Outlet />
      </main>
    </div>
  );
}

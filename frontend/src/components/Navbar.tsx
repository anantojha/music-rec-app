import { NavLink } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import "@/components/Navbar.css";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Deck", glyph: "01" },
  { to: "/history", label: "Log", glyph: "02" },
];

export function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="rail" aria-label="Primary">
      <div className="rail-mark eyebrow">AMR</div>

      <div className="rail-links">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `rail-link${isActive ? " rail-link-active" : ""}`}
          >
            <span className="rail-glyph mono">{item.glyph}</span>
            <span className="rail-label">{item.label}</span>
          </NavLink>
        ))}
      </div>

      <div className="rail-footer">
        {user && (
          <button className="rail-avatar" onClick={logout} title={`Sign out of ${user.display_name}`}>
            {user.display_name.charAt(0).toUpperCase()}
          </button>
        )}
      </div>
    </nav>
  );
}

import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Navbar() {
  const { isAuthenticated, signOut } = useAuth();
  const navigate = useNavigate();

  function handleSignOut() {
    signOut();
    navigate("/login");
  }

  return (
    <header className="navbar">
      <div className="navbar__inner">
        <NavLink to="/" className="navbar__brand">
          <span className="navbar__mark" aria-hidden="true" />
          TokenWise
        </NavLink>

        {isAuthenticated && (
          <nav className="navbar__links">
            <NavLink
              to="/chat"
              className={({ isActive }) => "navbar__link" + (isActive ? " navbar__link--active" : "")}
            >
              Chat
            </NavLink>
            <NavLink
              to="/stats"
              className={({ isActive }) => "navbar__link" + (isActive ? " navbar__link--active" : "")}
            >
              Stats
            </NavLink>
            <button className="navbar__signout" onClick={handleSignOut}>
              Sign out
            </button>
          </nav>
        )}
      </div>
    </header>
  );
}

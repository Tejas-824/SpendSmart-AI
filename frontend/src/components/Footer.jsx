import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer__inner">
        <span className="footer__text">
  SpendSmart AI - Smarter AI routing, lower costs, better answers.
</span>
        <nav className="footer__links">
          <Link to="/chat">Chat</Link>
          <Link to="/stats">Stats</Link>
          <a href="https://github.com" target="_blank" rel="noreferrer">
            GitHub
          </a>
        </nav>
      </div>
    </footer>
  );
}

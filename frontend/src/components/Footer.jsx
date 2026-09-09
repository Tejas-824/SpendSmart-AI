import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer__inner">
        <span className="footer__text">TokenWise - a cost-aware LLM router, built as a learning project.</span>
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

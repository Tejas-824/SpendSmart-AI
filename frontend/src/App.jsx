import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import ScrollToTop from "./components/ScrollToTop";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Chat from "./pages/Chat";
import Stats from "./pages/Stats";
import { useAuth } from "./AuthContext";

export default function App() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="app-shell">
      <ScrollToTop />
      <Navbar />

      <main className="app-content">
        <Routes>
          <Route path="/" element={<Navigate to={isAuthenticated ? "/chat" : "/login"} replace />} />
          <Route path="/login" element={isAuthenticated ? <Navigate to="/chat" replace /> : <Login />} />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <Chat />
              </ProtectedRoute>
            }
          />
          <Route
            path="/stats"
            element={
              <ProtectedRoute>
                <Stats />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <Footer />
    </div>
  );
}

import React, { useState, useEffect, useCallback } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Particles from "react-particles";
import { loadSlim } from "tsparticles-slim";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Dashboard from "./components/Dashboard";
import Login from "./pages/Login"; // Assuming Login.jsx is in pages/
import Register from "./pages/Register";
import Alerts from "./pages/Alerts";
import PoliciesGenerator from "./pages/PoliciesGenerator";
import VulnerabilityScanner from "./pages/VulnerabilityScanner";
import ComplianceChecker from "./pages/ComplianceChecker";
import RiskDashboard from "./pages/RiskDashboard";
import Pricing from "./pages/Pricing";
import Configs from "./pages/Configs";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loadingAuth, setLoadingAuth] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem("token");
      const tokenExpiration = localStorage.getItem("token_expiration");
      const storedUser = localStorage.getItem("user");

      if (token && tokenExpiration && Date.now() < parseInt(tokenExpiration)) {
        setIsAuthenticated(true);
        if (storedUser) {
          setUser(JSON.parse(storedUser));
        }
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
      setLoadingAuth(false);
    };

    setTimeout(checkAuth, 500);

    window.addEventListener("storage", checkAuth);
    return () => window.removeEventListener("storage", checkAuth);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("token_expiration");
    localStorage.removeItem("user");
    setIsAuthenticated(false);
    setUser(null);
    toast.success("Deconneted", { position: "top-right", autoClose: 3000 });
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed((prev) => !prev);
  };

  const particlesInit = useCallback(async (engine) => {
    await loadSlim(engine);
  }, []);

  const particlesOptions = {
    background: {
      color: { value: "#b6c5ec" },
    },
    fpsLimit: 120,
    interactivity: {
      events: {
        onClick: { enable: true, mode: "push" },
        onHover: { enable: true, mode: "repulse" },
        resize: true,
      },
      modes: {
        push: { quantity: 4 },
        repulse: { distance: 150, duration: 0.4 },
      },
    },
    particles: {
      color: { value: "#1c75df" },
      links: { color: "#5497e6", distance: 150, enable: true, opacity: 0.5, width: 1 },
      move: {
        direction: "none",
        enable: true,
        outModes: { default: "bounce" },
        random: true,
        speed: 2,
        straight: false,
      },
      number: { density: { enable: true, area: 800 }, value: 100 },
      opacity: { value: 0.6, random: true },
      shape: { type: "circle" },
      size: { value: { min: 1, max: 5 }, random: true },
    },
    detectRetina: true,
  };

  if (loadingAuth) {
    return (
      <div className="relative flex h-screen items-center justify-center text-slate-700 text-xl">
        <Particles id="tsparticles-loading" init={particlesInit} options={particlesOptions} className="absolute inset-0 z-0" />
        <div className="relative z-10">Loading...</div>
      </div>
    );
  }

  return (
    <Router>
      <ToastContainer autoClose={3000} />
      <div className="relative flex h-screen overflow-hidden">
        <Particles id="tsparticles" init={particlesInit} options={particlesOptions} className="absolute inset-0 z-0" />
        <div className="flex flex-1 h-full z-10">
          {isAuthenticated && (
            <Sidebar
              isAuthenticated={isAuthenticated}
              handleLogout={handleLogout}
              isCollapsed={isSidebarCollapsed}
              toggleSidebar={toggleSidebar}
            />
          )}
          <div className="flex flex-col flex-1">
            {isAuthenticated && (
              <Header
                isAuthenticated={isAuthenticated}
                user={user}
                handleLogout={handleLogout}
              />
            )}
            <main className="flex-1 overflow-y-auto p-6">
              <Routes>
                <Route path="/" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
                <Route path="/dashboard" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
                <Route path="/alerts" element={isAuthenticated ? <Alerts /> : <Navigate to="/login" />} />
                <Route path="/generate-policy" element={isAuthenticated ? <PoliciesGenerator /> : <Navigate to="/login" />} />
                <Route path="/scan" element={isAuthenticated ? <VulnerabilityScanner /> : <Navigate to="/login" />} />
                <Route path="/compliance" element={isAuthenticated ? <ComplianceChecker /> : <Navigate to="/login" />} />
                <Route path="/configs" element={isAuthenticated ? <Configs /> : <Navigate to="/login" />} />
                <Route path="/risks" element={isAuthenticated ? <RiskDashboard /> : <Navigate to="/login" />} />
                <Route
                  path="/login"
                  element={!isAuthenticated ? <Login setIsAuthenticated={setIsAuthenticated} setUser={setUser} /> : <Navigate to="/dashboard" />}
                />
                <Route
                  path="/auth/google/callback"
                  element={<Login setIsAuthenticated={setIsAuthenticated} setUser={setUser} />}
                />
                <Route
                  path="/auth/github/callback"
                  element={<Login setIsAuthenticated={setIsAuthenticated} setUser={setUser} />}
                />
                <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/dashboard" />} />
                <Route path="/pricing" element={<Pricing />} />
              </Routes>
            </main>
          </div>
        </div>
      </div>
    </Router>
  );
}

export default App;
import React, { useState, useEffect, useCallback } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Particles from "react-particles";
import { loadSlim } from "tsparticles-slim";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Dashboard from "./components/Dashboard";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Alerts from "./pages/Alerts";
import PoliciesGenerator from "./pages/PoliciesGenerator";
import VulnerabilityScanner from "./pages/VulnerabilityScanner/VulnerabilityScanner";
import ComplianceChecker from "./pages/ComplianceChecker/ComplianceChecker";
import RiskDashboard from "./pages/RiskDashboard/RiskDashboard";
import Pricing from "./pages/Pricing";
import Configs from "./pages/Configs";
import AllInOne from "./pages/AllInOne";
import AdminDashboard from "./pages/AdminDashboard";

// Protected route component for admin-only access
const ProtectedAdminRoute = ({ isAuthenticated, user, children }) => {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (!user || user.role !== "admin") {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

// Protected route component for user-only access
const ProtectedUserRoute = ({ isAuthenticated, user, children }) => {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (user?.role === "admin") {
    return <Navigate to="/admin-dashboard" replace />;
  }
  return children;
};

// Child component to handle routing and useLocation
const AppContent = ({ isAuthenticated, user, handleLogout, isSidebarCollapsed, toggleSidebar, setIsAuthenticated, setUser }) => {
  const location = useLocation();
  const showSidebar = isAuthenticated && location.pathname !== "/admin-dashboard";

  return (
    <div className="relative flex h-screen overflow-hidden bg-white">
      
      <div className="flex flex-1 h-full z-10">
        {showSidebar && (
          <Sidebar
            isAuthenticated={isAuthenticated}
            handleLogout={handleLogout}
            isCollapsed={isSidebarCollapsed}
            toggleSidebar={toggleSidebar}
            user={user}
          />
        )}
        <div className="flex flex-col flex-1">
          {isAuthenticated && (
            <Header
              isAuthenticated={isAuthenticated}
              user={user}
              handleLogout={handleLogout}
              isAdmin={location.pathname === "/admin-dashboard"}
              isCollapsed={isSidebarCollapsed}
            />
          )}
          <main className={`flex-1 overflow-y-auto p-6 transition-all duration-300 ${
            isAuthenticated && showSidebar 
              ? (isSidebarCollapsed ? 'ml-16 mt-16' : 'ml-64 mt-16') 
              : ''
          }`}>
            <Routes>
              <Route
                path="/"
                element={
                  <ProtectedUserRoute isAuthenticated={isAuthenticated} user={user}>
                    <Dashboard />
                  </ProtectedUserRoute>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <ProtectedUserRoute isAuthenticated={isAuthenticated} user={user}>
                    <Dashboard />
                  </ProtectedUserRoute>
                }
              />
              <Route
                path="/alerts"
                element={
                  <ProtectedUserRoute isAuthenticated={isAuthenticated} user={user}>
                    <Alerts />
                  </ProtectedUserRoute>
                }
              />
              <Route
                path="/generate-policy"
                element={
                  <ProtectedUserRoute isAuthenticated={isAuthenticated} user={user}>
                    <PoliciesGenerator />
                  </ProtectedUserRoute>
                }
              />
              <Route
                path="/scan"
                element={
                  <ProtectedUserRoute isAuthenticated={isAuthenticated} user={user}>
                    <VulnerabilityScanner />
                  </ProtectedUserRoute>
                }
              />
              <Route
                path="/compliance"
                element={
                  <ProtectedUserRoute isAuthenticated={isAuthenticated} user={user}>
                    <ComplianceChecker />
                  </ProtectedUserRoute>
                }
              />
              <Route
                path="/configs"
                element={
                  <ProtectedUserRoute isAuthenticated={isAuthenticated} user={user}>
                    <Configs />
                  </ProtectedUserRoute>
                }
              />
              <Route
                path="/risks"
                element={
                  <ProtectedUserRoute isAuthenticated={isAuthenticated} user={user}>
                    <RiskDashboard />
                  </ProtectedUserRoute>
                }
              />
              <Route path="/all-in-one" element={<AllInOne />} />
              <Route
                path="/admin-dashboard"
                element={
                  <ProtectedAdminRoute isAuthenticated={isAuthenticated} user={user}>
                    <AdminDashboard />
                  </ProtectedAdminRoute>
                }
              />
              <Route
                path="/login"
                element={
                  !isAuthenticated ? (
                    <Login setIsAuthenticated={setIsAuthenticated} setUser={setUser} />
                  ) : (
                    <Navigate to={user?.role === "admin" ? "/admin-dashboard" : "/dashboard"} />
                  )
                }
              />
              <Route
                path="/auth/google/callback"
                element={<Login setIsAuthenticated={setIsAuthenticated} setUser={setUser} />}
              />
              <Route
                path="/auth/github/callback"
                element={<Login setIsAuthenticated={setIsAuthenticated} setUser={setUser} />}
              />
              <Route
                path="/register"
                element={
                  !isAuthenticated ? (
                    <Register />
                  ) : (
                    <Navigate to={user?.role === "admin" ? "/admin-dashboard" : "/dashboard"} />
                  )
                }
              />
              <Route path="/pricing" element={<Pricing />} />
            </Routes>
          </main>
        </div>
      </div>
    </div>
  );
};

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
    toast.success("Logged out", { position: "top-right", autoClose: 3000 });
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed((prev) => !prev);
  };

  if (loadingAuth) {
    return (
      <div className="relative flex h-screen items-center justify-center text-slate-700 text-xl">
        <Particles
          id="tsparticles-loading"
          init={async (engine) => await loadSlim(engine)}
          options={{
            background: { color: { value: "#b6c5ec" } },
            fpsLimit: 120,
            interactivity: {
              events: { onClick: { enable: true, mode: "push" }, onHover: { enable: true, mode: "repulse" }, resize: true },
              modes: { push: { quantity: 4 }, repulse: { distance: 150, duration: 0.4 } },
            },
            particles: {
              color: { value: "#1c75df" },
              links: { color: "#5497e6", distance: 150, enable: true, opacity: 0.5, width: 1 },
              move: { direction: "none", enable: true, outModes: { default: "bounce" }, random: true, speed: 2, straight: false },
              number: { density: { enable: true, area: 800 }, value: 100 },
              opacity: { value: 0.6, random: true },
              shape: { type: "circle" },
              size: { value: { min: 1, max: 5 }, random: true },
            },
            detectRetina: true,
          }}
          className="absolute inset-0 z-0"
        />
        <div className="relative z-10">Loading...</div>
      </div>
    );
  }

  return (
    <Router>
      <ToastContainer autoClose={3000} />
      <AppContent
        isAuthenticated={isAuthenticated}
        user={user}
        handleLogout={handleLogout}
        isSidebarCollapsed={isSidebarCollapsed}
        toggleSidebar={toggleSidebar}
        setIsAuthenticated={setIsAuthenticated}
        setUser={setUser}
      />
    </Router>
  );
}

export default App;
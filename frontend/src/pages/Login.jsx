import React, { useState, useEffect } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { toast } from "react-toastify";
import { Eye, EyeOff } from "lucide-react";
import SetPassword from "./SetPassword"; // Adjust path

const Login = ({ setIsAuthenticated, setUser }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [needsPassword, setNeedsPassword] = useState(false);
  const [authUser, setAuthUser] = useState(null);

  // Handle OAuth callbacks (Google and GitHub)
  useEffect(() => {
    const handleOAuthCallback = () => {
      const params = new URLSearchParams(location.search);
      const accessToken = params.get("access_token");
      const refreshToken = params.get("refresh_token");
      const userId = params.get("user_id");
      const name = params.get("name");
      const email = params.get("email");
      const role = params.get("role") || "user"; // Include role from OAuth callback
      const needsPassword = params.get("needs_password") === "true";

      if (accessToken && refreshToken && userId && email) {
        localStorage.setItem("token", accessToken);
        localStorage.setItem("refresh_token", refreshToken);
        localStorage.setItem("token_expiration", Date.now() + 3600000);
        const user = { id: userId, name, email, role }; // Include role
        localStorage.setItem("user", JSON.stringify(user));

        if (!needsPassword) {
          setIsAuthenticated(true);
          setUser(user);
          toast.success("Connexion réussie !", {
            position: "top-right",
            autoClose: 3000,
            theme: "light",
          });
          // Navigate based on role
          navigate(role === "admin" ? "/admin-dashboard" : "/dashboard", { replace: true });
        } else {
          setAuthUser(user);
          setNeedsPassword(true);
        }
      } else {
        toast.error("Erreur lors de l'authentification", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
        navigate("/login", { replace: true });
      }
    };

    if (["/auth/google/callback", "/auth/github/callback"].includes(location.pathname)) {
      handleOAuthCallback();
    }
  }, [location, navigate, setIsAuthenticated, setUser]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:5000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();
      setLoading(false);

      if (response.ok) {
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        localStorage.setItem("token_expiration", Date.now() + 3600000);
        localStorage.setItem("user", JSON.stringify(data.user));

        setIsAuthenticated(true);
        setUser(data.user);

        toast.success("Connexion réussie !", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });

        // Navigate based on role
        navigate(data.user.role === "admin" ? "/admin-dashboard" : "/dashboard");
      } else {
        toast.error(data.error || "Échec de la connexion", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      }
    } catch (error) {
      toast.error("Erreur de connexion au serveur", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/auth/google");
      const data = await response.json();
      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      } else {
        toast.error("Erreur Google OAuth", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      }
    } catch (error) {
      toast.error("Erreur de connexion au serveur", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    }
  };

  const handleGitHubLogin = async () => {
    try {
      window.location.href = "http://127.0.0.1:5000/auth/github";
    } catch (error) {
      toast.error("Erreur GitHub OAuth", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    }
  };

  if (needsPassword && authUser) {
    return (
      <SetPassword
        user={authUser}
        setIsAuthenticated={setIsAuthenticated}
        setUser={setUser}
      />
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="bg-sky-100 p-6 rounded-lg shadow-lg w-full max-w-md z-10">
        <h2 className="text-2xl font-bold text-center text-gray-800 mb-6">Connexion</h2>
        <form onSubmit={handleLogin}>
          <div className="mb-4">
            <label htmlFor="email" className="block text-gray-800 mb-1">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-2 bg-sky-100 text-gray-800 border border-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 placeholder-gray-400"
              placeholder="Entrez votre email"
              required
            />
          </div>

          <div className="mb-6 relative">
            <label htmlFor="password" className="block text-gray-800 mb-1">
              Mot de passe
            </label>
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 pr-10 bg-sky-100 text-gray-800 border border-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 placeholder-gray-400"
              placeholder="Entrez votre mot de passe"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-2 top-9 text-gray-400 hover:text-gray-700"
              tabIndex={-1}
            >
              {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full bg-blue-600 text-white p-2 rounded-lg font-semibold transition-colors duration-200 ${
              loading ? "opacity-50 cursor-not-allowed" : "hover:bg-blue-700"
            }`}
          >
            {loading ? "Connexion..." : "Se connecter"}
          </button>
        </form>

        <div className="mt-4">
          <button
            onClick={handleGoogleLogin}
            className="w-full bg-white text-gray-800 p-2 rounded-lg font-semibold flex items-center justify-center hover:bg-gray-200 transition-colors duration-200 mb-2"
          >
            <img
              src="https://www.google.com/favicon.ico"
              alt="Google"
              className="w-5 h-5 mr-2"
            />
            Connect via Google
          </button>
          <button
            onClick={handleGitHubLogin}
            className="w-full bg-gray-900 text-white p-2 rounded-lg font-semibold flex items-center justify-center hover:bg-gray-700 transition-colors duration-200"
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.12-1.47-1.12-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.29 1.08 2.85.82.09-.64.35-1.08.63-1.33-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02A9.56 9.56 0 0 1 12 6.8c.85 0 1.71.11 2.52.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.94.36.31.66.94.66 1.9v2.81c0 .27.16.59.66.5A10 10 0 0 0 22 12 10 10 0 0 0 12 2z" />
            </svg>
            Connect with GitHub
          </button>
        </div>

        <p className="text-center text-gray-500 mt-4">
          Pas encore de compte ?{" "}
          <Link to="/register" className="text-blue-400 hover:underline">
            S'inscrire
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

const BASE_URL = (import.meta.env?.VITE_SIP || "http://localhost").replace(/\/+$/, "");
const API = `${BASE_URL}`;

const SetPassword = ({ user, setIsAuthenticated, setUser }) => {
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    if (password !== confirmPassword) {
      toast.error("The passwords are not similar !", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API}:5000/set-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ password }),
      });

      const data = await response.json();
      setLoading(false);

      if (response.ok) {
        toast.success("Password Saved successfully!", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
        setIsAuthenticated(true);
        setUser(user);
        navigate("/dashboard", { replace: true });
      } else {
        toast.error(data.error || "Failed to save the password", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      }
    } catch (error) {
      toast.error("Server Connexion Error ", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md z-10">
        <h2 className="text-2xl font-bold text-center text-gray-700 mb-6">
          Set a password for your account
        </h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="password" className="block text-gray-500 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 bg-gray-200 text-gray-700 border border-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 placeholder-gray-400"
              placeholder="Enter your password"
              required
            />
          </div>
          <div className="mb-6">
            <label htmlFor="confirm-password" className="block text-gray-500 mb-1">
              Confirm the password
            </label>
            <input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full p-2 bg-gray-200 text-gray-700 border border-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 placeholder-gray-400"
              placeholder="Repeat your password"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className={`w-full bg-blue-600 text-white p-2 rounded-lg font-semibold transition-colors duration-200 ${
              loading ? "opacity-50 cursor-not-allowed" : "hover:bg-blue-700"
            }`}
          >
            {loading ? "Saving..." : "Save the password"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default SetPassword; 
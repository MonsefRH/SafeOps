import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "react-toastify";

const BASE_URL = (process.env.REACT_APP_SIP || "http://localhost").replace(/\/+$/, "");
const API = `${BASE_URL}`;

const Register = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1: Register form, 2: Verify code
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}:5000/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await response.json();
      if (response.ok) {
        toast.success("Verification code sent to your email!", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
        setStep(2); 
      } else {
        toast.error(data.error || "Registration failed!", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      }
    } catch (error) {
      toast.error("Server connection error!", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    }
  };

  const handleVerifyCode = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}:5000/verify-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code }),
      });

      const data = await response.json();
      if (response.ok) {
        toast.success("Registration successful!", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
        navigate("/dashboard");
      } else {
        toast.error(data.error || "Invalid verification code!", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      }
    } catch (error) {
      toast.error("Server connection error!", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="bg-white p-6 rounded-lg shadow-lg w-full max-w-md z-10">
        {step === 1 ? (
          <>
            <h2 className="text-2xl font-bold text-center text-gray-700 mb-6">Register</h2>
            <form onSubmit={handleRegister}>
              <div className="mb-4">
                <label htmlFor="name" className="block text-gray-700 mb-1">
                  Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full p-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 placeholder-gray-500"
                  placeholder="Enter your name"
                  required
                />
              </div>
              <div className="mb-4">
                <label htmlFor="email" className="block text-gray-700 mb-1">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full p-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 placeholder-gray-500"
                  placeholder="Enter your email"
                  required
                />
              </div>
              <div className="mb-6">
                <label htmlFor="password" className="block text-gray-700 mb-1">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full p-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 placeholder-gray-500"
                  placeholder="Enter your password"
                  required
                />
              </div>
              <button
                type="submit"
                className="w-full bg-blue-600 text-white p-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors duration-200"
              >
                Send Verification Code
              </button>
            </form>
            <p className="text-center text-gray-500 mt-4">
              Already have an account?{" "}
              <Link to="/login" className="text-blue-400 hover:underline">
                Login
              </Link>
            </p>
          </>
        ) : (
          <>
            <h2 className="text-2xl font-bold text-center text-gray-700 mb-6">Verify Code</h2>
            <form onSubmit={handleVerifyCode}>
              <div className="mb-4">
                <label htmlFor="code" className="block text-gray-700 mb-1">
                  Verification Code
                </label>
                <input
                  id="code"
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="w-full p-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 placeholder-gray-500"
                  placeholder="Enter the code sent to your email"
                  required
                />
              </div>
              <button
                type="submit"
                className="w-full bg-blue-600 text-white p-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors duration-200"
              >
                Verify Code
              </button>
            </form>
            <p className="text-center text-gray-500 mt-4">
              Back to{" "}
              <button
                onClick={() => setStep(1)}
                className="text-blue-400 hover:underline"
              >
                Register
              </button>
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default Register;
import React, { useState } from "react";
import { toast } from "react-toastify";
import { CheckCircleIcon, ArrowPathIcon } from "@heroicons/react/24/outline";

const GitHubComplianceChecker = ({ setResult, isLoading, setIsLoading, userId }) => {
  const [url, setUrl] = useState("");

  const checkCompliance = async () => {
    if (!url || !url.includes("github.com")) {
      toast.warn("Veuillez entrer une URL de dépôt GitHub valide (ex. https://github.com/user/repo) !", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:5000/checkov", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "X-User-ID": userId, // Add user_id
        },
        body: JSON.stringify({ repo_url: url, input_type: "repo" }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Error while verification ");
      }

      const data = await response.json();
      setResult(data); // Pass raw response
      toast.success("Verification finished successfully", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    } catch (error) {
      toast.error(error.message || "Error while verification", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-2xl">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <CheckCircleIcon className="h-7 w-7 text-green-400" />
        Validation &  Conformity - GitHub (NIST, ISO 27001, GDPR, HIPAA)
      </h2>
      <div className="relative mb-6">
        <label htmlFor="github-url" className="text-gray-500 text-sm mb-2 block">
          GitHub Repos URL:
        </label>
        <input
          id="github-url"
          type="text"
          placeholder="GitHub URL (ex. https://github.com/user/repo)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full pl-10 pr-4 py-3 bg-gray-700 text-gray-100 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition duration-200 placeholder-gray-400"
        />
        <span className="absolute left-3 top-12 transform -translate-y-1/2 text-gray-400">
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.333-1.756-1.333-1.756-1.09-.745.083-.73.083-.73 1.205.135 1.838 1.24 1.838 1.24 1.065 1.885 2.876 1.34 3.578 1.025.112-.795.434-1.34.792-1.645-2.776-.315-5.686-1.385-5.686-6.165 0-1.365.487-2.48 1.287-3.355-.13-.315-.558-1.585.123-3.305 0 0 1.05-.335 3.44 1.285A12.01 12.01 0 0112 4.8c1.065.005 2.135.145 3.14.43 2.39-1.62 3.435-1.285 3.435-1.285.685 1.72.255 2.99.125 3.305.805.875 1.285 1.99 1.285 3.355 0 4.795-2.915 5.845-5.695 6.155.445.385.84 1.145.84 2.31 0 1.665-.015 3.015-.015 3.42 0 .32.215.695.825.575C20.565 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z" />
          </svg>
        </span>
      </div>
      <button
        onClick={checkCompliance}
        disabled={isLoading || !url}
        className={`w-full sm:w-auto bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors duration-200 flex items-center justify-center gap-2 ${
          isLoading || !url ? "opacity-50 cursor-not-allowed" : ""
        }`}
      >
        {isLoading ? (
          <>
            <ArrowPathIcon className="h-5 w-5 animate-spin" />
            Verification...
          </>
        ) : (
          <>
            <CheckCircleIcon className="h-5 w-5" />
            Verify
          </>
        )}
      </button>
    </div>
  );
};

export default GitHubComplianceChecker;
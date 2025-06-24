import React, { useState } from "react";
import { toast } from "react-toastify";
import {
  ArrowPathIcon,
  BugAntIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon
} from "@heroicons/react/24/outline";

const AllInOne = ({ userId }) => {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleScan = async () => {
    if (!url || !url.includes("github.com")) {
      toast.warn("Entrez une URL GitHub valide (ex: https://github.com/user/repo)", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      toast.error("Token JWT manquant. Veuillez vous reconnecter.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("http://127.0.0.1:5000/full-scan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "X-User-ID": userId
        },
        body: JSON.stringify({
          repo_url: url,
          repo_name: url.split("/").slice(-1)[0] || "unknown"
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Échec du scan");
      }

      const data = await response.json();
      setResult(data);
      toast.success("Scan terminé avec succès !", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    } catch (error) {
      toast.error(error.message || "Erreur pendant le scan");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 bg-white rounded shadow-md w-full max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <BugAntIcon className="h-6 w-6 text-red-500" />
        All-In-One Scanner
      </h1>

      <div className="mb-4">
        <label htmlFor="repo-url" className="block text-gray-600 text-sm font-semibold mb-2">
          GitHub Repo URL:
        </label>
        <input
          id="repo-url"
          type="text"
          className="w-full border border-gray-300 rounded px-4 py-2"
          placeholder="https://github.com/username/repo"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
      </div>

      <button
        onClick={handleScan}
        disabled={loading}
        className={`bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded ${
          loading ? "opacity-50 cursor-not-allowed" : ""
        }`}
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <ArrowPathIcon className="h-5 w-5 animate-spin" />
            Scanning...
          </span>
        ) : (
          "Scan All"
        )}
      </button>

      {result && (
        <div className="mt-8 text-sm text-gray-800 space-y-8">
          <h2 className="text-lg font-bold mb-2 flex items-center gap-2 text-blue-600">
            <DocumentTextIcon className="h-5 w-5" />
            Corrected files
          </h2>
          {Object.entries(result.t5 || {}).map(([filename, data]) => (
            <div key={filename} className="mb-6">
              <h3 className="font-semibold text-md text-gray-700">{filename}</h3>
              {data.corrected && data.content ? (
                <pre className="bg-gray-100 border p-4 rounded overflow-auto max-h-96 whitespace-pre-wrap">
                  {data.content}
                </pre>
              ) : (
                <p className="text-red-500">Erreur : {data.error || "correction impossible"}</p>
              )}
            </div>
          ))}

          <div>
            <h2 className="text-lg font-bold mb-2 flex items-center gap-2 text-green-700">
              <CheckCircleIcon className="h-5 w-5" />
              Validation & Conformity
            </h2>
            <pre className="bg-green-50 border p-4 rounded max-h-[400px] overflow-auto">
              {JSON.stringify(result.checkov_corrected || {}, null, 2)}
            </pre>
          </div>

          <div>
            <h2 className="text-lg font-bold mb-2 flex items-center gap-2 text-red-700">
              <ExclamationTriangleIcon className="h-5 w-5" />
              Vulnerability Analyser
            </h2>
            <pre className="bg-red-50 border p-4 rounded max-h-[400px] overflow-auto">
              {JSON.stringify(result.semgrep || {}, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default AllInOne;

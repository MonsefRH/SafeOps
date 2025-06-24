import React, { useState } from "react";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import {
  ArrowPathIcon,
  BugAntIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  DocumentDuplicateIcon,
} from "@heroicons/react/24/outline";

// Fonction pour convertir les données Checkov en texte lisible avec fichier en premier
const formatCheckovText = (data, filename) => {
  if (!data || !data.failed_checks) return "Aucune vérification disponible pour ce fichier.";
  return data.failed_checks.map(check => {
    const lines = check["file_line_range"] ? `${check["file_line_range"][0]}-${check["file_line_range"][1]}` : "Toutes les lignes";
    const filePath = check["file_path"] || filename; // Utilise file_path si disponible, sinon filename
    return `- Fichier: ${filePath} (Lignes ${lines})\n  - Check: **${check["check_name"]}** (${check["check_id"]})\n  - Résultat: Non conforme\n  - Détail: ${check["check_name"]}\n  - Suggestion: ${check["suggestion"] || "Aucune suggestion spécifique."}`;
  }).join("\n");
};

const AllInOne = ({ userId }) => {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [activeSection, setActiveSection] = useState(null);

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
          "X-User-ID": userId,
        },
        body: JSON.stringify({
          repo_url: url,
          repo_name: url.split("/").slice(-1)[0] || "unknown",
        }),
      });

      console.log("Response status:", response.status);
      console.log("Response headers:", Object.fromEntries(response.headers));
      const responseText = await response.text();
      console.log("Response text:", responseText);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
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
      console.error("Error details:", error);
      toast.error(error.message || "Erreur pendant le scan");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (content) => {
    navigator.clipboard.writeText(content)
      .then(() => {
        toast.success("Code copié avec succès !", {
          position: "top-right",
          autoClose: 2000,
          theme: "light",
        });
      })
      .catch(() => {
        toast.error("Erreur lors de la copie du code !", {
          position: "top-right",
          autoClose: 2000,
          theme: "light",
        });
      });
  };

  return (
    <div className="min-h-screen text-gray-200 font-sans flex items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-white rounded-xl shadow-2xl p-6 transition-all duration-300 scanner-content">
        <div className="flex justify-between items-center mb-6 border-b border-gray-300 pb-4">
          <h1 className="text-2xl font-bold text-green-400 flex items-center gap-2">
            <BugAntIcon className="h-7 w-7" />
            All-In-One Scanner
          </h1>
        </div>

        <div className="mb-4">
          <label htmlFor="repo-url" className="block text-gray-600 text-sm font-semibold mb-2">
            GitHub Repo URL:
          </label>
          <input
            id="repo-url"
            type="text"
            className="w-full border border-gray-300 rounded px-4 py-2 text-gray-800"
            placeholder="https://github.com/username/repo"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>

        <button
          onClick={handleScan}
          disabled={loading}
          className={`bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors duration-200 flex items-center justify-center gap-2 ${
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
          <div className="mt-6">
            {/* Boutons pour sélectionner la section */}
            <div className="flex gap-4 mb-4">
              <button
                onClick={() => setActiveSection("t5")}
                className={`px-4 py-2 rounded-lg font-semibold transition-colors duration-200 ${
                  activeSection === "t5" ? "bg-green-600 text-white" : "bg-gray-300 text-gray-700 hover:bg-gray-400"
                }`}
              >
                Corrected Files
              </button>
              <button
                onClick={() => setActiveSection("checkov")}
                className={`px-4 py-2 rounded-lg font-semibold transition-colors duration-200 ${
                  activeSection === "checkov" ? "bg-green-600 text-white" : "bg-gray-300 text-gray-700 hover:bg-gray-400"
                }`}
              >
                Validation & Conformity
              </button>
              <button
                onClick={() => setActiveSection("semgrep")}
                className={`px-4 py-2 rounded-lg font-semibold transition-colors duration-200 ${
                  activeSection === "semgrep" ? "bg-green-600 text-white" : "bg-gray-300 text-gray-700 hover:bg-gray-400"
                }`}
              >
                Vulnerability Analyser
              </button>
            </div>

            {/* Affichage conditionnel des sections */}
            {activeSection === "t5" && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
                  <DocumentTextIcon className="h-6 w-6" />
                  Corrected Files (T5)
                </h2>
                {Object.entries(result.t5 || {}).length > 0 ? (
                  Object.entries(result.t5 || {}).map(([filename, data]) => (
                    <div key={filename} className="mb-4">
                      <h4 className="text-md font-medium text-gray-700 mb-2">File: {filename} (Corrected)</h4>
                      {data.corrected && data.content ? (
                        <div className="relative">
                          <h5 className="text-gray-600 font-bold p-2">Corrected Content</h5>
                          <pre className="p-4 bg-slate-800 text-green-300 rounded-lg shadow-inner max-h-96 overflow-auto font-mono text-sm">
                            <code>{data.content}</code>
                          </pre>
                          <button
                            onClick={() => handleCopy(data.content)}
                            className="absolute top-2 right-2 bg-gray-700 text-white px-2 py-1 rounded hover:bg-gray-600 transition-colors duration-200 flex items-center gap-1"
                          >
                            <DocumentDuplicateIcon className="h-4 w-4" />
                          </button>
                        </div>
                      ) : (
                        <p className="text-red-500">Erreur : {data.error || "correction impossible"}</p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500">Aucun fichier corrigé trouvé.</p>
                )}
              </div>
            )}

            {activeSection === "checkov" && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
                  <CheckCircleIcon className="h-6 w-6" />
                  Validation & Conformity (Checkov)
                </h2>
                {result.checkov_corrected ? (
                  Object.entries(result.checkov_corrected).map(([filename, data]) => (
                    <div key={filename} className="mb-4">
                      <h4 className="text-md font-medium text-gray-700 mb-2">File: {filename} (Scanned)</h4>
                      <div className="relative">
                        <h5 className="text-gray-600 font-bold p-2">Checkov Results</h5>
                        <pre className="p-4 bg-slate-800 text-green-300 rounded-lg shadow-inner max-h-96 overflow-auto font-mono text-sm">
                          <code>{formatCheckovText(data, filename)}</code>
                        </pre>
                        <button
                          onClick={() => handleCopy(formatCheckovText(data, filename))}
                          className="absolute top-2 right-2 bg-gray-700 text-white px-2 py-1 rounded hover:bg-gray-600 transition-colors duration-200 flex items-center gap-1"
                        >
                          <DocumentDuplicateIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500">Aucun résultat Checkov trouvé.</p>
                )}
              </div>
            )}

            {activeSection === "semgrep" && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
                  <ExclamationTriangleIcon className="h-6 w-6" />
                  Vulnerability Analyser (Semgrep)
                </h2>
                {result.semgrep ? (
                  Object.entries(result.semgrep).map(([filename, data]) => (
                    <div key={filename} className="mb-4">
                      <h4 className="text-md font-medium text-gray-700 mb-2">File: {filename} (Scanned)</h4>
                      <div className="relative">
                        <h5 className="text-gray-600 font-bold p-2">Semgrep Results</h5>
                        <pre className="p-4 bg-slate-800 text-green-300 rounded-lg shadow-inner max-h-96 overflow-auto font-mono text-sm">
                          <code>{JSON.stringify(data, null, 2)}</code>
                        </pre>
                        <button
                          onClick={() => handleCopy(JSON.stringify(data, null, 2))}
                          className="absolute top-2 right-2 bg-gray-700 text-white px-2 py-1 rounded hover:bg-gray-600 transition-colors duration-200 flex items-center gap-1"
                        >
                          <DocumentDuplicateIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500">Aucun résultat Semgrep trouvé.</p>
                )}
              </div>
            )}
          </div>
        )}
        <ToastContainer position="top-right" autoClose={3000} theme="light" />
      </div>
    </div>
  );
};

export default AllInOne;
import React, { useState, useEffect } from "react";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { CheckCircleIcon, DocumentDuplicateIcon, ClockIcon, CloudArrowDownIcon, CodeBracketSquareIcon, ListBulletIcon } from "@heroicons/react/24/outline";
import { useLocation } from "react-router-dom";

import GitHubComplianceChecker from "../components/ComplianceChecker/GitHubComplianceChecker";
import SelectedReposComplianceChecker from "../components/ComplianceChecker/SelectedReposComplianceChecker";
import CodeComplianceChecker from "../components/ComplianceChecker/CodeComplianceChecker";
import FileComplianceChecker from "../components/ComplianceChecker/FileComplianceChecker";
import ResultDisplay from "../components/ComplianceChecker/ResultDisplay";
import HistoryModal from "../components/ComplianceChecker/HistoryModal";

import JenkinsfileContent from "../configs/Jenkinsfile";
import GitLabCIContent from "../configs/GitlabCi";
import GitHubActionsContent from "../configs/GithubActions";

const ComplianceChecker = () => {
  const [sourceType, setSourceType] = useState(null);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const location = useLocation();
  const selectedFiles = location.state?.selectedFiles || [];
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const userId = user.id;

  const resetChecker = () => {
    setSourceType(null);
    setResult(null);
    setIsLoading(false);
    document.querySelector(".checker-content")?.classList.add("opacity-0");
    setTimeout(() => {
      document.querySelector(".checker-content")?.classList.remove("opacity-0");
    }, 100);
  };

  const openHistory = () => setIsHistoryOpen(true);
  const closeHistory = () => setIsHistoryOpen(false);

  const handleCopy = (content) => {
    navigator.clipboard.writeText(content)
      .then(() => toast.success("Code copié avec succès !", { position: "top-right", autoClose: 2000, theme: "light" }))
      .catch(() => toast.error("Erreur lors de la copie du code !", { position: "top-right", autoClose: 2000, theme: "light" }));
  };

  const renderCode = () => {
    const configs = {
      jenkinsfile: JenkinsfileContent,
      gitlabci: GitLabCIContent,
      githubactions: GitHubActionsContent,
    };

    const labelMap = {
      jenkinsfile: "Jenkinsfile",
      gitlabci: "GitLab CI/CD",
      githubactions: "GitHub Actions",
    };

    if (!configs[sourceType]) return null;

    return (
      <div className="relative">
        <h2 className="text-gray-600 font-bold p-2">{labelMap[sourceType]}</h2>
        <pre className="p-4 bg-slate-800 text-green-300 rounded-lg shadow-inner max-h-96 overflow-auto font-mono text-sm">
          <code>{configs[sourceType]}</code>
        </pre>
        <button
          onClick={() => handleCopy(configs[sourceType])}
          className="absolute top-2 right-2 bg-gray-700 text-white px-2 py-1 rounded hover:bg-gray-600 transition-colors duration-200 flex items-center gap-1"
        >
          <DocumentDuplicateIcon className="h-4 w-4" />
          Copy
        </button>
      </div>
    );
  };

  useEffect(() => {
    document.body.style.overflow = isLoading ? "hidden" : "auto";
    return () => { document.body.style.overflow = "auto"; };
  }, [isLoading]);

  return (
    <div className="min-h-screen text-gray-200 font-sans flex items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-white rounded-xl shadow-2xl p-6 transition-all duration-300 checker-content">
        <div className="flex justify-between items-center mb-6 border-b border-gray-300 pb-4">
          <h1 className="text-2xl font-bold text-green-400 flex items-center gap-2">
            <CheckCircleIcon className="h-7 w-7" />
            Conformity Checker
          </h1>
          <button
            onClick={openHistory}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-all duration-200 flex items-center gap-2 shadow-md"
          >
            <ClockIcon className="h-5 w-5" />
            History
          </button>
        </div>

        {!sourceType ? (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">Select a type :</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                { type: "selected_repos", label: "Dépôts Sélectionnés", icon: <ListBulletIcon className="w-5 h-5" /> },
                {
                  type: "github",
                  label: "Lien GitHub",
                  icon: (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.333-1.756-1.333-1.756-1.09-.745.083-.73.083-.73 1.205.135 1.838 1.24 1.838 1.24 1.065 1.885 2.876 1.34 3.578 1.025.112-.795.434-1.34.792-1.645-2.776-.315-5.686-1.385-5.686-6.165 0-1.365.487-2.48 1.287-3.355-.13-.315-.558-1.585.123-3.305 0 0 1.05-.335 3.44 1.285A12.01 12.01 0 0112 4.8c1.065.005 2.135.145 3.14.43 2.39-1.62 3.435-1.285 3.435-1.285.685 1.72.255 2.99.125 3.305.805.875 1.285 1.99 1.285 3.355 0 4.795-2.915 5.845-5.695 6.155.445.385.84 1.145.84 2.31 0 1.665-.015 3.015-.015 3.42 0 .32.215.695.825.575C20.565 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z" />
                    </svg>
                  ),
                },
                { type: "code", label: "Code", icon: <CodeBracketSquareIcon className="h-5 w-5" /> },
                { type: "file", label: "Fichier", icon: <CloudArrowDownIcon className="h-5 w-5" /> },
                {
                  type: "jenkinsfile",
                  label: "Jenkinsfile",
                  icon: (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 2c5.514 0 10 4.486 10 10s-4.486 10-10 10S2 17.514 2 12 6.486 2 12 2zm0 3a1 1 0 00-1 1v4H8a1 1 0 100 2h3v4a1 1 0 102 0v-4h3a1 1 0 100-2h-3V6a1 1 0 00-1-1z" />
                    </svg>
                  ),
                },
                {
                  type: "githubactions",
                  label: "GitHub Actions",
                  icon: (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.333-1.756-1.333-1.756-1.09-.745.083-.73.083-.73 1.205.135 1.838 1.24 1.838 1.24 1.065 1.885 2.876 1.34 3.578 1.025.112-.795.434-1.34.792-1.645-2.776-.315-5.686-1.385-5.686-6.165 0-1.365.487-2.48 1.287-3.355-.13-.315-.558-1.585.123-3.305 0 0 1.05-.335 3.44 1.285A12.01 12.01 0 0112 4.8c1.065.005 2.135.145 3.14.43 2.39-1.62 3.435-1.285 3.435-1.285.685 1.72.255 2.99.125 3.305.805.875 1.285 1.99 1.285 3.355 0 4.795-2.915 5.845-5.695 6.155.445.385.84 1.145.84 2.31 0 1.665-.015 3.015-.015 3.42 0 .32.215.695.825.575C20.565 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z" />
                    </svg>
                  ),
                },
                {
                  type: "gitlabci",
                  label: "GitLab CI/CD",
                  icon: (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M23.64 14.67l-1.31-4-2.09-6.36a.66.66 0 00-.63-.45.66.66 0 00-.63.45l-2.09 6.36h-4.18L10.62 4.31a.66.66 0 00-.63-.45.66.66 0 00-.63.45l-2.09 6.36H3.07L1.76 14.67a.66.66 0 00.24.81l9.55 6.95a.66.66 0 00.78 0l9.55-6.95a.66.66 0 00.24-.81zm-15.2-2.5l1.31-4 1.31 4H8.44zm7.12 0l1.31-4 1.31 4h-2.62z" />
                    </svg>
                  ),
                },
              ].map(({ type, label, icon }) => (
                <button
                  key={type}
                  onClick={() => setSourceType(type)}
                  className="bg-green-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors duration-200 flex items-center justify-center gap-2 shadow-md"
                >
                  {icon}
                  {label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {sourceType === "selected_repos" && (
              <SelectedReposComplianceChecker setResult={setResult} isLoading={isLoading} setIsLoading={setIsLoading} userId={userId} />
            )}
            {sourceType === "github" && (
              <GitHubComplianceChecker setResult={setResult} isLoading={isLoading} setIsLoading={setIsLoading} userId={userId} />
            )}
            {sourceType === "code" && (
              <CodeComplianceChecker setResult={setResult} isLoading={isLoading} setIsLoading={setIsLoading} userId={userId} preSelectedFiles={selectedFiles} />
            )}
            {sourceType === "file" && (
              <FileComplianceChecker setResult={setResult} isLoading={isLoading} setIsLoading={setIsLoading} userId={userId} />
            )}
            {renderCode()}
            <div className="w-full overflow-y-auto bg-slate-600 p-4 rounded-lg shadow-inner border border-gray-700">
              <ResultDisplay result={result} userId={userId} />
            </div>
            <div className="flex justify-between space-x-4">
              <button
                onClick={resetChecker}
                className="bg-gray-600 text-white px-6 py-3 mt-4 rounded-lg font-semibold hover:bg-gray-700 transition-all duration-200 flex items-center gap-2 shadow-md"
              >
                Retour
              </button>
              <button
                onClick={() => setResult(null)}
                className="bg-gray-600 text-white px-6 py-3 mt-4 rounded-lg font-semibold hover:bg-gray-700 transition-all duration-200 flex items-center gap-2 shadow-md"
                style={{ display: result ? "flex" : "none" }}
              >
                Effacer le résultat
              </button>
            </div>
          </>
        )}

        <ToastContainer position="top-right" autoClose={3000} theme="light" />
        <HistoryModal isOpen={isHistoryOpen} onClose={closeHistory} userId={userId} scanType="compliance" />
      </div>
    </div>
  );
};

export default ComplianceChecker;

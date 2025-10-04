import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { DocumentTextIcon, SparklesIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import { useLocation } from "react-router-dom";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { dracula } from "react-syntax-highlighter/dist/esm/styles/prism";
import ReactMarkdown from "react-markdown";

const BASE_URL = (import.meta.env?.VITE_SIP || "http://localhost").replace(/\/+$/, "");
const API = `${BASE_URL}`;

const PoliciesGenerator = () => {
  const location = useLocation();
  const selectedFiles = location.state?.selectedFiles || [];
  const [dockerfileInput, setDockerfileInput] = useState("");
  const [correctedDockerfile, setCorrectedDockerfile] = useState("");
  const [instructions, setInstructions] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Populate textarea if files are passed
  useEffect(() => {
    if (selectedFiles.length > 0) {
      const firstFile = selectedFiles[0];
      setDockerfileInput(firstFile.content);
    }
  }, [selectedFiles]);

  const correctDockerfile = async () => {
    if (!dockerfileInput.trim()) {
      toast.warn("Please enter code to correct!", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API}:5000/t5`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ dockerfile: dockerfileInput }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Error while server connection!");
      }

      const data = await response.json();
      setCorrectedDockerfile(data.correction);
      setInstructions(data.explanation);
      
      toast.success("Configuration file corrected successfully!", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    } catch (error) {
      toast.error(error.message || "Error while processing", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const clearResults = () => {
    setCorrectedDockerfile("");
    setInstructions("");
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-800 mb-2 flex items-center gap-3">
            <DocumentTextIcon className="h-8 w-8 text-blue-500" />
            Configuration File Correction
          </h2>
          <p className="text-gray-600">Automatically correct and improve your configuration files using AI</p>
        </div>

        {/* Input Section */}
        <div className="mb-6">
          <label htmlFor="dockerfile-input" className="block text-gray-700 font-medium mb-2">
            Enter your configuration code:
          </label>
          <textarea
            id="dockerfile-input"
            value={dockerfileInput}
            onChange={(e) => setDockerfileInput(e.target.value)}
            className="w-full h-64 p-4 bg-gray-900 text-green-400 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-500 transition-all duration-200 font-mono text-sm"
            placeholder="FROM ubuntu:latest\nRUN apt-get update\n...\n\n# Paste your Dockerfile, Kubernetes YAML, Terraform, or other config files here"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={correctDockerfile}
            disabled={isLoading || !dockerfileInput.trim()}
            className={`bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors duration-200 flex items-center gap-2 ${
              isLoading || !dockerfileInput.trim() ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            {isLoading ? (
              <>
                <ArrowPathIcon className="h-5 w-5 animate-spin" />
                Generating Correction...
              </>
            ) : (
              <>
                <SparklesIcon className="h-5 w-5" />
                Correct Configuration
              </>
            )}
          </button>
          
          {(correctedDockerfile || instructions) && (
            <button
              onClick={clearResults}
              className="bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700 transition-colors duration-200"
            >
              Clear Results
            </button>
          )}
        </div>

        {/* Results Section */}
        {(correctedDockerfile || instructions) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Corrected Configuration */}
            {correctedDockerfile && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <SparklesIcon className="h-5 w-5 text-green-500" />
                  Corrected Configuration
                </h3>
                <div className="relative">
                  <SyntaxHighlighter
                    language="docker"
                    style={dracula}
                    customStyle={{
                      background: "#1e293b",
                      borderRadius: "0.5rem",
                      padding: "1rem",
                      maxHeight: "400px",
                      overflow: "auto",
                      fontSize: "0.875rem",
                    }}
                  >
                    {correctedDockerfile}
                  </SyntaxHighlighter>
                  <button
                    onClick={() => navigator.clipboard.writeText(correctedDockerfile)}
                    className="absolute top-2 right-2 bg-gray-700 hover:bg-gray-600 text-white p-2 rounded transition-colors"
                    title="Copy corrected code"
                  >
                    📋
                  </button>
                </div>
              </div>
            )}

            {/* Explanation */}
            {instructions && (
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <DocumentTextIcon className="h-5 w-5 text-blue-500" />
                  Changes & Explanations
                </h3>
                <div className="bg-white p-4 rounded-lg border max-h-96 overflow-auto">
                  <div className="prose prose-sm max-w-none text-gray-700">
                    <ReactMarkdown>{instructions}</ReactMarkdown>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Help Section */}
        {!correctedDockerfile && !instructions && (
          <div className="mt-8 bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-3">How it works:</h3>
            <ul className="text-blue-700 space-y-2">
              <li>• Paste your configuration file (Dockerfile, Kubernetes YAML, Terraform, etc.)</li>
              <li>• Our AI analyzes your code for best practices and security issues</li>
              <li>• Get an improved version with detailed explanations of changes</li>
              <li>• Copy the corrected configuration and apply it to your project</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default PoliciesGenerator;
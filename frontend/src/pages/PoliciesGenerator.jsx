import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { DocumentTextIcon, SparklesIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import { useLocation } from "react-router-dom";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { dracula } from "react-syntax-highlighter/dist/esm/styles/prism";
import ReactMarkdown from "react-markdown";

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
    setIsLoading(true);
    try {
      let accessToken = localStorage.getItem("token");
      const tokenExpiration = localStorage.getItem("token_expiration");

      if (!accessToken) {
        throw new Error("User not authenticated! ");
      }

      if (tokenExpiration && Date.now() > parseInt(tokenExpiration)) {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) {
          throw new Error("Session expired , you should reconnect!");
        }

        const refreshResponse = await fetch("http://127.0.0.1:5000/refresh", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        });

        if (!refreshResponse.ok) {
          throw new Error("Impossible to refresh the token, you should reconnect!");
        }

        const refreshData = await refreshResponse.json();
        accessToken = refreshData.access_token;
        localStorage.setItem("token", accessToken);
        localStorage.setItem("token_expiration", Date.now() + 3600000);
      }

      const response = await fetch("http://127.0.0.1:5000/t5", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization:`Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ dockerfile: dockerfileInput }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Error while server connexion!");
      }

      const data = await response.json();
      setCorrectedDockerfile(data.correction);
      setInstructions(data.explanation); // Store explanation
      toast.success("Docker file corrected successfully ", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    } catch (error) {
      toast.error(error.message || "Error while processing ", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-fit  flex items-center justify-center p-4">
      <div className="bg-slate-100 p-8 rounded-lg shadow-lg w-8/12">
        <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
          <DocumentTextIcon className="h-7 w-7 text-gray" />
          Configuration file correction
        </h2>

        {/* Input Section */}
        <div className="mb-6">
          <label htmlFor="dockerfile-input" className="text-gray-500 text-sm mb-2 block">
            Enter the code :
          </label>
          <textarea
            id="dockerfile-input"
            value={dockerfileInput}
            onChange={(e) => setDockerfileInput(e.target.value)}
            className="w-full h-64 p-4 bg-slate-600 text-white border border-gray-600 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-400 transition-all duration-200 font-mono"
            placeholder="FROM ubuntu:latest\nRUN apt-get update\n..."
          />
        </div>

        {/* Correct Button */}
        <button
          onClick={correctDockerfile}
          disabled={isLoading || !dockerfileInput.trim()}
          className={`w-full sm:w-auto bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors duration-200 flex items-center justify-center gap-2 ${
            isLoading || !dockerfileInput.trim() ? "opacity-50 cursor-not-allowed" : ""
          }`}
        >
          {isLoading ? (
            <>
              <ArrowPathIcon className="h-5 w-5 animate-spin" />
              Loading Generation ...
            </>
          ) : (
            <>
              <SparklesIcon className="h-5 w-5" />
              Correct
            </>
          )}
        </button>

        {/* Output Section */}
        {(correctedDockerfile || instructions) && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Corrected Dockerfile */}
            {correctedDockerfile && (
              <div>
                <label className="text-gray-400 text-sm mb-2 block">
                  Corrected file:
                </label>
                <SyntaxHighlighter
                  language="docker"
                  style={dracula}
                  customStyle={{
                    background: "#2b384a",
                    borderRadius: "0.5rem",
                    padding: "1rem",
                    maxHeight: "400px",
                    overflow: "auto",
                  }}
                >
                  {correctedDockerfile}
                </SyntaxHighlighter>
              </div>
            )}

            {/* Explanation */}
            {instructions && (
              <div>
                <label className="text-gray-400 text-sm mb-2 block">
                  Changement executed on the code  :
                </label>
                <div className="bg-gray-700 p-4 rounded-lg text-gray-100 max-h-96 overflow-auto">
                  <ReactMarkdown>{instructions}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PoliciesGenerator;
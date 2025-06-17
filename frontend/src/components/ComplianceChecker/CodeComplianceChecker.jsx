import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { CheckCircleIcon, ArrowPathIcon } from "@heroicons/react/24/outline";

const CodeComplianceChecker = ({ setResult, isLoading, setIsLoading, preSelectedFiles = [], userId }) => {
  const [codeInput, setCodeInput] = useState("");
  const [framework, setFramework] = useState("terraform");

  useEffect(() => {
    if (preSelectedFiles.length === 1) {
      const file = preSelectedFiles[0];
      setCodeInput(file.content);
      setFramework(file.framework !== "unknown" ? file.framework : "terraform");
    }
  }, [preSelectedFiles]);

  const checkCompliance = async () => {
    if (!codeInput.trim()) {
      toast.warn("Enter a code to verify !", {
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
        body: JSON.stringify({ content: codeInput, framework, input_type: "content" }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "error while verification !");
      }

      const data = await response.json();
      setResult(data); // Pass raw response
      toast.success("Verification finished successfully ", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    } catch (error) {
      toast.error(error.message || "error while verification !", {
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
        Validation & Conformity - Code (Terraform, Kubernetes, Dockerfile)
      </h2>
      {preSelectedFiles.length === 1 && (
        <div className="mb-6">
          <label className="text-gray-400 text-sm mb-2 block">
            Selected file : {preSelectedFiles[0].file_name}
          </label>
        </div>
      )}
      <div className="mb-6">
        <label htmlFor="framework" className="text-gray-400 text-sm mb-2 block">
          Type of code  :
        </label>
        <select
          id="framework"
          value={framework}
          onChange={(e) => setFramework(e.target.value)}
          className="w-full bg-gray-700 text-gray-100 border border-gray-600 rounded-lg p-3"
        >
          <option value="terraform">Terraform (.tf)</option>
          <option value="kubernetes">Kubernetes (.yaml)</option>
          <option value="dockerfile">Dockerfile</option>
        </select>
      </div>
      <div className="mb-6">
        <label htmlFor="code-input" className="text-gray-400 text-sm mb-2 block">
          File content  :
        </label>
        <textarea
          id="code-input"
          value={codeInput}
          onChange={(e) => setCodeInput(e.target.value)}
          className="w-full h-32 p-4 bg-gray-700 text-gray-100 border border-gray-600 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-green-500 placeholder-gray-400 transition-all duration-200 font-mono"
          placeholder="Enter the code of the file ... "
        />
      </div>
      <button
        onClick={checkCompliance}
        disabled={isLoading || !codeInput.trim()}
        className={`w-full sm:w-auto bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors duration-200 flex items-center justify-center gap-2 ${
          isLoading || !codeInput.trim() ? "opacity-50 cursor-not-allowed" : ""
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

export default CodeComplianceChecker;
import React, { useState } from "react";
import { toast } from "react-toastify";
import { CheckCircleIcon, ArrowPathIcon } from "@heroicons/react/24/outline";

const FileComplianceChecker = ({ setResult, isLoading, setIsLoading, userId }) => {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const checkCompliance = async () => {
    if (!file) {
      toast.warn("Select a configuration file or a folder zip to scan!", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
      return;
    }

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("input_type", file.name.endsWith(".zip") ? "zip" : "file");

      const response = await fetch("http://127.0.0.1:5000/checkov", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "X-User-ID": userId,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Error while verification");
      }

      const data = await response.json();
      setResult(data); // Pass raw response to ResultDisplay
      toast.success("Verification finished successfully ", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    } catch (error) {
      toast.error(error.message || "Error while verification !", {
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
        Validation &  Conformité - Configuration file or ZIP (NIST, ISO 27001, GDPR, HIPAA)
      </h2>
      <div className="mb-6">
        <label htmlFor="file-upload" className="text-gray-500 text-sm mb-2 block">
         Select a configuration file or folder  :
        </label>
        <input
          id="file-upload"
          type="file"
          accept=".zip,.txt,.json,.yml,.yaml,.tf,Dockerfile"
          onChange={handleFileChange}
          className="w-full text-gray-100 bg-gray-700 border border-gray-600 rounded-lg p-3 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-green-600 file:text-white hover:file:bg-green-700"
        />
      </div>
      <button
        onClick={checkCompliance}
        disabled={isLoading || !file}
        className={`w-full sm:w-auto bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors duration-200 flex items-center justify-center gap-2 ${
          isLoading || !file ? "opacity-50 cursor-not-allowed" : ""
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

export default FileComplianceChecker;
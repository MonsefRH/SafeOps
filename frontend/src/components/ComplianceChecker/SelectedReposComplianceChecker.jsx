import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { CheckCircleIcon, ArrowPathIcon } from "@heroicons/react/24/outline";

const SelectedReposComplianceChecker = ({ setResult, isLoading, setIsLoading, userId }) => {
  const [repos, setRepos] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState("");
  const [reposLoading, setReposLoading] = useState(false);
  const [reposError, setReposError] = useState("");

  useEffect(() => {
    const fetchRepos = async () => {
      setReposLoading(true);
      setReposError("");
      try {
        const response = await fetch("http://127.0.0.1:5000/github/repos", {
          method: "GET",
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Trouble while retrieving repos.");
        }

        const data = await response.json();
        const selectedRepos = data.filter((repo) => repo.is_selected);
        setRepos(selectedRepos);
        if (selectedRepos.length > 0) {
          setSelectedRepo(selectedRepos[0].full_name);
        }
        toast.success("Selectionned repos loaded !", {
          toastId: "selectionned-repos-loaded",
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      } catch (err) {
        setReposError("Impossible to retrieve the selected repos ");
        toast.error(err.message, {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      } finally {
        setReposLoading(false);
      }
    };

    fetchRepos();
  }, []);

  const checkCompliance = async () => {
    if (!selectedRepo) {
      toast.warn("Select a repos to scan !", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
      return;
    }

    setIsLoading(true);
    try {
      const repoData = repos.find((r) => r.full_name === selectedRepo);
      const response = await fetch("http://127.0.0.1:5000/checkov", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "X-User-ID": userId, // Add user_id
        },
        body: JSON.stringify({ repo_url: repoData.html_url, input_type: "repo" }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Error while verification ");
      }

      const data = await response.json();
      setResult({ repo: repoData.full_name, data }); // Pass raw response with repo info
      toast.success("Verification finished successfully", {
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
        Validation & Conformité - Selected Repos
      </h2>
      {reposLoading ? (
        <div className="flex justify-center items-center py-4">
          <ArrowPathIcon className="h-6 w-6 text-blue-500 animate-spin" />
          <span className="ml-2 text-gray-400">Loading Repos...</span>
        </div>
      ) : reposError ? (
        <div className="flex justify-center items-center py-4 text-red-400">
          <p>{reposError}</p>
        </div>
      ) : repos.length > 0 ? (
        <div>
          <div className="mb-6">
            <label htmlFor="repo-select" className="text-gray-400 text-sm mb-2 block">
              Select a repository  :
            </label>
            <select
              id="repo-select"
              value={selectedRepo}
              onChange={(e) => setSelectedRepo(e.target.value)}
              className="w-full bg-gray-700 text-gray-100 border border-gray-600 rounded-lg p-3"
            >
              <option value=""> Select a project </option>
              {repos.map((repo) => (
                <option key={repo.full_name} value={repo.full_name}>
                  {repo.full_name}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={checkCompliance}
            disabled={isLoading || !selectedRepo}
            className={`w-full sm:w-auto bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors duration-200 flex items-center justify-center gap-2 ${
              isLoading || !selectedRepo ? "opacity-50 cursor-not-allowed" : ""
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
      ) : (
        <p className="text-gray-400">There is no selected repos yet , go to dashboard to select one   </p>
      )}
    </div>
  );
};

export default SelectedReposComplianceChecker;
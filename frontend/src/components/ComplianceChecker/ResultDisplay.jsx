import React, { useState } from "react";
import { toast } from "react-toastify";
import { DocumentDuplicateIcon } from "@heroicons/react/24/outline";

const ResultDisplay = ({ result, item_name}) => {
  const [activeTab, setActiveTab] = useState("checkov"); // Default tab: Standard Checkov Output
  console.log(result);

  if (!result) return <p className="text-gray-400">Result Not available </p>;

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(result, null, 2)).then(() => {
      toast.success("Resultat copied", { position: "top-right", autoClose: 2000, theme: "light" });
    });
  };

  const renderResults = (results) => {
    // Handle array of results (legacy support for multi-repo)
    if (Array.isArray(results)) {
      return results.map((item, index) => (
        <div key={index} className="mb-4">
          <h3 className="text-lg font-semibold text-gray-100">{item.repo}</h3>
          {item.error ? (
            <p className="text-red-400">Error : {item.error}</p>
          ) : (
            renderSingleResult(item.data)
          )}
        </div>
      ));
    }

    // Handle single result from SelectedReposComplianceChecker
    if (results.repo && results.data) {
      return (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-100">{results.repo}</h3>
          {renderSingleResult(results.data)}
        </div>
      );
    }

    // Handle raw Checkov result (from GitHubComplianceChecker, CodeComplianceChecker, etc.)
    return renderSingleResult(results);
  };

  const renderSingleResult = (data) => {
    // Handle single file result
    if (data.file_path) {
      const groupedChecks = {
        [data.file_path]: data.failed_checks || [],
      };
      return renderGroupedResults({ failed_checks: data.failed_checks, passed_checks: data.passed_checks, files_found: [data.file_path] }, groupedChecks);
    }

    // Handle directory/repo result
    const results = data.results || data;
    if (!results.passed_checks && !results.failed_checks && !results.summary) {
      return <p className="text-gray-400">No available result .</p>;
    }

    // Group failed checks by file_path
    const groupedChecks = {};
    (results.failed_checks || []).forEach((check) => {
      const filePath = check.file_path;
      if (!groupedChecks[filePath]) {
        groupedChecks[filePath] = [];
      }
      groupedChecks[filePath].push(check);
    });

    return renderGroupedResults(results, groupedChecks);
  };

  const renderGroupedResults = (results, groupedChecks) => {
    // Extract repository name from repo_url
    const repoUrl = result?.repo_url;
    const ItemName = (repoUrl != null )? repoUrl.split("/").slice(-2).join("/")
        : (item_name ? item_name : "File");


    return (
      <div>
        {/* Repository Name */}
        {ItemName !== "File"  && <h3 className="text-lg font-semibold text-gray-100 mb-4">{ItemName}</h3>}

        {/* Summary */}
        <div className="mb-4">
          {results.compliant !== undefined && (
            <p className="text-gray-100">Conforme : {results.compliant ? "Yes" : "No"}</p>
          )}
          {results.summary?.passed!==0 && <p className="text-green-400">Successed Verifications  : { results.summary?.passed || results.passed_checks?.length }</p>}
          <p className="text-red-400">Failed Verifications  : {results.summary?.failed || results.failed_checks?.length || 0}</p>
          {(results.score !== undefined &&  results.score !== 0) && <p className="text-gray-100">Score : {results.score}%</p>}
        </div>

        {/* Tabs */}
        <div className="mb-4">
          <div className="flex border-b border-gray-700">
            <button
              className={`px-4 py-2 font-semibold ${
                activeTab === "checkov" ? "border-b-2 border-green-500 text-green-400" : "text-gray-400"
              }`}
              onClick={() => setActiveTab("checkov")}
            >
              Results
            </button>
            <button
              className={`px-4 py-2 font-semibold ${
                activeTab === "recommendations" ? "border-b-2 border-green-500 text-green-400" : "text-gray-400"
              }`}
              onClick={() => setActiveTab("recommendations")}
            >
              Recommendations
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === "checkov" && (
          <div>
            {results.failed_checks?.length > 0 && (
              <div className="mb-4">
                <h4 className="text-gray-100 font-semibold">Failed Verifications  :</h4>
                {Object.entries(groupedChecks).map(([filePath, checks]) => (
                  <div key={filePath} className="mt-4">
                    <h5 className="text-red-500 font-medium">----------------{filePath}----------------</h5>
                    <ul className="list-disc list-inside text-gray-300">
                      {checks.map((check, idx) => (
                        <li key={idx}>
                          <span className="text-red-400">{check.check_id}</span> - {check.check_name} (Line : {check.file_line_range?.join("-")})
                          {check.guideline && <span>, Guideline: <a href={check.guideline} className="text-blue-400" target="_blank" rel="noopener noreferrer">{check.guideline}</a></span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
            {results.passed_checks?.length > 0 && (
              <div className="mb-4">
                <h4 className="text-gray-100 font-semibold">Vérifications réussies :</h4>
                <ul className="list-disc list-inside text-gray-300">
                  {results.passed_checks.map((check, idx) => (
                    <li key={idx}>
                      <span className="text-green-400">{check.check_id}</span> - {check.check_name} (File : {check.file_path}, Line : {check.file_line_range?.join("-")})
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === "recommendations" && (
          <div>
            {results.failed_checks?.length > 0 ? (
              Object.entries(groupedChecks).map(([filePath, checks]) => (
                <div key={filePath} className="mt-4">
                  <h5 className="text-red-700 font-medium">----------------{filePath}----------------</h5>
                  <ul className="list-disc list-inside text-gray-300">
                    {checks.map((check, idx) => (
                      <li key={idx} className="mb-2">
                        <span className="text-red-400">{check.check_id}</span> - {check.check_name} (Line : {check.file_line_range?.join("-")})
                        <div className="text-slate-400 mt-1">Recommendation: {check.suggestion}</div>
                      </li>
                    ))}
                  </ul>
                </div>
              ))
            ) : (
              <p className="text-gray-400">No available recommendations .</p>
            )}
          </div>
        )}

        {/* Scanned Files */}
        {results.files_found?.length > 0 && (
          <div className="mt-4">
            <h4 className="text-gray-100 font-semibold">Files scanned :</h4>
            <ul className="list-disc list-inside text-gray-300">
              {results.files_found.map((file, idx) => (
                <li key={idx}>{file}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
      <div className="mt-6 w-full max-w-260 relative h-50">
        <label htmlFor="compliance-result" className="text-gray-400 text-sm mb-2 block">
          Verification Result :
        </label>
        <div
            className="p-4 bg-slate-800 text-green-300 rounded-lg shadow-inner max-h-96 overflow-y-auto font-mono text-sm">
          {renderResults(result)}
          <button
              onClick={handleCopy}
              className="absolute top-8 right-6 bg-gray-700 text-white px-2 py-1 rounded hover:bg-gray-600"
          >
            <DocumentDuplicateIcon className="h-4 w-4"/>
          </button>
        </div>

      </div>
  );
};

export default ResultDisplay;
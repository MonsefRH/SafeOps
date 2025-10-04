import React, { useState, useEffect, useMemo } from "react";
import { toast } from "react-toastify";
import { XCircleIcon, ChevronDownIcon, ChevronUpIcon, MagnifyingGlassIcon } from "@heroicons/react/24/outline";
import ResultDisplay from "./ResultDisplay";
import debounce from "lodash.debounce";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:5000";

const HistoryModal = ({ isOpen, onClose, userId, scanType }) => {
  const [history, setHistory] = useState([]);
  const [selectedScan, setSelectedScan] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState({ from: "", to: "" });
  const [expandedGroups, setExpandedGroups] = useState({});

  // Fetch scan history when modal opens
  useEffect(() => {
    if (!isOpen || !userId) return;

    const fetchHistory = async () => {
      setIsLoading(true);
      try {
        const scan_type = scanType === "vulnerability" ? "semgrep" : "checkov";
        const url = scanType
          ? `${API_URL}/history?scan_type=${scan_type}`
          : `${API_URL}/history`;
        const response = await fetch(url, {
          headers: {
            "X-User-ID": userId,
          },
        });
        const data = await response.json();
        if (response.ok) {
          setHistory(data);
        } else {
          toast.error("Error while receiving histories! ", {
            position: "top-right",
            autoClose: 2000,
            theme: "light",
          });
        }
      } catch (error) {
        toast.error("Server Error !", {
          position: "top-right",
          autoClose: 2000,
          theme: "light",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, [isOpen, userId, scanType]);

  // Format date to a readable format
  const formatDate = (isoString) => {
    if (!isoString) return "N/A";
    const date = new Date(isoString);
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  };

  // Filter history by date range
  const filteredByDateHistory = useMemo(() => {
    if (!dateRange.from && !dateRange.to) return history;

    const fromDate = dateRange.from ? new Date(dateRange.from) : null;
    const toDate = dateRange.to ? new Date(dateRange.to) : null;

    return history.filter((scan) => {
      const scanDate = new Date(scan.created_at);
      if (fromDate && scanDate < fromDate) return false;
      if (toDate && scanDate > toDate) return false;
      return true;
    });
  }, [history, dateRange]);

  // Group scans into three categories: Files, Zip Files, and Repositories
  const groupedHistory = useMemo(() => {
    const groups = {
      Files: [],
      "Zip Files": [],
      Repositories: {},
    };

    filteredByDateHistory.forEach((scan) => {
      const isZip =
        scan.input_type === "zip" || scan.item_name?.toLowerCase().endsWith(".zip");
      const hasRepo = !!scan.repo_url;

      if (hasRepo) {
        // Group under Repositories
        const repoKey = scan.repo_url.split("/").slice(-2).join("/") || "Repository without name ";
        if (!groups.Repositories[repoKey]) {
          groups.Repositories[repoKey] = [];
        }
        groups.Repositories[repoKey].push({
          ...scan,
          ItemName: scan.repo_url
            ? scan.repo_url.split("/").slice(-2).join("/")
            : scan.item_name
            ? scan.item_name
            : "File ",
        });
      } else if (isZip) {
        // Group under Zip Files
        groups["Zip Files"].push({
          ...scan,
          ItemName: scan.item_name || " ZIP File ",
        });
      } else {
        // Group under Files
        groups.Files.push({
          ...scan,
          ItemName: scan.item_name || "File",
        });
      }
    });

    // Sort scans within each category
    groups.Files.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    groups["Zip Files"].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    Object.keys(groups.Repositories).forEach((repo) => {
      groups.Repositories[repo].sort(
        (a, b) => new Date(b.created_at) - new Date(a.created_at)
      );
    });

    // Sort repository keys alphabetically
    const sortedRepos = {};
    Object.keys(groups.Repositories)
      .sort((a, b) => a.localeCompare(b))
      .forEach((repo) => {
        sortedRepos[repo] = groups.Repositories[repo];
      });
    groups.Repositories = sortedRepos;

    return groups;
  }, [filteredByDateHistory]);

  // Filter scans based on search query
  const filteredGroupedHistory = useMemo(() => {
    if (!searchQuery.trim()) return groupedHistory;

    const query = searchQuery.toLowerCase().trim();
    const filtered = {
      Files: [],
      "Zip Files": [],
      Repositories: {},
    };

    // Filter Files
    filtered.Files = groupedHistory.Files.filter(
      (scan) =>
        scan.ItemName.toLowerCase().includes(query) ||
        scan.status?.toLowerCase().includes(query)
    );

    // Filter Zip Files
    filtered["Zip Files"] = groupedHistory["Zip Files"].filter(
      (scan) =>
        scan.ItemName.toLowerCase().includes(query) ||
        scan.status?.toLowerCase().includes(query)
    );

    // Filter Repositories
    Object.keys(groupedHistory.Repositories).forEach((repo) => {
      const filteredScans = groupedHistory.Repositories[repo].filter(
        (scan) =>
          scan.ItemName.toLowerCase().includes(query) ||
          scan.repo_url?.toLowerCase().includes(query) ||
          scan.status?.toLowerCase().includes(query)
      );
      if (filteredScans.length > 0) {
        filtered.Repositories[repo] = filteredScans;
      }
    });

    return filtered;
  }, [groupedHistory, searchQuery]);

  // Initialize expanded groups to be open by default
  useEffect(() => {
    const initialExpanded = {};
    // Expand top-level categories
    ["Files", "Zip Files", "Repositories"].forEach((category) => {
      initialExpanded[category] = true;
    });
    // Expand repository sub-groups
    Object.keys(groupedHistory.Repositories).forEach((repo) => {
      initialExpanded[`Repositories-${repo}`] = false;
    });
    setExpandedGroups(initialExpanded);
  }, [groupedHistory]);

  // Debounced search handler
  const handleSearch = debounce((value) => {
    setSearchQuery(value);
  }, 300);

  // Handle date range change
  const handleDateChange = (e) => {
    const { name, value } = e.target;
    setDateRange((prev) => ({ ...prev, [name]: value }));
  };

  // Toggle group expansion
  const toggleGroup = (group) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [group]: !prev[group],
    }));
  };

  // Handle card click to show scan details
  const handleCardClick = (scan) => {
    setSelectedScan(scan);
  };

  // Close scan details
  const closeScanDetails = () => {
    setSelectedScan(null);
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="history-modal-title"
    >
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2
            id="history-modal-title"
            className="text-2xl font-bold text-slate-600"
          >
            Scan History
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-300"
            aria-label="Fermer la modale"
          >
            <XCircleIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="mb-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Search by repo , file or status ..."
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full p-2 pl-10 bg-gray-300 text-gray-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Rechercher dans l'historique"
            />
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
          </div>
        </div>

        {/* Date Range Filter */}
        <div className="mb-4 flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label htmlFor="date-from" className="text-gray-500 text-sm mb-1 block">
              From
            </label>
            <input
              type="datetime-local"
              id="date-from"
              name="from"
              value={dateRange.from}
              onChange={handleDateChange}
              className="w-full p-2 bg-gray-400 text-gray-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Filtrer par date de début"
            />
          </div>
          <div className="flex-1">
            <label htmlFor="date-to" className="text-gray-500 text-sm mb-1 block">
              To
            </label>
            <input
              type="datetime-local"
              id="date-to"
              name="to"
              value={dateRange.to}
              onChange={handleDateChange}
              className="w-full p-2 bg-gray-400 text-gray-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Filtrer par date de fin"
            />
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, index) => (
              <div
                key={index}
                className="border border-gray-600 p-4 rounded-lg animate-pulse"
              >
                <div className="h-4 bg-gray-600 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-600 rounded w-1/2 mb-2"></div>
                <div className="h-4 bg-gray-600 rounded w-1/4"></div>
              </div>
            ))}
          </div>
        ) : (filteredGroupedHistory.Files.length === 0 &&
            filteredGroupedHistory["Zip Files"].length === 0 &&
            Object.keys(filteredGroupedHistory.Repositories).length === 0) ? (
          <p className="text-gray-400 text-center py-4">
            No history found .
          </p>
        ) : !selectedScan ? (
          <div className="space-y-4">
            {/* Files Category */}
            {filteredGroupedHistory.Files.length > 0 && (
              <div className="border border-gray-300 rounded-lg">
                <button
                  onClick={() => toggleGroup("Files")}
                  className="w-full flex justify-between items-center p-4 bg-gray-500  rounded-lg hover:bg-gray-600 transition-colors duration-200"
                  aria-expanded={expandedGroups["Files"]}
                  aria-controls="group-files"
                >
                  <h3 className="text-lg font-semibold text-gray-100">
                    Local files
                  </h3>
                  {expandedGroups["Files"] ? (
                    <ChevronUpIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                  )}
                </button>
                {expandedGroups["Files"] && (
                  <div id="group-files" className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredGroupedHistory.Files.map((scan) => (
                      <div
                        key={scan.id}
                        onClick={() => handleCardClick(scan)}
                        className={`bg-gray-700 p-4 rounded-lg cursor-pointer hover:bg-gray-600 transition-colors duration-200 ${
                          scan.scan_type === "checkov"
                            ? "border-l-4 border-blue-500"
                            : "border-l-4 border-green-500"
                        }`}
                      >
                        <h4 className="text-md font-semibold text-gray-100">
                          {scan.ItemName}
                        </h4>
                        <p className="text-gray-300">Statut: {scan.status}</p>
                        <p className="text-gray-300">
                          Conforme: {scan.compliant ? "Oui" : "Non"}
                        </p>
                        <p className="text-gray-400 text-sm">
                          Date: {formatDate(scan.created_at)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Zip Files Category */}
            {filteredGroupedHistory["Zip Files"].length > 0 && (
              <div className="border border-gray-600 rounded-lg">
                <button
                  onClick={() => toggleGroup("Zip Files")}
                  className="w-full flex justify-between items-center p-4  bg-gray-500 rounded-lg hover:bg-gray-600 transition-colors duration-200"
                  aria-expanded={expandedGroups["Zip Files"]}
                  aria-controls="group-zip-files"
                >
                  <h3 className="text-lg font-semibold text-gray-100">
                    zip files
                  </h3>
                  {expandedGroups["Zip Files"] ? (
                    <ChevronUpIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                  )}
                </button>
                {expandedGroups["Zip Files"] && (
                  <div id="group-zip-files" className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredGroupedHistory["Zip Files"].map((scan) => (
                      <div
                        key={scan.id}
                        onClick={() => handleCardClick(scan)}
                        className={`bg-gray-700 p-4 rounded-lg cursor-pointer hover:bg-gray-600 transition-colors duration-200 ${
                          scan.scan_type === "checkov"
                            ? "border-l-4 border-blue-500"
                            : "border-l-4 border-green-500"
                        }`}
                      >
                        <h4 className="text-md font-semibold text-gray-100">
                          {scan.ItemName}
                        </h4>
                        <p className="text-gray-300">Statut: {scan.status}</p>
                        <p className="text-gray-300">
                          Conforme: {scan.compliant ? "Oui" : "Non"}
                        </p>
                        <p className="text-gray-400 text-sm">
                          Date: {formatDate(scan.created_at)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Repositories Category */}
            {Object.keys(filteredGroupedHistory.Repositories).length > 0 && (
              <div className="border border-gray-600 rounded-lg">
                <button
                  onClick={() => toggleGroup("Repositories")}
                  className="w-full flex justify-between items-center p-4 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors duration-200"
                  aria-expanded={expandedGroups["Repositories"]}
                  aria-controls="group-repositories"
                >
                  <h3 className="text-lg font-semibold text-gray-100">
                    Repositories
                  </h3>
                  {expandedGroups["Repositories"] ? (
                    <ChevronUpIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                  )}
                </button>
                {expandedGroups["Repositories"] && (
                  <div id="group-repositories" className="p-4 space-y-4">
                    {Object.keys(filteredGroupedHistory.Repositories).map((repo) => {
                      const isRepoExpanded = expandedGroups[`Repositories-${repo}`] || false;
                      return (
                        <div key={repo} className="border border-gray-600 rounded-lg">
                          <button
                            onClick={() => toggleGroup(`Repositories-${repo}`)}
                            className="w-full flex justify-between items-center p-4 bg-gray-900 rounded-lg hover:bg-gray-600 transition-colors duration-200"
                            aria-expanded={isRepoExpanded}
                            aria-controls={`group-repo-${repo}`}
                          >
                            <h4 className="text-md font-semibold text-gray-100">
                              {repo}
                            </h4>
                            {isRepoExpanded ? (
                              <ChevronUpIcon className="h-5 w-5 text-gray-400" />
                            ) : (
                              <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                            )}
                          </button>
                          {isRepoExpanded && (
                            <div
                              id={`group-repo-${repo}`}
                              className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4"
                            >
                              {filteredGroupedHistory.Repositories[repo].map((scan) => (
                                <div
                                  key={scan.id}
                                  onClick={() => handleCardClick(scan)}
                                  className={`bg-gray-700 p-4 rounded-lg cursor-pointer hover:bg-gray-600 transition-colors duration-200 ${
                                    scan.scan_type === "checkov"
                                      ? "border-l-4 border-blue-500"
                                      : "border-l-4 border-green-500"
                                  }`}
                                >
                                  <h5 className="text-sm font-semibold text-gray-100">
                                    {scan.ItemName}
                                  </h5>
                                  <p className="text-gray-300">Statut: {scan.status}</p>
                                  <p className="text-gray-300">
                                    Conforme: {scan.compliant ? "Oui" : "Non"}
                                  </p>
                                  <p className="text-gray-400 text-sm">
                                    Date: {formatDate(scan.created_at)}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div>
            <button
              onClick={closeScanDetails}
              className="mb-4 bg-gray-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-gray-700 transition-colors duration-200"
              aria-label="Retour à l'historique"
            >
              Back to history
            </button>
            <ResultDisplay 
            result={selectedScan.scan_result} 
            item_name={selectedScan.ItemName} />
          </div>
        )}
      </div>
    </div>
  );
};

export default React.memo(HistoryModal);
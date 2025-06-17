import React, { useState, useEffect } from "react";
import {
  ChartBarIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  StarIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from "@heroicons/react/24/outline";
import { Link } from "react-router-dom";
import { toast } from "react-toastify";

// Utility function for smooth number animation
const useCountUp = (end, duration = 2000) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const increment = end / (duration / 16); // 60fps
    const step = () => {
      start += increment;
      if (start >= end) {
        setCount(end);
        return;
      }
      setCount(Math.floor(start));
      requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [end, duration]);

  return count;
};

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [repos, setRepos] = useState([]);
  const [reposLoading, setReposLoading] = useState(false);
  const [reposError, setReposError] = useState("");
  const [isGithubLinked, setIsGithubLinked] = useState(null);
  const [pat, setPat] = useState("");
  const [selectedRepos, setSelectedRepos] = useState([]);
  const [availableRepos, setAvailableRepos] = useState([]);
  const [showGithubSection, setShowGithubSection] = useState(true);

  // Fetch dashboard stats
  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      setError("");
      try {
        const user = JSON.parse(localStorage.getItem("user") || "{}");
        const userId = user.id;
        const response = await fetch("http://127.0.0.1:5000/stats", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "X-User-ID": userId,
          },
        });

        if (!response.ok) {
          throw new Error("Erreur lors de la récupération des données");
        }

        const data = await response.json();
        setStats(data);
      } catch (err) {
        setError("Impossible de charger les données du tableau de bord");
        console.error("Erreur stats:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  // Fetch GitHub repos
  useEffect(() => {
    const fetchGithubRepos = async () => {
      setReposLoading(true);
      setReposError("");
      try {
        const response = await fetch("http://127.0.0.1:5000/github/repos", {
          method: "GET",
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });

        if (response.status === 404) {
          setIsGithubLinked(false);
          setRepos([]);
          return;
        }

        if (!response.ok) {
          throw new Error("Échec récupération dépôts");
        }

        const data = await response.json();
        setRepos(data);
        setSelectedRepos(data.filter(repo => repo.is_selected).map(repo => repo.full_name));
        setIsGithubLinked(true);
        toast.success("Repos Github Fetched", {
          toastId: "github-repos-loaded",
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      } catch (err) {
        setReposError("Impossible to get the GitHub Repos");
        console.error("Erreur GitHub:", err);
        setIsGithubLinked(false);
      } finally {
        setReposLoading(false);
      }
    };

    fetchGithubRepos();
  }, []);


  // Handle PAT submission
  const handlePatSubmit = async () => {
    if (!pat) {
      toast.error("Enter the Github Token", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:5000/github/validate-token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          token: pat,
          selected_repos: selectedRepos,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        setRepos(data.repos.map(repo => ({ ...repo, is_selected: selectedRepos.includes(repo.full_name) })));
        setIsGithubLinked(true);
        setPat("");
        setSelectedRepos([]);
        setAvailableRepos([]);
        toast.success("Token validated , Repos Charged", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      } else {
        toast.error(data.error || "Token invalid", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      }
    } catch (err) {
      toast.error("Server Connexion Error ", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    }
  };

  // Fetch repos for PAT preview
  const handlePatPreview = async () => {
    if (!pat) {
      toast.error("Enter the Github Token", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
      return;
    }

    try {
      const response = await fetch("https://api.github.com/user/repos", {
        method: "GET",
        headers: { Authorization: `Bearer ${pat}` },
      });

      if (!response.ok) {
        throw new Error("token invalid");
      }

      const repos = await response.json();
      const repoData = repos.map((repo) => ({
        name: repo.name,
        full_name: repo.full_name,
        description: repo.description || "",
        html_url: repo.html_url,
        is_selected: selectedRepos.includes(repo.full_name),
      }));
      setAvailableRepos(repoData);
      toast.success("Repos charged !", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    } catch (err) {
      toast.error("Jeton invalid or error API", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
      setAvailableRepos([]);
    }
  };

  // Toggle repo selection
  const toggleRepoSelection = (full_name) => {
    setSelectedRepos((prev) =>
      prev.includes(full_name)
        ? prev.filter((r) => r !== full_name)
        : [...prev, full_name]
    );
    setRepos((prev) =>
      prev.map((repo) =>
        repo.full_name === full_name
          ? { ...repo, is_selected: !repo.is_selected }
          : repo
      )
    );
  };

  // Save selected repos
  const handleSaveRepos = async () => {
    try {
      const response = await fetch("http://127.0.0.1:5000/github/save-repos", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          selected_repos: repos.filter((repo) => selectedRepos.includes(repo.full_name)),
        }),
      });

      if (response.ok) {
        toast.success("Repos saved !", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      } else {
        const data = await response.json();
        toast.error(data.error || "Error while saving", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      }
    } catch (err) {
      toast.error("Erreur serveur", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    }
  };

  // Sort repos to pin selected ones at the top
  const sortedRepos = [...repos].sort((a, b) => {
    if (a.is_selected && !b.is_selected) return -1;
    if (!a.is_selected && b.is_selected) return 1;
    return a.full_name.localeCompare(b.full_name);
  });

  // Animated stats
  // Define animated counts unconditionally
  const policiesCount = useCountUp(stats ? stats.policies : 0, 1500);
  const alertsCount = useCountUp(stats ? stats.alerts : 0, 1500);
  const securityScoreCount = useCountUp(stats ? stats.securityScore : 0, 1500);

  // Filter stats (unchanged)
  const filteredStats = stats
    ? {
        policies: policiesCount,
        alerts: alertsCount,
        securityScore: securityScoreCount,
      }
    : null;

  return (
    <div className="h-fit flex flex-col p-6  min-h-screen">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-center mb-8">
        <h2 className="text-3xl font-semibold text-slate-700 mb-4 sm:mb-0 flex items-center gap-3 transition-all duration-300">
          <ChartBarIcon className="h-8 w-8 text-blue-700 animate-pulse" />
          Dashboard
        </h2>
        <div className="relative w-full sm:w-80 transition-all duration-300">
          <label htmlFor="search-input" className="sr-only">
            Search
          </label>
          <input
            id="search-input"
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-white text-gray-700 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 placeholder-gray-700 hover:bg-slate-300"
          />
          <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
            <MagnifyingGlassIcon className="h-5 w-5" />
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <ArrowPathIcon className="h-10 w-10 text-blue-500 animate-spin" />
          <span className="ml-3 text-gray-400 text-lg">Loading...</span>
        </div>
      ) : error ? (
        <div className="flex justify-center items-center py-12 text-red-400">
          <ExclamationTriangleIcon className="h-6 w-6 mr-2" />
          <p className="text-lg">{error}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
            <h3 className="text-lg font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <ShieldCheckIcon className="h-5 w-5 text-blue-500" />
              Total scan
            </h3>
            <p className="text-3xl text-blue-400 transition-all duration-300">{filteredStats.policies}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
            <h3 className="text-lg font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              Security Alerts
            </h3>
            <p className="text-3xl text-red-400 transition-all duration-300">{filteredStats.alerts}</p>
          </div>
        </div>
      )}

      {/* GitHub Repositories Section */}
      <div className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300">
        <button
          className="flex items-center justify-between w-full text-lg font-semibold text-gray-300 mb-4"
          onClick={() => setShowGithubSection(!showGithubSection)}
        >
          <span className="flex items-center gap-2 text-slate-700">
            <svg className="h-5 w-5 text-blue-400 transition-transform duration-300 hover:scale-110" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.12-1.47-1.12-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.29 1.08 2.85.82.09-.64.35-1.08.63-1.33-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02A9.56 9.56 0 0 1 12 6.8c.85 0 1.71.11 2.52.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.94.36.31.66.94.66 1.9v2.81c0 .27.16.59.66.5A10 10 0 0 0 22 12 10 10 0 0 0 12 2z" />
            </svg>
            Github Repositories
          </span>
          {showGithubSection ? (
            <ChevronUpIcon className="h-5 w-5 text-gray-400 transition-transform duration-200" />
          ) : (
            <ChevronDownIcon className="h-5 w-5 text-gray-400 transition-transform duration-200" />
          )}
        </button>

        {showGithubSection && (
          <>
            {isGithubLinked === null ? (
              <div className="flex justify-center items-center py-4">
                <ArrowPathIcon className="h-6 w-6 text-blue-500 animate-spin" />
                <span className="ml-2 text-gray-400">Github account Verification...</span>
              </div>
            ) : isGithubLinked ? (
              reposLoading ? (
                <div className="flex justify-center items-center py-4">
                  <ArrowPathIcon className="h-6 w-6 text-blue-500 animate-spin" />
                  <span className="ml-2 text-gray-400">Loading Repos...</span>
                </div>
              ) : reposError ? (
                <div className="flex justify-center items-center py-4 text-red-400">
                  <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
                  <p>{reposError}</p>
                </div>
              ) : sortedRepos.length > 0 ? (
                <div>
                  <ul className="space-y-2 max-h-96 overflow-y-auto">
                    {sortedRepos.map((repo) => (
                      <li
                        key={repo.full_name}
                        className={`flex items-center justify-between p-2 rounded-lg transition-all duration-200 ${
                          repo.is_selected ? "bg-blue-900/50" : "hover:bg-gray-700/50"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={repo.is_selected}
                            onChange={() => toggleRepoSelection(repo.full_name)}
                            className="h-4 w-4 text-blue-500 rounded focus:ring-blue-500"
                          />
                          <a
                            href={repo.html_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-slate-700 hover:text-slate-200 transition-colors duration-200"
                          >
                            {repo.full_name}
                          </a>
                        </div>
                        {repo.description && (
                          <p className="text-sm text-gray-500 max-w-xs truncate">{repo.description}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                  <div className="mt-4 flex gap-3">
                    <button
                      onClick={handleSaveRepos}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-all duration-200 transform hover:scale-105"
                    >
                      Save Repos
                    </button>
                    <Link
                      to="/configs"
                      className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-all duration-200 transform hover:scale-105"
                    >
                      Get Configuration files
                    </Link>
                    <button
                      onClick={() => {
                        setRepos([]);
                        setReposLoading(true);
                        fetch("http://127.0.0.1:5000/github/repos", {
                          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
                        })
                          .then((res) => res.json())
                          .then((data) => {
                            setRepos(data);
                            setSelectedRepos(data.filter(repo => repo.is_selected).map(repo => repo.full_name));
                            setReposLoading(false);
                            toast.success("Repos search Refreshed  ", {
                              position: "top-right",
                              autoClose: 3000,
                              theme: "light",
                            });
                          })
                          .catch(() => {
                            setReposError("Rechargement Error");
                            setReposLoading(false);
                          });
                      }}
                      className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-all duration-200 transform hover:scale-105"
                    >
                      Refresh
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-slate-700">Repos Not Found !</p>
              )
            ) : (
              <div className="mt-6   pt-4">
                <h4 className="text-md font-semibold text-gray-600 mb-2">Use your token for personnel access (PAT)
                </h4>
                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="text"
                    value={pat}
                    onChange={(e) => setPat(e.target.value)}
                    placeholder="Entrez votre jeton GitHub"
                    className="w-full p-2 bg-gray-200  hover:bg-gray-300  text-gray-700 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-200 placeholder-slate-500"
                  />
                  <button
                    onClick={handlePatPreview}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-all duration-200 transform hover:scale-105"
                  >
                    Validate
                  </button>
                </div>
                {availableRepos.length > 0 && (
                  <div className="mt-4">
                    <h5 className="text-sm font-semibold text-gray-500 mb-2">Select the repos :</h5>
                    <ul className="max-h-40 overflow-y-auto border border-gray-700 rounded-lg p-2">
                      {availableRepos.map((repo) => (
                        <li
                          key={repo.full_name}
                          className="flex items-center gap-2 text-gray-500 p-1 hover:bg-gray-700/50 hover:text-slate-300 rounded transition-all duration-200"
                        >
                          <input
                            type="checkbox"
                            checked={selectedRepos.includes(repo.full_name)}
                            onChange={() => toggleRepoSelection(repo.full_name)}
                            className="h-4 w-4 text-blue-500 rounded focus:ring-blue-500"
                          />
                          <span>{repo.full_name}</span>
                        </li>
                      ))}
                    </ul>
                    <button
                      onClick={handlePatSubmit}
                      className="mt-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-all duration-200 transform hover:scale-105"
                    >
                      Add the selected repos
                    </button>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
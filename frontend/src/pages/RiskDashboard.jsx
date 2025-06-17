import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { ChartBarIcon, ArrowPathIcon, ExclamationCircleIcon } from "@heroicons/react/24/outline";

// Ensure Chart.js is properly imported
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const RiskDashboard = () => {
  const [risks, setRisks] = useState([]);
  const [details, setDetails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchRisks = async () => {
    setLoading(true);
    setError("");
    try {
      const user = JSON.parse(localStorage.getItem("user") || "{}");
      const userId = user.id;
      if (!userId) throw new Error("Utilisateur non connecté");

      const response = await fetch("http://127.0.0.1:5000/risks", {
        method: "GET",
        headers: {
          "X-User-ID": userId,
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      const data = await response.json();
      console.log("📊 Données reçues :", data);

      if (!response.ok) throw new Error(data.error || "Erreur serveur");
      if (!data.risks || !Array.isArray(data.risks)) {
        throw new Error("Format inattendu des données");
      }

      setRisks(data.risks);
      setDetails(data.details || []);
    } catch (error) {
      console.error("❌ Erreur lors de la récupération des Risks :", error);
      setError("Impossible to receive data : " + error.message);
      toast.error("Erreur lors du chargement des Risks !", {
        position: "top-right",
        autoClose: 3000,
        theme: "light",
      });
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchRisks();
  }, []);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchRisks();
  };

  // Debug chart data
  console.log("📈 Risks pour le graphique :", risks);

  const chartData = {
    labels: risks.map((risk) => risk.name) || ["Any risque"],
    datasets: [
      {
        label: "Risk Level ",
        data: risks.map((risk) => risk.level) || [0],
        backgroundColor: risks.length
          ? [
              "rgba(239, 68, 68, 0.5)", // Red for Critical
              "rgba(246, 173, 85, 0.5)", // Orange for High
              "rgba(74, 222, 128, 0.5)", // Green for Low
            ]
          : ["rgba(100, 100, 100, 0.5)"], // Gray for no data
        borderColor: risks.length
          ? [
              "rgba(239, 68, 68, 1)",
              "rgba(246, 173, 85, 1)",
              "rgba(74, 222, 128, 1)",
            ]
          : ["rgba(100, 100, 100, 1)"],
        borderWidth: 1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: "Risks per severity level",
        color: "#333a4c",
        font: { size: 16 },
      },
      tooltip: {
        backgroundColor: "#1f2937",
        titleColor: "#f3f4f6",
        bodyColor: "#f3f4f6",
      },
    },
    scales: {
      x: {
        ticks: { color: "#2b2b2b" },
        grid: { color: "#6c6a6a" },
      },
      y: {
        ticks: { color: "#2b2b2b" },
        grid: { color: "#6c6a6a" },
        beginAtZero: true,
        title: {
          display: true,
          text: "Risk score",
          color: "#333a4c",
        },
        suggestedMax: Math.max(...risks.map((r) => r.level), 10) + 10,
      },
    },
  };

  return (
    <div className="min-h-screen items-center justify-center flex flex-col p-4">
      <div className="bg-white  p-8 rounded-lg shadow-lg w-full max-w-6xl">
        <div className="flex justify-between items-center mb-6 ">
          <h2 className="text-2xl font-bold text-gray-500 flex items-center gap-2">
            <ChartBarIcon className="h-7 w-7 text-blue-400" />
             Risks Dashboard
          </h2>
          <button
            onClick={handleRefresh}
            disabled={loading || isRefreshing}
            className={`bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors duration-200 flex items-center gap-2 ${
              loading || isRefreshing ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            {isRefreshing ? (
              <>
                <ArrowPathIcon className="h-5 w-5 animate-spin" />
                Refreshing ...
              </>
            ) : (
              <>
                <ArrowPathIcon className="h-5 w-5" />
                Refresh
              </>
            )}
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-10">
            <ArrowPathIcon className="h-10 w-10 text-blue-500 animate-spin" />
            <span className="ml-3 text-gray-400">Chargement...</span>
          </div>
        ) : error ? (
          <div className="flex justify-center items-center py-4 text-red-400">
            <ExclamationCircleIcon className="h-6 w-6 mr-2" />
            <p>{error}</p>
          </div>
        ) : (
          <>
            <div className="bg-gray-300 p-4 rounded-lg mb-6 h-96">
              <label htmlFor="risk-chart" className="text-gray-500 text-sm mb-2 block">
                Risk Graphique Representation :
              </label>
              <div className="h-80">
                <Bar id="risk-chart" data={chartData} options={chartOptions} />
              </div>
            </div>
            <div className="bg-gray-300 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-500 mb-4">vulnerability Details</h3>
              {details.length === 0 ? (
                <p className="text-gray-400">No vulnerability found </p>
              ) : (
                <>
                  {/* Table for larger screens */}
                  <div className="hidden md:block overflow-x-auto max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800 ">
                    <table className="w-full text-left text-gray-900">
                      <thead className="sticky top-0 bg-gray-600">
                        <tr className="border-b border-gray-600 text-slate-200">
                          <th className="py-3 px-4 text-sm font-medium ">Severity</th>
                          <th className="py-3 px-4 text-sm font-medium">Problem</th>
                          <th className="py-3 px-4 text-sm font-medium">Suggestion</th>
                        </tr>
                      </thead>
                      <tbody>
                        {details.map((detail, index) => (
                          <tr
                            key={index}
                            className="border-b border-gray-400 hover:bg-gray-500 hover:text-white transition-colors"
                          >
                            <td
                              className={`py-3 px-4 text-sm ${
                                detail.severity === "ERROR"
                                  ? "text-red-400"
                                  : detail.severity === "WARNING"
                                  ? "text-yellow-400"
                                  : "text-green-400"
                              }`}
                            >
                              {detail.severity}
                            </td>
                            <td className="py-3 px-4 text-sm">{detail.message}</td>
                            <td className="py-3 px-4 text-sm">{detail.suggestion}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {/* Card layout for smaller screens */}
                  <div className="md:hidden space-y-4 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
                    {details.map((detail, index) => (
                      <div
                        key={index}
                        className="bg-gray-800 p-4 rounded-lg shadow-md hover:bg-gray-600 transition-colors"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span
                            className={`text-sm font-semibold ${
                              detail.severity === "ERROR"
                                ? "text-red-400"
                                : detail.severity === "WARNING"
                                ? "text-yellow-400"
                                : "text-green-400"
                            }`}
                          >
                            {detail.severity}
                          </span>
                        </div>
                        <p className="text-gray-300 text-sm">
                          <span className="font-medium">Problème :</span> {detail.message}
                        </p>
                        <p className="text-gray-300 text-sm mt-2">
                          <span className="font-medium">Suggestion :</span> {detail.suggestion}
                        </p>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default RiskDashboard;
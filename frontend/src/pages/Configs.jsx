import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { DocumentTextIcon, ArrowPathIcon, DocumentDuplicateIcon } from "@heroicons/react/24/outline";
import { Link, useNavigate } from "react-router-dom";
import LoadingLogo from "../components/LoadingLogo";
import loadingVideo from "../assets/loading.mp4";

const Configs = () => {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchConfigs = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await fetch("http://127.0.0.1:5000/github/repo-configs", {
          method: "GET",
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || "Échec récupération configurations");
        }

        const data = await response.json();
        setConfigs(data);
        toast.success("Configurations charged!", {
          toastId: 'configurations-charged',
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      } catch (err) {
        setError("Impossible to charge the configuration files");
        toast.error(err.message, {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      } finally {
        // setLoading(false);
      }
    };

    fetchConfigs();
  }, []);

  const copyToClipboard = (content) => {
    // navigator.clipboard.writeText(content).then(() => {
    //   toast.success("Content copied", { position: "top-right", autoClose: 2000, theme: "light" });
    // });
  };

  const checkSingleFileCompliance = (config) => {
    const selectedFile = {
      id: config.id,
      file_name: config.file_name,
      content: config.content,
      framework: inferFramework(config.file_name),
    };

    navigate("/compliance", { state: { selectedFiles: [selectedFile] } });
  };

  const inferFramework = (fileName) => {
    const lowerName = fileName.toLowerCase();
    if (lowerName === "dockerfile") return "dockerfile";
    if (lowerName.endsWith(".yml") || lowerName.endsWith(".yaml")) return "kubernetes";
    if (lowerName.endsWith(".tf")) return "terraform";
    return "unknown";
  };

  return (
    <div className="h-full flex flex-col">
      <h2 className="text-3xl font-bold text-gray-800 mb-8 flex items-center gap-2">
        <DocumentTextIcon className="h-8 w-8 text-blue-400" />
        Repos Configurations
      </h2>

      {loading ? (
        <div className="flex-1 flex items-center justify-center bg-white min-h-[500px]">
          <div className="flex flex-col items-center justify-center space-y-6">
            <video 
              src={loadingVideo} 
              autoPlay 
              loop 
              muted 
              playsInline 
              className="w-64 h-64 object-cover rounded-2xl"
              style={{ 
                backgroundColor: 'transparent',
                border: 'none',
                outline: 'none',
                filter: 'brightness(1.1) contrast(1.05)'
              }}
            />
            <div className="text-center space-y-2">
              <p className="text-xl font-semibold text-gray-700">Loading configurations...</p>
              <p className="text-sm text-gray-500">Please wait while we fetch your repository data</p>
            </div>
          </div>
        </div>
      ) : configs.length > 0 ? (
        <div className="bg-sky-100 p-6 rounded-lg shadow-md w-full max-w-4xl mx-auto">
          <ul className="space-y-4">
            {configs.map((config) => (
              <li key={config.id} className="border-b border-gray-700 pb-4">
                <div className="flex justify-between items-center flex-wrap gap-4">
                  <div className="flex items-center gap-2 max-w-[70%]">
                    <div className="overflow-hidden">
                      <a
                        href={config.repo_html_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-800 hover:text-blue-400 transition-colors truncate block"
                      >
                        {config.repo_full_name}
                      </a>
                      <p className="text-gray-500 truncate">{config.file_path}</p>
                    </div>
                  </div>
                  <div className="flex gap-2 min-w-fit">
                    <button
                      onClick={() => copyToClipboard(config.content)}
                      className="bg-gray-600 text-white px-3 py-1 rounded-lg hover:bg-gray-700"
                    >
                      <DocumentDuplicateIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => checkSingleFileCompliance(config)}
                      className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors whitespace-nowrap"
                    >
                        Conformity check
                    </button>
                    <Link
                      to="/generate-policy"
                      state={{ selectedFiles: [{ id: config.id, file_name: config.file_name, content: config.content, framework: inferFramework(config.file_name) }] }}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap"
                    >
                      Correct
                    </Link>
                  </div>
                </div>
                <pre className="mt-2 p-4 bg-slate-600 text-white rounded-lg max-h-64 overflow-auto font-mono text-sm">
                  {config.content}
                </pre>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center bg-white min-h-[400px]">
          <div className="text-center space-y-4">
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <DocumentTextIcon className="h-12 w-12 text-gray-400" />
            </div>
            <p className="text-xl font-medium text-gray-600">No configurations found</p>
            <p className="text-sm text-gray-400 max-w-md">
              Select repositories from the dashboard to view their configuration files here.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Configs;
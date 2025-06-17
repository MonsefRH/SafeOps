import React from "react";
import { Link } from "react-router-dom";
import {
  HomeIcon,
  ShieldCheckIcon,
  ShieldExclamationIcon,
  CheckCircleIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  ArrowRightStartOnRectangleIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  DocumentTextIcon,
} from "@heroicons/react/24/outline";

const Sidebar = ({ handleLogout, isCollapsed, toggleSidebar }) => {
  return (
    <div
      className={`bg-blue-600 text-gray-100 flex flex-col h-screen transition-all duration-300 ${
        isCollapsed ? "w-16" : "w-64"
      }`}
    >
      {/* En-tête avec le titre et le bouton toggle */}
      <div className="p-5 flex items-center justify-between">
        <h1
          className={`text-xl font-bold flex items-center gap-2 ${
            isCollapsed ? "hidden" : "text-center"
          }`}
        >
          <ShieldCheckIcon className="h-6 w-6 text-gray-300" />
          {!isCollapsed && "SafeOps"}
        </h1>
        <button
          onClick={toggleSidebar}
          className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200"
          aria-label={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isCollapsed ? (
            <ChevronRightIcon className="h-5 w-5" />
          ) : (
            <ChevronLeftIcon className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="space-y-2 flex-1">
        <Link
          to="/"
          className={`flex items-center p-2 rounded hover:bg-blue-700 transition-colors duration-200 ${
            isCollapsed ? "justify-center" : ""
          }`}
          aria-label="Dashboard"
        >
          <HomeIcon className="h-5 w-5 text-gray-200" />
          {!isCollapsed && <span className="ml-3">Dashboard</span>}
        </Link>
        <Link
          to="/configs"
          className={`flex items-center p-2 rounded hover:bg-blue-700 transition-colors duration-200 ${
            isCollapsed ? "justify-center" : ""
          }`}
          aria-label="Configurations"
        >
          <DocumentTextIcon className="h-5 w-5 text-gray-300" />
          {!isCollapsed && <span className="ml-3">Configuration Files </span>}
        </Link>
        <Link
          to="/generate-policy"
          className={`flex items-center p-2 rounded hover:bg-blue-700 transition-colors duration-200 ${
            isCollapsed ? "justify-center" : ""
          }`}
          aria-label="Policy Generator"
        >
          <ShieldCheckIcon className="h-5 w-5 text-gray-300" />
          {!isCollapsed && <span className="ml-3">Policy Generator</span>}
        </Link>
        <Link
          to="/scan"
          className={`flex items-center p-2 rounded hover:bg-blue-700 transition-colors duration-200 ${
            isCollapsed ? "justify-center" : ""
          }`}
          aria-label="Vulnerability Analyse"
        >
          <ShieldExclamationIcon className="h-5 w-5 text-gray-300" />
          {!isCollapsed && <span className="ml-3">Vulnerability Analyser</span>}
        </Link>
        <Link
          to="/compliance"
          className={`flex items-center p-2 rounded hover:bg-blue-700 transition-colors duration-200 ${
            isCollapsed ? "justify-center" : ""
          }`}
          aria-label="Validation & Conformity"
        >
          <CheckCircleIcon className="h-5 w-5 text-gray-300" />
          {!isCollapsed && <span className="ml-3">Validation & Conformity</span>}
        </Link>
        <Link
          to="/risks"
          className={`flex items-center p-2 rounded hover:bg-blue-700 transition-colors duration-200 ${
            isCollapsed ? "justify-center" : ""
          }`}
          aria-label="Risque Monitoring"
        >
          <ChartBarIcon className="h-5 w-5 text-gray-300" />
          {!isCollapsed && <span className="ml-3">Risque Monitoring</span>}
        </Link>
        <Link
          to="/pricing"
          className={`flex items-center p-2 rounded hover:bg-blue-700 transition-colors duration-200 ${
            isCollapsed ? "justify-center" : ""
          }`}
          aria-label="Tarification"
        >
          <CurrencyDollarIcon className="h-5 w-5 text-gray-300" />
          {!isCollapsed && <span className="ml-3">Tarification</span>}
        </Link>
      </nav>

      {/* Bouton Déconnexion */}
      <button
        onClick={handleLogout}
        className={`flex items-center p-2 w-full rounded hover:bg-red-600 transition-colors duration-200 text-left mt-2 ${
          isCollapsed ? "justify-center" : ""
        }`}
        aria-label="Deconnect"
      >
        <ArrowRightStartOnRectangleIcon className="h-5 w-5 text-gray-300" />
        {!isCollapsed && <span className="ml-3">Deconnect</span>}
      </button>
    </div>
  );
};

export default Sidebar;
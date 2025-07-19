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
  UserGroupIcon,
} from "@heroicons/react/24/outline";

const Sidebar = ({ handleLogout, isCollapsed, toggleSidebar, user }) => {
  // Define navigation items based on role
  const navItems = user?.role === "admin"
    ? [
        {
          to: "/admin-dashboard",
          label: "Admin Dashboard",
          icon: <UserGroupIcon className="h-5 w-5 text-gray-200" />,
        },
        // Add more admin-specific routes here if needed
      ]
    : [
        { to: "/", label: "Dashboard", icon: <HomeIcon className="h-5 w-5 text-gray-200" /> },
        { to: "/configs", label: "Configuration Files", icon: <DocumentTextIcon className="h-5 w-5 text-gray-300" /> },
        { to: "/generate-policy", label: "Policy Generator", icon: <ShieldCheckIcon className="h-5 w-5 text-gray-300" /> },
        { to: "/scan", label: "Vulnerability Scanner", icon: <ShieldExclamationIcon className="h-5 w-5 text-gray-300" /> },
        { to: "/compliance", label: "Compliance Checker", icon: <CheckCircleIcon className="h-5 w-5 text-gray-300" /> },
        { to: "/risks", label: "Risk Monitoring", icon: <ChartBarIcon className="h-5 w-5 text-gray-300" /> },
        { to: "/all-in-one", label: "All in One", icon: <DocumentTextIcon className="h-5 w-5 text-gray-300" /> },
        { to: "/pricing", label: "Pricing", icon: <CurrencyDollarIcon className="h-5 w-5 text-gray-300" /> },
      ];

  // Use same theme for both admins and users
  const sidebarBg = "bg-blue-600";

  return (
    <div
      className={`${sidebarBg} text-gray-100 flex flex-col h-screen transition-all duration-300 ${
        isCollapsed ? "w-16" : "w-64"
      }`}
    >
      {/* Header with title and toggle button */}
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
          className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200"
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
        {navItems.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={`flex items-center p-2 rounded hover:bg-blue-700 transition-colors duration-200 ${
              isCollapsed ? "justify-center" : ""
            }`}
            aria-label={item.label}
          >
            {item.icon}
            {!isCollapsed && <span className="ml-3">{item.label}</span>}
          </Link>
        ))}
      </nav>

      {/* Logout Button */}
      <button
        onClick={handleLogout}
        className={`flex items-center p-2 w-full rounded hover:bg-red-600 transition-colors duration-200 text-left mt-2 ${
          isCollapsed ? "justify-center" : ""
        }`}
        aria-label="Logout"
      >
        <ArrowRightStartOnRectangleIcon className="h-5 w-5 text-gray-300" />
        {!isCollapsed && <span className="ml-3">Logout</span>}
      </button>
    </div>
  );
};

export default Sidebar;
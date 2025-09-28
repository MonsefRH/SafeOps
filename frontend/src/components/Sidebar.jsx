import React from "react";
import { Link, useLocation } from "react-router-dom";
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
import './Sidebar.css';

const Sidebar = ({ handleLogout, isCollapsed, toggleSidebar, user }) => {
  const location = useLocation();

  // Define navigation items based on role
  const navItems = user?.role === "admin"
    ? [
        {
          to: "/admin-dashboard",
          label: "Admin Dashboard",
          icon: <UserGroupIcon className="sidebar__nav-icon" />,
        },
      ]
    : [
        { to: "/", label: "Dashboard", icon: <HomeIcon className="sidebar__nav-icon" /> },
        { to: "/configs", label: "Configuration Files", icon: <DocumentTextIcon className="sidebar__nav-icon" /> },
        { to: "/generate-policy", label: "Policy Generator", icon: <ShieldCheckIcon className="sidebar__nav-icon" /> },
        { to: "/scan", label: "Vulnerability Scanner", icon: <ShieldExclamationIcon className="sidebar__nav-icon" /> },
        { to: "/compliance", label: "Compliance Checker", icon: <CheckCircleIcon className="sidebar__nav-icon" /> },
        { to: "/risks", label: "Risk Monitoring", icon: <ChartBarIcon className="sidebar__nav-icon" /> },
        { to: "/all-in-one", label: "All in One", icon: <DocumentTextIcon className="sidebar__nav-icon" /> },
        { to: "/pricing", label: "Pricing", icon: <CurrencyDollarIcon className="sidebar__nav-icon" /> },
      ];

  return (
    <div className={`sidebar ${isCollapsed ? 'sidebar--collapsed' : 'sidebar--expanded'}`}>
      {/* Header with title and toggle button */}
      <div className="sidebar__header">
        {!isCollapsed && (
          <h1 className="sidebar__title">
            <ShieldCheckIcon className="sidebar__title-icon" />
            Security Hub
          </h1>
        )}
        <button
          onClick={toggleSidebar}
          className="sidebar__toggle"
          aria-label={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isCollapsed ? (
            <ChevronRightIcon className="sidebar__toggle-icon" />
          ) : (
            <ChevronLeftIcon className="sidebar__toggle-icon" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar__nav">
        {navItems.map((item) => {
          const isActive = location.pathname === item.to;
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`sidebar__nav-item ${
                isCollapsed ? 'sidebar__nav-item--collapsed' : ''
              } ${
                isActive ? 'sidebar__nav-item--active' : ''
              }`}
              data-tooltip={item.label}
              aria-label={item.label}
            >
              {item.icon}
              {!isCollapsed && <span className="sidebar__nav-label">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Logout Button */}
      <button
        onClick={handleLogout}
        className={`sidebar__logout ${
          isCollapsed ? 'sidebar__logout--collapsed' : ''
        }`}
        aria-label="Logout"
      >
        <ArrowRightStartOnRectangleIcon className="sidebar__logout-icon" />
        {!isCollapsed && <span className="sidebar__logout-label">Logout</span>}
      </button>
    </div>
  );
};

export default Sidebar;
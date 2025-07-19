import React from "react";
import { UserIcon, ArrowRightStartOnRectangleIcon } from "@heroicons/react/24/outline";

const Header = ({ isAuthenticated, user, handleLogout, isAdmin }) => {
  return isAuthenticated ? (
    <header
      className={`flex items-center justify-between px-6 py-4 shadow-lg ${
        isAdmin ? "bg-purple-600" : "bg-blue-500"
      } transition-colors duration-300`}
    >
      <div className="flex items-center gap-3">
        <h2 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-300">
          SafeOps
        </h2>
        {isAdmin && (
          <span className="text-sm font-medium text-gray-200 bg-purple-700/50 px-2 py-1 rounded-md">
            Admin
          </span>
        )}
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <UserIcon className="h-6 w-6 text-gray-200" />
          <span className="text-gray-200 text-base font-semibold">
            {user?.name ? user.name : "User"}
          </span>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors duration-200"
          aria-label="Logout"
        >
          <ArrowRightStartOnRectangleIcon className="h-5 w-5" />
          <span className="text-sm font-medium">Logout</span>
        </button>
      </div>
    </header>
  ) : null;
};

export default Header;

import React from "react";
import { UserIcon, ArrowRightStartOnRectangleIcon } from "@heroicons/react/24/outline";

const Header = ({ isAuthenticated, user, handleLogout }) => {
  console.log("User in Header:", user); // Debugging

  return isAuthenticated ? (
    <header className="flex items-center justify-between bg-blue-500 p-4 shadow-md ">
      <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
      </h2>
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <UserIcon className="h-5 w-5 text-gray-300" />
          <span className="text-gray-300 font-semibold">
            {user?.name ? user.name : "Utilisateur"}
          </span>
        </div>
        <button
          onClick={handleLogout}
          className="p-2 rounded-full bg-red-600 text-white hover:bg-red-700 transition-colors duration-200 flex items-center gap-1"
          aria-label="Se déconnecter"
        >
          <ArrowRightStartOnRectangleIcon className="h-5 w-5" />
        </button>
      </div>
    </header>
  ) : null;
};

export default Header;
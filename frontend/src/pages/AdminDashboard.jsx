import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import {
  UserGroupIcon,
  ShieldCheckIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
const BASE_URL = (import.meta.env?.VITE_SIP || "http://localhost").replace(/\/+$/, "");
const API = `${BASE_URL}/api`;
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
    const animationId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(animationId); // Cleanup animation
  }, [end, duration]);

  return count;
};

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Memoize user object to prevent unnecessary useEffect triggers
  const user = useMemo(() => {
    const storedUser = localStorage.getItem("user");
    return storedUser ? JSON.parse(storedUser) : null;
  }, []);

  // Fetch admin stats (total users, total scans, and user data)
  useEffect(() => {
    const abortController = new AbortController();

    // Skip fetching if user is not an admin
    if (!user || user.role !== "admin") {
      setLoading(false);
      navigate("/dashboard");
      return;
    }

    // Skip if stats are already loaded
    if (stats) {
      setLoading(false);
      return;
    }

    const fetchAdminStats = async () => {
      try {
        const response = await fetch(`${API}:5000/admin-stats`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new Error("Failed to fetch admin stats");
        }

        const data = await response.json();
        setStats(data);
      } catch (err) {
        if (err.name === "AbortError") return;
        setError("Unable to load admin dashboard data");
        console.error("Admin stats error:", err);
        toast.error("Failed to load admin stats", {
          position: "top-right",
          autoClose: 3000,
          theme: "light",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchAdminStats();

    return () => abortController.abort();
  }, [user, stats, navigate]);

  // Animated stats
  const totalUsersCount = useCountUp(stats ? stats.total_users : 0, 1500);
  const totalScansCount = useCountUp(stats ? stats.total_scans : 0, 1500);

  const filteredStats = stats
    ? {
        totalUsers: totalUsersCount,
        totalScans: totalScansCount,
        users: stats.users,
      }
    : null;

  // Render only if user is admin
  if (!user || user.role !== "admin") {
    return null; // Navigation handled in useEffect
  }

  return (
    <div className="h-fit flex flex-col p-8 min-h-screen ">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-purple-800 flex items-center gap-3">
          <UserGroupIcon className="h-8 w-8 text-purple-500 animate-pulse" />
          Admin Dashboard
        </h2>
      </div>
      {/* Stats Grid */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <ArrowPathIcon className="h-12 w-12 text-purple-500 animate-spin" />
          <span className="ml-3 text-gray-500 text-xl">Loading...</span>
        </div>
      ) : error ? (
        <div className="flex justify-center items-center py-12 text-red-500">
          <ExclamationTriangleIcon className="h-8 w-8 mr-2" />
          <p className="text-xl">{error}</p>
        </div>
      ) : filteredStats ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          <div className="bg-gradient-to-br from-white to-gray-50 p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2">
            <div className="flex items-center gap-4">
              <UserGroupIcon className="h-10 w-10 text-purple-500 animate-pulse" />
              <div>
                <h3 className="text-xl font-semibold text-gray-800">Total Users</h3>
                <p className="text-4xl font-bold text-purple-600 mt-2">{filteredStats.totalUsers}</p>
              </div>
            </div>
          </div>
          <div className="bg-gradient-to-br from-white to-gray-50 p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2">
            <div className="flex items-center gap-4">
              <ShieldCheckIcon className="h-10 w-10 text-purple-500 animate-pulse" />
              <div>
                <h3 className="text-xl font-semibold text-gray-800">Total Scans</h3>
                <p className="text-4xl font-bold text-purple-600 mt-2">{filteredStats.totalScans}</p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex justify-center items-center py-12 text-gray-500">
          <p className="text-xl">No stats available</p>
        </div>
      )}
      {/* User Management Section */}
      <div className="bg-white p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300">
        <h3 className="text-xl font-semibold text-gray-800 mb-6 flex items-center gap-3">
          <UserGroupIcon className="h-6 w-6 text-purple-500" />
          User Management
        </h3>
        {filteredStats && filteredStats.users && filteredStats.users.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-200">
                  <th className="p-4 text-gray-700 font-semibold">Name</th>
                  <th className="p-4 text-gray-700 font-semibold">Email</th>
                  <th className="p-4 text-gray-700 font-semibold">Role</th>
                  <th className="p-4 text-gray-700 font-semibold">Created At</th>
                  <th className="p-4 text-gray-700 font-semibold">Scans</th>
                </tr>
              </thead>
              <tbody>
                {filteredStats.users.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-gray-200 hover:bg-gray-50 transition-colors duration-200"
                  >
                    <td className="p-4 text-gray-600">{user.name}</td>
                    <td className="p-4 text-gray-600">{user.email}</td>
                    <td className="p-4 text-gray-600 capitalize">{user.role}</td>
                    <td className="p-4 text-gray-600">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-4 text-gray-600">{user.scan_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-600 text-lg">No users found.</p>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
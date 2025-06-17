import React from "react";
import { FaExclamationTriangle } from "react-icons/fa";

const alerts = [
  { id: 1, message: "Fuite de secrets détectée", level: "Critique" },
  { id: 2, message: "IAM Policy trop permissive", level: "Moyen" },
];

const Alerts = () => {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Surveillance & Alertes</h2>
      <ul className="space-y-2">
        {alerts.map((alert) => (
          <li key={alert.id} className="flex items-center bg-red-100 p-3 rounded-lg">
            <FaExclamationTriangle className="text-red-500 mr-2" />
            <span>{alert.message} ({alert.level})</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Alerts;

import React from "react";
import { CurrencyEuroIcon, CheckCircleIcon, ChartBarIcon, ArrowRightIcon } from "@heroicons/react/24/outline";

const Pricing = () => {
  return (
    <div className="h-full flex items-center justify-center flex-col">
      <div className="w-full max-w-4xl">
        <h1 className="text-3xl font-bold text-slate-700 mb-8 text-center flex items-center justify-center gap-2">
          <CurrencyEuroIcon className="h-8 w-8 text-blue-400" />
          Our Pricing
        </h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300">
            <h3 className="text-xl font-semibold text-gray-500 mb-4">Starter</h3>
            <p className="text-2xl text-blue-400 mb-2 flex items-center gap-2">
              <CurrencyEuroIcon className="h-6 w-6" />
              19€/month
            </p>
            <p className="text-gray-400 flex items-center gap-2">
              <CheckCircleIcon className="h-5 w-5 text-green-400" />
              Basic analysis
            </p>
            <p className="text-gray-400 flex items-center gap-2">
              <CheckCircleIcon className="h-5 w-5 text-green-400" />
              1 scan/month
            </p>
            <button className="mt-4 w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors duration-200 flex items-center justify-center gap-2">
              Select
              <ArrowRightIcon className="h-5 w-5" />
            </button>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300">
            <h3 className="text-xl font-semibold text-gray-500 mb-4">Pro</h3>
            <p className="text-2xl text-blue-400 mb-2 flex items-center gap-2">
              <CurrencyEuroIcon className="h-6 w-6" />
              49€/month
            </p>
            <p className="text-gray-400 flex items-center gap-2">
              <CheckCircleIcon className="h-5 w-5 text-green-400" />
              Scans illimited
            </p>
            <p className="text-gray-400 flex items-center gap-2">
              <ChartBarIcon className="h-5 w-5 text-green-400" />
              Advanced Dashboard
            </p>
            <button className="mt-4 w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors duration-200 flex items-center justify-center gap-2">
              Select
              <ArrowRightIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Pricing;
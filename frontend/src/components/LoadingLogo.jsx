// src/components/LoadingLogo.jsx
import React from "react";
import loadingGif from "../assets/loading.gif";

const LoadingLogo = ({ size = 150 }) => {
  return (
    <div className="flex flex-col justify-center items-center h-full">
      <img
        src={loadingGif}
        alt="Loading..."
        style={{ width: size, height: size }}
        className="animate-pulse" // optional: adds a pulsing effect
      />
      <span className="mt-4 text-gray-600 text-lg">Loading Configurations ...</span>
    </div>
  );
};

export default LoadingLogo;

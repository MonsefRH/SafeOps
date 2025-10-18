import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { useLocation } from 'react-router-dom';

export const useScaner = () => {
  const [sourceType, setSourceType] = useState(null);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // NEW: lifted code state
  const [code, setCode] = useState("");
    const [url, setUrl] = useState(""); // <-- define state


  const location = useLocation();
  const selectedFiles = location.state?.selectedFiles || [];
  
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const userId = user.id;

  useEffect(() => {
    document.body.style.overflow = isLoading ? 'hidden' : 'auto';
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [isLoading]);

  const resetScanner = () => {
    setSourceType(null);
    setResult(null);
    setIsLoading(false);
    // Keep code if you want persistence across reset,
    // OR uncomment next line to clear when going back:
    // setCode("");
    
    const scannerContent = document.querySelector('.scanner-content');
    if (scannerContent) {
      scannerContent.classList.add('opacity-0');
      setTimeout(() => {
        scannerContent.classList.remove('opacity-0');
      }, 100);
    }
  };

  const clearResult = () => setResult(null);
  const openHistory = () => setIsHistoryOpen(true);
  const closeHistory = () => setIsHistoryOpen(false);

  const handleCopy = async (content) => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success('Code copied successfully!', {
        position: 'top-right',
        autoClose: 2000,
        theme: 'light'
      });
    } catch (error) {
      toast.error('Error copying code!', {
        position: 'top-right',
        autoClose: 2000,
        theme: 'light'
      });
    }
  };

  const selectSourceType = (type) => setSourceType(type);

  return {
    sourceType,
    result,
    isLoading,
    isHistoryOpen,
    selectedFiles,
    userId,
    code, 
    url,
    setUrl,
    setIsLoading,      // NEW
    setCode,    // NEW
    setResult,
    resetScanner,
    clearResult,
    openHistory,
    closeHistory,
    handleCopy,
    selectSourceType,
  };
};

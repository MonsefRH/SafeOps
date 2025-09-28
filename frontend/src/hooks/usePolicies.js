import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { useLocation } from 'react-router-dom';

export const usePolicies = () => {
  const [sourceType, setSourceType] = useState(null);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const location = useLocation();
  const selectedFiles = location.state?.selectedFiles || [];
  
  // Get user data
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const userId = user.id;

  // Handle body scroll when loading
  useEffect(() => {
    document.body.style.overflow = isLoading ? 'hidden' : 'auto';
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [isLoading]);

  const resetGenerator = () => {
    setSourceType(null);
    setResult(null);
    setIsLoading(false);
    
    // Add smooth transition effect
    const generatorContent = document.querySelector('.generator-content');
    if (generatorContent) {
      generatorContent.classList.add('opacity-0');
      setTimeout(() => {
        generatorContent.classList.remove('opacity-0');
      }, 100);
    }
  };

  const clearResult = () => {
    setResult(null);
  };

  const openHistory = () => {
    setIsHistoryOpen(true);
  };

  const closeHistory = () => {
    setIsHistoryOpen(false);
  };

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

  const selectSourceType = (type) => {
    setSourceType(type);
  };

  return {
    // State
    sourceType,
    result,
    isLoading,
    isHistoryOpen,
    selectedFiles,
    userId,
    
    // Actions
    setResult,
    setIsLoading,
    resetGenerator,
    clearResult,
    openHistory,
    closeHistory,
    handleCopy,
    selectSourceType,
  };
};
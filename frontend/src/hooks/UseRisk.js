import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

export const useRisks = () => {
  const [risks, setRisks] = useState([]);
  const [details, setDetails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchRisks = async () => {
    setLoading(true);
    setError('');
    
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const userId = user.id;
      
      if (!userId) {
        throw new Error('User not connected');
      }

      const response = await fetch('http://127.0.0.1:5000/risks', {
        method: 'GET',
        headers: {
          'X-User-ID': userId,
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Server error');
      }
      
      if (!data.risks || !Array.isArray(data.risks)) {
        throw new Error('Unexpected data format');
      }

      setRisks(data.risks);
      setDetails(data.details || []);
    } catch (error) {
      const errorMessage = `Unable to receive data: ${error.message}`;
      setError(errorMessage);
      toast.error('Error loading risks!', {
        position: 'top-right',
        autoClose: 3000,
        theme: 'light',
      });
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  const refreshRisks = () => {
    setIsRefreshing(true);
    fetchRisks();
  };

  useEffect(() => {
    fetchRisks();
  }, []);

  return {
    risks,
    details,
    loading,
    error,
    isRefreshing,
    refreshRisks,
  };
};
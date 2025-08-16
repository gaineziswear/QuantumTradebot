import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

export default function Test() {
  const [status, setStatus] = useState({
    backend: 'checking...',
    auth: 'checking...',
    error: null as string | null
  });

  const checkConnections = async () => {
    try {
      // Test backend connection
      const response = await fetch('/api/health');
      if (response.ok) {
        const data = await response.json();
        setStatus(prev => ({ 
          ...prev, 
          backend: `✅ Backend Connected (${data.backend || 'Unknown'})` 
        }));
      } else {
        setStatus(prev => ({ 
          ...prev, 
          backend: `❌ Backend Error: ${response.status}` 
        }));
      }
    } catch (error) {
      setStatus(prev => ({ 
        ...prev, 
        backend: `❌ Backend Offline: ${error}`,
        error: String(error)
      }));
    }

    // Test auth status
    try {
      const isAuth = apiClient.isAuthenticated();
      setStatus(prev => ({ 
        ...prev, 
        auth: isAuth ? '✅ Authenticated' : '❌ Not Authenticated' 
      }));
    } catch (error) {
      setStatus(prev => ({ 
        ...prev, 
        auth: `❌ Auth Error: ${error}` 
      }));
    }
  };

  useEffect(() => {
    checkConnections();
  }, []);

  const testLogin = async () => {
    try {
      const result = await apiClient.login({
        username: 'trader',
        password: 'crypto2024'
      });
      setStatus(prev => ({ 
        ...prev, 
        auth: result.success ? '✅ Login Success' : '❌ Login Failed' 
      }));
    } catch (error) {
      setStatus(prev => ({ 
        ...prev, 
        auth: `❌ Login Error: ${error}` 
      }));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl w-full">
        <h1 className="text-2xl font-bold mb-6 text-center">🔧 Frontend Diagnostics</h1>
        
        <div className="space-y-4">
          <div className="p-4 bg-gray-50 rounded">
            <h3 className="font-semibold mb-2">Backend Connection:</h3>
            <p className="text-sm">{status.backend}</p>
          </div>
          
          <div className="p-4 bg-gray-50 rounded">
            <h3 className="font-semibold mb-2">Authentication:</h3>
            <p className="text-sm">{status.auth}</p>
          </div>
          
          {status.error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded">
              <h3 className="font-semibold mb-2 text-red-800">Error Details:</h3>
              <p className="text-sm text-red-700">{status.error}</p>
            </div>
          )}
          
          <div className="space-y-2">
            <button 
              onClick={checkConnections}
              className="w-full bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              🔄 Refresh Status
            </button>
            
            <button 
              onClick={testLogin}
              className="w-full bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
            >
              🔑 Test Login
            </button>
          </div>
          
          <div className="text-center pt-4">
            <a 
              href="/login" 
              className="text-blue-500 hover:underline mr-4"
            >
              Go to Login
            </a>
            <a 
              href="/dashboard" 
              className="text-blue-500 hover:underline"
            >
              Go to Dashboard
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

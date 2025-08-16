import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "@/lib/api";

export default function Index() {
  const navigate = useNavigate();

  useEffect(() => {
    // Temporarily redirect directly to login to avoid auth loop
    navigate('/login', { replace: true });
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-white">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-gray-300 border-t-gray-900 rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-600">Loading AI Crypto Trading Bot...</p>
      </div>
    </div>
  );
}

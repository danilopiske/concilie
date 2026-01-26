/**
 * Cliente API base - Conecta Next.js ao FastAPI backend
 */
import axios, { AxiosInstance } from 'axios';

// API URL - Hardcoded to 8000 as requested for the split-port topology
// Frontend runs on 3000, Backend on 8000.
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
console.log('[DEBUG] API Client URL:', API_URL);

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes default timeout
});

// Interceptor para adicionar token (futuro)
apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para tratamento de erros
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirecionar para login (futuro)
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

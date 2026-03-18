/**
 * Cliente API base - Conecta Next.js ao FastAPI backend
 */
import axios, { AxiosInstance } from 'axios';

// API URL - Hardcoded to 8000 as requested for the split-port topology
// Frontend runs on 3000, Backend on 8000.
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 300000, // 5 minutes default timeout
  withCredentials: true, // envia cookie HttpOnly automaticamente
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

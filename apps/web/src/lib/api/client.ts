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

// Interceptor para adicionar o token de autorização
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Interceptor para tratamento de erros e captura de token
apiClient.interceptors.response.use(
  (response) => {
    // Se for a rota de login, salvar o token recebido no localStorage
    if (response.config.url?.includes('/login/access-token') && response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Remover token inválido
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

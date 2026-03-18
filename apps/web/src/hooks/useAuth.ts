import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api/client';

export interface User {
  id: number;
  usuario: string;
}

export function useAuth() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Cookie é gerenciado pelo browser; apenas restaura dados do usuário para exibição
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (usuario: string, senha: string) => {
    try {
      // Use URLSearchParams for OAuth2 form data
      const formData = new URLSearchParams();
      formData.append('username', usuario);
      formData.append('password', senha);

      const response = await apiClient.post('/login/access-token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      // Cookie HttpOnly é setado automaticamente pelo backend
      // Armazena apenas dados de exibição (sem token sensível)
      const userData = { id: 0, usuario };
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      
      router.push('/');
      return true;
    } catch (error) {
      console.error('Login failed', error);
      throw error;
    }
  };

  const logout = async () => {
    localStorage.removeItem('user');
    setUser(null);
    // Limpa o cookie via backend (ou expira localmente via max-age=0)
    try {
      await apiClient.post('/login/logout');
    } catch {
      // silencioso — mesmo sem endpoint de logout, o cookie expira naturalmente
    }
    router.push('/login');
  };

  return { user, login, logout, loading };
}

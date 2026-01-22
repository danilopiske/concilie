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
    // Check for token on mount
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token) {
      if (savedUser) {
        setUser(JSON.parse(savedUser));
      }
      // Optionally verify token validity here
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

      const { access_token } = response.data;
      
      localStorage.setItem('token', access_token);
      
      // Store minimal user info (or fetch full profile)
      const userData = { id: 0, usuario }; // ID is in token, but we assume 0 for now until we fetch /me
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      
      router.push('/');
      return true;
    } catch (error) {
      console.error('Login failed', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    router.push('/login');
  };

  return { user, login, logout, loading };
}

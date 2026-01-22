/**
 * Hook para obter informações do sistema
 */
'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';

interface DatabaseInfo {
  type: string;
  dialect: string;
  driver: string;
  connection: string;
}

interface HealthInfo {
  status: string;
  version: string;
  database: DatabaseInfo;
}

export function useSystemInfo() {
  const [info, setInfo] = useState<HealthInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        setLoading(true);
        const { data } = await apiClient.get<HealthInfo>('/health', {
          baseURL: 'http://localhost:8000',
        });
        setInfo(data);
        setError(null);
      } catch (err: any) {
        setError('Não foi possível conectar ao backend');
        console.error('Erro ao buscar info do sistema:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchInfo();
  }, []);

  return { info, loading, error };
}

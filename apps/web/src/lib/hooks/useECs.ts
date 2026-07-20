/**
 * Hook para gerenciar ECs (Estabelecimentos Comerciais)
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';

type ApiErr = { response?: { data?: { detail?: string } } };

export function useECs(clienteId: number | null) {
  const [ecs, setEcs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!clienteId) {
      setEcs([]);
      return;
    }

    const carregarECs = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const { data } = await apiClient.get(`/clientes/${clienteId}/ecs`);
        setEcs(data);
      } catch (err: unknown) {
        console.error('Erro ao carregar ECs:', err);
        setError((err as ApiErr)?.response?.data?.detail || 'Erro ao carregar ECs');
        setEcs([]);
      } finally {
        setLoading(false);
      }
    };

    carregarECs();
  }, [clienteId]);

  return { ecs, loading, error };
}

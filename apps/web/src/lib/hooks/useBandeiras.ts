/**
 * Hook para gerenciar bandeiras
 */
import { useState, useEffect } from 'react';
import { gestaoApi } from '@/lib/api/gestao';
import { BandeiraDisponivel } from '@/lib/types/gestao';

export function useBandeiras() {
  const [bandeiras, setBandeiras] = useState<BandeiraDisponivel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBandeiras = async () => {
    try {
      setLoading(true);
      const data = await gestaoApi.bandeiras.listar();
      setBandeiras(data);
      setError(null);
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao carregar bandeiras');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBandeiras();
  }, []);

  return { bandeiras, loading, error, refetch: fetchBandeiras };
}

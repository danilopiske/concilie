import { useState, useCallback } from 'react';
import { gestaoApi } from '@/lib/api/gestao';

export function useBandeirasPorEC() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bandeirasEC, setBandeirasEC] = useState<Record<string, number>>({});

  const fetchBandeirasEC = useCallback(async (ecId: string | number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await gestaoApi.bandeirasPorEC.obter(ecId);
      setBandeirasEC(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao carregar bandeiras do EC');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const salvarBandeirasEC = useCallback(async (ecId: string | number, bandeiras: Record<string, number>) => {
    try {
      setLoading(true);
      setError(null);
      await gestaoApi.bandeirasPorEC.atualizar(ecId, bandeiras);
      // Recarregar para garantir sincronia
      await fetchBandeirasEC(ecId);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Erro ao salvar bandeiras do EC';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  }, [fetchBandeirasEC]);

  return {
    bandeirasEC,
    loading,
    error,
    fetchBandeirasEC,
    salvarBandeirasEC,
  };
}

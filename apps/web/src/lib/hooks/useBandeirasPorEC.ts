import { useState, useCallback } from 'react';
import { gestaoApi } from '@/lib/api/gestao';

type ApiErr = { response?: { data?: { detail?: string } } };

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
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao carregar bandeiras do EC');
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
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao salvar bandeiras do EC';
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

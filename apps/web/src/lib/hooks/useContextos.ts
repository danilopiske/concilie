/**
 * Hook para gerenciar contextos
 */
import { useState, useEffect } from 'react';
import { gestaoApi } from '@/lib/api/gestao';
import { Contexto } from '@/lib/types/gestao';

type ApiErr = { response?: { data?: { detail?: string } } };

export function useContextos(incluirInativos: boolean = false) {
  const [contextos, setContextos] = useState<Contexto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchContextos = async () => {
    try {
      setLoading(true);
      const data = await gestaoApi.contextos.listar(incluirInativos);
      setContextos(data);
      setError(null);
    } catch (err: unknown) {
      setError((err as ApiErr)?.response?.data?.detail || 'Erro ao carregar contextos');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContextos();
  }, [incluirInativos]);

  return { contextos, loading, error, refetch: fetchContextos };
}

/**
 * Hook para gerenciar termos filtráveis
 */

import { useState, useEffect, useCallback } from 'react';
import { listarTermos, adicionarTermo, atualizarTermo, excluirTermo, TermoFiltravel, TermoFiltravelCreate } from '@/lib/api/termos';

type ApiErr = { response?: { data?: { detail?: string } } };

interface UseTermosProps {
  ec: string;
  contexto: string;
  tipo?: string;
}

export function useTermos({ ec, contexto, tipo }: UseTermosProps) {
  const [termos, setTermos] = useState<TermoFiltravel[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTermos = useCallback(async () => {
    if (!ec) {
      setTermos([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await listarTermos(ec, contexto, tipo);
      setTermos(data);
    } catch (err: unknown) {
      setError((err as ApiErr)?.response?.data?.detail || 'Erro ao carregar termos');
      console.error('Erro ao carregar termos:', err);
    } finally {
      setLoading(false);
    }
  }, [ec, contexto, tipo]);

  useEffect(() => {
    fetchTermos();
  }, [fetchTermos]);

  const adicionar = async (novoTermo: TermoFiltravelCreate) => {
    try {
      setLoading(true);
      setError(null);
      const termo = await adicionarTermo(novoTermo);
      setTermos((prev) => [...prev, termo]);
      return termo;
    } catch (err: unknown) {
      const errorMsg = (err as ApiErr)?.response?.data?.detail || 'Erro ao adicionar termo';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const excluir = async (termoId: number) => {
    try {
      setLoading(true);
      setError(null);
      await excluirTermo(termoId);
      setTermos((prev) => prev.filter((t) => t.id !== termoId));
    } catch (err: unknown) {
      const errorMsg = (err as ApiErr)?.response?.data?.detail || 'Erro ao excluir termo';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const atualizar = async (termoId: number, dados: { termo?: string; tipo?: string }) => {
    try {
      setError(null);
      const updated = await atualizarTermo(termoId, dados);
      setTermos((prev) => prev.map((t) => (t.id === termoId ? updated : t)));
      return updated;
    } catch (err: unknown) {
      const errorMsg = (err as ApiErr)?.response?.data?.detail || 'Erro ao atualizar termo';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  };

  return {
    termos,
    loading,
    error,
    refetch: fetchTermos,
    adicionar,
    atualizar,
    excluir,
  };
}

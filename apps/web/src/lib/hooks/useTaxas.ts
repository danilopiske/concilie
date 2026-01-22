/**
 * Hook para gerenciar taxas
 */
import { useState, useEffect } from 'react';
import { taxasApi, Taxa, TaxaCreate } from '@/lib/api/taxas';

export function useTaxas(ec: string | null, contexto: string = 'padrao') {
  const [taxas, setTaxas] = useState<Taxa[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTaxas = async () => {
    if (!ec) {
      setTaxas([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await taxasApi.listarPorEC(ec, contexto);
      setTaxas(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao carregar taxas');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTaxas();
  }, [ec, contexto]);

  const adicionar = async (taxa: TaxaCreate) => {
    try {
      setError(null);
      await taxasApi.criar(taxa);
      await fetchTaxas(); // Recarregar lista
      return true;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao adicionar taxa');
      throw err;
    }
  };

  const atualizar = async (taxaId: number, taxa: Partial<TaxaCreate>) => {
    try {
      setError(null);
      await taxasApi.atualizar(taxaId, taxa);
      await fetchTaxas(); // Recarregar lista
      return true;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao atualizar taxa');
      throw err;
    }
  };

  const excluir = async (taxaId: number) => {
    try {
      setError(null);
      await taxasApi.deletar(taxaId);
      await fetchTaxas(); // Recarregar lista
      return true;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao excluir taxa');
      throw err;
    }
  };

  return {
    taxas,
    loading,
    error,
    adicionar,
    atualizar,
    excluir,
    refetch: fetchTaxas,
  };
}

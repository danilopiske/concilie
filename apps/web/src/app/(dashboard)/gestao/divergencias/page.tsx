'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { AlertTriangle, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { divergenciasApi, DivergenciaConsolidadaItem } from '@/lib/api/divergencias';

const PAGE_SIZE = 20;

export default function DivergenciasConsolidadoPage() {
  const [items, setItems] = useState<DivergenciaConsolidadaItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busca, setBusca] = useState('');

  const fetchData = useCallback(async (currentOffset: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await divergenciasApi.getConsolidado(PAGE_SIZE, currentOffset);
      setItems(data.items);
      setTotal(data.total);
    } catch {
      setError('Erro ao carregar painel de divergências.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(offset);
  }, [fetchData, offset]);

  const itensFiltrados = busca.trim()
    ? items.filter((i) =>
        i.nome_cliente.toLowerCase().includes(busca.toLowerCase())
      )
    : items;

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <AlertTriangle className="w-7 h-7 text-amber-500" />
        <div>
          <h1 className="text-2xl font-bold text-[#1e3a8a]">Painel de Divergências</h1>
          <p className="text-sm text-gray-500">
            Todos os clientes com divergências entre taxas contratadas e cobradas
          </p>
        </div>
      </div>

      {/* Filtro */}
      <div className="mb-4 relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Filtrar por nome do cliente..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#1e3a8a]/20"
        />
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Cliente</th>
              <th className="text-right px-4 py-3 font-semibold text-gray-600">Divergências</th>
              <th className="text-right px-4 py-3 font-semibold text-gray-600">Diferença Total (%)</th>
              <th className="text-center px-4 py-3 font-semibold text-gray-600">Ações</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={4} className="text-center py-12 text-gray-400">
                  Carregando...
                </td>
              </tr>
            )}
            {error && !loading && (
              <tr>
                <td colSpan={4} className="text-center py-12 text-red-500">
                  {error}
                </td>
              </tr>
            )}
            {!loading && !error && itensFiltrados.length === 0 && (
              <tr>
                <td colSpan={4} className="text-center py-12 text-gray-400">
                  Nenhuma divergência encontrada.
                </td>
              </tr>
            )}
            {!loading &&
              !error &&
              itensFiltrados.map((item) => (
                <tr
                  key={item.cliente_id}
                  className="border-b border-gray-100 hover:bg-amber-50/30 transition-colors"
                >
                  <td className="px-4 py-3 font-medium text-gray-800">
                    {item.nome_cliente}
                    <span className="ml-2 text-xs text-gray-400">#{item.cliente_id}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-semibold text-xs">
                      <AlertTriangle className="w-3 h-3" />
                      {item.total_divergencias}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-amber-600 font-medium">
                    {item.valor_total_divergente.toFixed(4)}%
                  </td>
                  <td className="px-4 py-3 text-center">
                    <Link
                      href={`/gestao/clientes/${item.cliente_id}/divergencias`}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#1e3a8a] text-white text-xs font-medium hover:bg-[#1e3a8a]/90 transition-colors"
                    >
                      Ver detalhes
                    </Link>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Paginação */}
      {!loading && !error && total > PAGE_SIZE && (
        <div className="flex items-center justify-between mt-4">
          <span className="text-sm text-gray-500">
            Página {currentPage} de {totalPages} — {total} clientes com divergências
          </span>
          <div className="flex gap-2">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-200 text-sm disabled:opacity-40 hover:bg-gray-50 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Anterior
            </button>
            <button
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-200 text-sm disabled:opacity-40 hover:bg-gray-50 transition-colors"
            >
              Próxima
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

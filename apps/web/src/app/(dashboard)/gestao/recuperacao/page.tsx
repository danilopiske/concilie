'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { TrendingUp, Download, Trophy, DollarSign, AlertTriangle } from 'lucide-react';
import { recuperacaoApi, type RankingRecuperacao } from '@/lib/api/recuperacao';

function formatBRL(value: number) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export default function RecuperacaoPage() {
  const [dados, setDados] = useState<RankingRecuperacao | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    recuperacaoApi
      .getRanking(20)
      .then(setDados)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const maxPerda = dados ? Math.max(...dados.ranking.map((r) => r.total_perda_rs), 1) : 1;

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-6 h-6 text-[#1e3a8a]" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">Ranking de Recuperação</h1>
            <p className="text-sm text-gray-500">
              Clientes ordenados por valor potencial a recuperar
            </p>
          </div>
        </div>
        <a
          href={recuperacaoApi.exportarCsvUrl()}
          download
          className="flex items-center gap-2 px-4 py-2 text-sm border border-[#1e3a8a] text-[#1e3a8a] rounded-lg hover:bg-blue-50 transition-colors"
        >
          <Download className="w-4 h-4" />
          Exportar CSV
        </a>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 text-sm">Carregando...</div>
      ) : !dados ? (
        <div className="text-center py-12 text-red-400 text-sm">Erro ao carregar dados.</div>
      ) : (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gradient-to-r from-[#1e3a8a] to-[#1e40af] rounded-xl p-5 text-white">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-5 h-5 text-[#f59e0b]" />
                <span className="text-sm opacity-80">Total Recuperável</span>
              </div>
              <p className="text-3xl font-bold">{formatBRL(dados.total_recuperavel_rs)}</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-5">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <span className="text-sm text-gray-500">Clientes com Perdas</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">{dados.total_clientes_com_perda}</p>
            </div>
          </div>

          {/* Ranking */}
          {dados.ranking.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-100 p-8 text-center">
              <Trophy className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">
                Nenhuma perda financeira encontrada nos dados calculados.
              </p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-100">
                <h2 className="text-sm font-semibold text-gray-700">
                  Top Clientes por Perda Financeira
                </h2>
              </div>
              <div className="divide-y divide-gray-50">
                {dados.ranking.map((item) => (
                  <div key={item.cliente_id} className="px-4 py-4 flex items-center gap-4">
                    {/* Posição */}
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                        item.posicao === 1
                          ? 'bg-[#f59e0b] text-white'
                          : item.posicao === 2
                            ? 'bg-gray-300 text-gray-700'
                            : item.posicao === 3
                              ? 'bg-amber-700 text-white'
                              : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {item.posicao}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <Link
                          href={`/gestao/clientes/${item.cliente_id}`}
                          className="text-sm font-semibold text-gray-800 hover:text-[#1e3a8a] transition-colors truncate"
                        >
                          {item.nome || `Cliente ${item.cliente_id}`}
                        </Link>
                        <span className="text-sm font-bold text-red-600 flex-shrink-0 ml-2">
                          {formatBRL(item.total_perda_rs)}
                        </span>
                      </div>
                      {/* Barra de progresso relativa */}
                      <div className="h-1.5 bg-gray-100 rounded-full">
                        <div
                          className="h-1.5 bg-gradient-to-r from-[#1e3a8a] to-[#f59e0b] rounded-full transition-all duration-700"
                          style={{ width: `${(item.total_perda_rs / maxPerda) * 100}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        {item.count_transacoes.toLocaleString('pt-BR')} transações · média{' '}
                        {formatBRL(item.media_perda_rs)}/transação
                      </p>
                    </div>

                    {/* Link divergências */}
                    <Link
                      href={`/gestao/clientes/${item.cliente_id}/divergencias`}
                      className="flex-shrink-0 text-xs text-[#1e3a8a] hover:text-[#f59e0b] transition-colors"
                    >
                      Ver detalhes →
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

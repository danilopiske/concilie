'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { BarChart3, CheckCircle2, DollarSign, FileText, TrendingUp } from 'lucide-react';
import { contestacoesMetricasApi, type ContestacaoMetricas } from '@/lib/api/contestacoesMetricas';

function formatBRL(v: number) {
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

const STATUS_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  rascunho:   { label: 'Rascunho',   color: 'text-gray-600',   bg: 'bg-gray-400' },
  enviada:    { label: 'Enviada',    color: 'text-blue-600',   bg: 'bg-blue-500' },
  em_analise: { label: 'Em Análise', color: 'text-purple-600', bg: 'bg-purple-500' },
  deferida:   { label: 'Deferida',   color: 'text-green-600',  bg: 'bg-green-500' },
  indeferida: { label: 'Indeferida', color: 'text-red-600',    bg: 'bg-red-500' },
};

export default function ContestacaoMetricasPage() {
  const [dados, setDados] = useState<ContestacaoMetricas | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    contestacoesMetricasApi
      .get()
      .then(setDados)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const maxStatus = dados ? Math.max(...Object.values(dados.por_status), 1) : 1;

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <BarChart3 className="w-6 h-6 text-[#1e3a8a]" />
        <h1 className="text-xl font-bold text-gray-900">Métricas de Contestações</h1>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 text-sm">Carregando...</div>
      ) : !dados ? (
        <div className="text-center py-12 text-red-400 text-sm">Erro ao carregar métricas.</div>
      ) : (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-gray-100 p-4">
              <FileText className="w-5 h-5 text-gray-400 mb-2" />
              <p className="text-2xl font-bold text-gray-900">{dados.total_contestacoes}</p>
              <p className="text-xs text-gray-500">Total de contestações</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-4">
              <CheckCircle2 className="w-5 h-5 text-green-500 mb-2" />
              <p className="text-2xl font-bold text-gray-900">{dados.taxa_sucesso_pct}%</p>
              <p className="text-xs text-gray-500">Taxa de sucesso</p>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl border border-green-200 p-4">
              <DollarSign className="w-5 h-5 text-green-600 mb-2" />
              <p className="text-xl font-bold text-green-700">{formatBRL(dados.valor_recuperado_rs)}</p>
              <p className="text-xs text-green-600">Valor recuperado</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-4">
              <TrendingUp className="w-5 h-5 text-amber-500 mb-2" />
              <p className="text-xl font-bold text-gray-900">{formatBRL(dados.valor_em_disputa_rs)}</p>
              <p className="text-xs text-gray-500">Em disputa</p>
            </div>
          </div>

          {/* Gráfico de barras por status */}
          <div className="bg-white rounded-xl border border-gray-100 p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Distribuição por Status</h2>
            <div className="space-y-3">
              {Object.entries(dados.por_status).map(([status, count]) => {
                const cfg = STATUS_LABELS[status] ?? {
                  label: status,
                  color: 'text-gray-600',
                  bg: 'bg-gray-400',
                };
                return (
                  <div key={status}>
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
                      <span className="text-xs text-gray-500">{count}</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full">
                      <div
                        className={`h-2 ${cfg.bg} rounded-full transition-all duration-700`}
                        style={{ width: `${(count / maxStatus) * 100}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top clientes */}
          {dados.top_clientes_recuperacao.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-100 p-5">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">
                Top Clientes — Valor Recuperado
              </h2>
              <div className="space-y-3">
                {dados.top_clientes_recuperacao.map((c, i) => (
                  <div key={c.cliente_id} className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-[#f59e0b] text-white text-xs flex items-center justify-center font-bold flex-shrink-0">
                      {i + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <Link
                        href={`/gestao/clientes/${c.cliente_id}/contestacoes`}
                        className="text-sm font-medium text-gray-800 hover:text-[#1e3a8a] transition-colors truncate block"
                      >
                        {c.nome || `Cliente ${c.cliente_id}`}
                      </Link>
                      <p className="text-xs text-gray-400">{c.total_deferidas} deferida(s)</p>
                    </div>
                    <span className="text-sm font-bold text-green-600 flex-shrink-0">
                      {formatBRL(c.total_recuperado_rs)}
                    </span>
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

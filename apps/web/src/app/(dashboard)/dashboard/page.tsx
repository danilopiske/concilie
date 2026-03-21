'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, BarChart3, FileText, RefreshCw, TrendingUp } from 'lucide-react';
import { AtividadeItem } from '@/components/dashboard/AtividadeItem';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { MiniBarChart } from '@/components/dashboard/MiniBarChart';
import {
  AtividadeRecenteResponse,
  AtividadeSemanalResponse,
  DashboardResumo,
  dashboardApi,
} from '@/lib/api/dashboard';

const PERIODOS = [
  { label: '7 dias', value: 7 },
  { label: '30 dias', value: 30 },
  { label: '90 dias', value: 90 },
];

export default function DashboardPage() {
  const [resumo, setResumo] = useState<DashboardResumo | null>(null);
  const [atividade, setAtividade] = useState<AtividadeRecenteResponse | null>(null);
  const [atividadeSemanal, setAtividadeSemanal] = useState<AtividadeSemanalResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [periodo, setPeriodo] = useState(30);

  const carregar = async (p: number = periodo) => {
    setLoading(true);
    setError(null);
    try {
      const [r, a, s] = await Promise.all([
        dashboardApi.getResumo(p),
        dashboardApi.getAtividadeRecente(),
        dashboardApi.getAtividadeSemanal(),
      ]);
      setResumo(r);
      setAtividade(a);
      setAtividadeSemanal(s);
    } catch {
      setError('Erro ao carregar dados do dashboard.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar(periodo);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [periodo]);

  const formatCurrency = (v: number) =>
    v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  return (
    <div className="max-w-7xl mx-auto pb-10 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Dashboard Executivo</h1>
          <p className="text-sm text-gray-500 mt-1">Visão geral do sistema Concilie</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Seletor de período */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {PERIODOS.map((p) => (
              <button
                key={p.value}
                onClick={() => setPeriodo(p.value)}
                className={`px-3 py-1.5 text-sm transition-colors ${
                  periodo === p.value
                    ? 'bg-[#1e3a8a] text-white'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
          <button
            onClick={() => carregar(periodo)}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 border rounded hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>
      )}

      {/* KPI Cards */}
      {loading && !resumo ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : resumo ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title={`Processamentos (${PERIODOS.find((p) => p.value === periodo)?.label ?? 'período'})`}
            value={resumo.processamentos_mes_atual}
            icon={BarChart3}
            color="blue"
            sublabel={`${resumo.total_processamentos} total`}
          />
          <KpiCard
            title="Valor Conciliado"
            value={formatCurrency(resumo.valor_total_conciliado)}
            icon={TrendingUp}
            color="green"
            sublabel="Total acumulado"
          />
          <KpiCard
            title="Alertas Abusividade"
            value={resumo.alertas_abusividade_pendentes}
            icon={AlertTriangle}
            color={resumo.alertas_abusividade_pendentes > 0 ? 'red' : 'green'}
            sublabel="Variações de taxa detectadas"
          />
          <KpiCard
            title="Extratos Divergentes"
            value={resumo.extratos_divergentes}
            icon={FileText}
            color={resumo.extratos_divergentes > 0 ? 'yellow' : 'green'}
            sublabel={`${resumo.extratos_aguardando} aguardando`}
          />
        </div>
      ) : null}

      {/* Último processamento */}
      {resumo?.ultimo_processamento && (
        <div className="bg-gray-50 border rounded-lg px-4 py-3 text-sm text-gray-600 flex items-center gap-3">
          <span className="font-medium text-gray-700">Último processamento:</span>
          <span>{resumo.ultimo_processamento.nome_arquivo}</span>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
            resumo.ultimo_processamento.status === 'Sucesso'
              ? 'bg-green-100 text-green-700'
              : resumo.ultimo_processamento.status === 'Erro'
              ? 'bg-red-100 text-red-700'
              : 'bg-yellow-100 text-yellow-700'
          }`}>
            {resumo.ultimo_processamento.status}
          </span>
          {resumo.ultimo_processamento.data && (
            <span className="text-gray-400 text-xs ml-auto">
              {new Date(resumo.ultimo_processamento.data).toLocaleString('pt-BR')}
            </span>
          )}
        </div>
      )}

      {/* Relatórios do mês */}
      {resumo && (
        <div className="text-sm text-gray-500">
          Relatórios gerados este mês:{' '}
          <span className="font-semibold text-gray-700">{resumo.relatorios_gerados_mes}</span>
        </div>
      )}

      {/* Mini gráfico de atividade semanal */}
      {atividadeSemanal && atividadeSemanal.semanas.length > 0 && (
        <MiniBarChart
          title="Importações por semana (últimas 4 semanas)"
          data={atividadeSemanal.semanas.map((s) => ({ label: s.label, value: s.count }))}
        />
      )}

      {/* Atividade Recente */}
      <div className="bg-white border rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50">
          <h2 className="font-semibold text-gray-700">Atividade Recente</h2>
        </div>
        <div className="px-4">
          {loading && !atividade ? (
            <div className="py-8 text-center">
              <RefreshCw className="w-5 h-5 animate-spin text-gray-400 mx-auto" />
            </div>
          ) : atividade && atividade.eventos.length > 0 ? (
            atividade.eventos.map((evento, i) => (
              <AtividadeItem key={i} evento={evento} />
            ))
          ) : (
            <p className="text-sm text-gray-400 py-8 text-center">Nenhuma atividade recente.</p>
          )}
        </div>
      </div>
    </div>
  );
}

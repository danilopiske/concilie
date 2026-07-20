'use client';

import { useEffect, useState, useCallback } from 'react';
import { Upload, Calculator, FileBarChart, AlertTriangle, Activity } from 'lucide-react';
import Link from 'next/link';
import { tarefasApi, TarefaItem, TarefasResumo } from '@/lib/api/tarefas';

const POLLING_INTERVAL = 15000;

function statusBadge(status: string): string {
  const s = status.toUpperCase();
  if (s === 'PENDING' || s === 'PENDING') return 'bg-gray-100 text-gray-600';
  if (s === 'PROCESSING') return 'bg-blue-100 text-blue-700';
  if (s === 'SUCCESS' || s === 'READY') return 'bg-green-100 text-green-700';
  if (s === 'FAILED' || s === 'ERROR') return 'bg-red-100 text-red-700';
  // lowercase variants
  if (status === 'pending') return 'bg-gray-100 text-gray-600';
  if (status === 'processing') return 'bg-blue-100 text-blue-700';
  if (status === 'ready') return 'bg-green-100 text-green-700';
  if (status === 'error') return 'bg-red-100 text-red-700';
  return 'bg-gray-100 text-gray-600';
}

function relativeDate(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'agora';
  if (mins < 60) return `${mins}min atrás`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h atrás`;
  const days = Math.floor(hrs / 24);
  return `${days}d atrás`;
}

interface TarefaCardProps {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  items: TarefaItem[];
  linkHref: string;
  linkLabel: string;
  showProgress?: boolean;
}

function TarefaCard({ title, icon: Icon, items, linkHref, linkLabel, showProgress }: TarefaCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5 text-[#1e3a8a]" />
          <h2 className="text-base font-semibold text-gray-800">{title}</h2>
        </div>
        <Link
          href={linkHref}
          className="text-xs text-[#1e3a8a] hover:text-[#f59e0b] transition-colors font-medium"
        >
          {linkLabel} →
        </Link>
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-4">Nenhuma tarefa recente</p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {items.map((item) => (
            <li key={item.id} className="py-2 flex items-center justify-between gap-2">
              <div className="flex flex-col min-w-0">
                <span className="text-xs text-gray-500 font-mono truncate">{item.id.slice(0, 8)}…</span>
                {item.usuario && (
                  <span className="text-xs text-gray-400">{item.usuario}</span>
                )}
                {showProgress && item.progress !== undefined && (
                  <div className="mt-1 w-full bg-gray-100 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full transition-all"
                      style={{ width: `${item.progress}%` }}
                    />
                  </div>
                )}
              </div>
              <div className="flex flex-col items-end gap-1 flex-shrink-0">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusBadge(item.status)}`}>
                  {item.status}
                </span>
                {item.created_at && (
                  <span className="text-xs text-gray-400">{relativeDate(item.created_at)}</span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function TarefasPage() {
  const [resumo, setResumo] = useState<TarefasResumo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchResumo = useCallback(async () => {
    try {
      const data = await tarefasApi.getResumo();
      setResumo(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError('Erro ao carregar tarefas. Tentando novamente...');
      console.error('Erro ao buscar resumo de tarefas:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchResumo();
    const interval = setInterval(fetchResumo, POLLING_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchResumo]);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Activity className="w-6 h-6 text-[#1e3a8a]" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">Centro de Progresso de Tarefas</h1>
            <p className="text-sm text-gray-500">Acompanhe o status de todas as tarefas assíncronas</p>
          </div>
        </div>
        {lastUpdated && (
          <span className="text-xs text-gray-400">
            Atualizado às {lastUpdated.toLocaleTimeString('pt-BR')} · atualiza a cada 15s
          </span>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && !resumo && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 h-48 animate-pulse">
              <div className="h-4 bg-gray-100 rounded w-1/3 mb-4" />
              <div className="space-y-2">
                <div className="h-3 bg-gray-100 rounded w-full" />
                <div className="h-3 bg-gray-100 rounded w-5/6" />
                <div className="h-3 bg-gray-100 rounded w-4/6" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cards */}
      {resumo && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TarefaCard
            title="Importações"
            icon={Upload}
            items={resumo.importacoes}
            linkHref="/importar/processamentos"
            linkLabel="Ver processamentos"
            showProgress
          />
          <TarefaCard
            title="Cálculos"
            icon={Calculator}
            items={resumo.calculos}
            linkHref="/calculos/gestao"
            linkLabel="Ver cálculos"
            showProgress
          />
          <TarefaCard
            title="Relatórios"
            icon={FileBarChart}
            items={resumo.relatorios}
            linkHref="/relatorios/gestao"
            linkLabel="Ver relatórios"
            showProgress
          />
          <TarefaCard
            title="Abusividade"
            icon={AlertTriangle}
            items={resumo.abusividades}
            linkHref="/abusividade"
            linkLabel="Ver abusividade"
            showProgress={false}
          />
        </div>
      )}
    </div>
  );
}

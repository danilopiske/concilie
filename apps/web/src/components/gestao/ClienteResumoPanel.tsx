'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, Bell, FileBarChart, Upload, Calculator, TrendingUp } from 'lucide-react';
import { clienteResumoApi, type ClienteResumo } from '@/lib/api/clienteResumo';

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    SUCCESS: 'bg-green-100 text-green-700',
    ready: 'bg-green-100 text-green-700',
    PROCESSING: 'bg-blue-100 text-blue-700',
    processing: 'bg-blue-100 text-blue-700',
    PENDING: 'bg-gray-100 text-gray-600',
    pending: 'bg-gray-100 text-gray-600',
    FAILED: 'bg-red-100 text-red-700',
    error: 'bg-red-100 text-red-700',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${map[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  );
}

function tempoRelativo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'agora';
  if (mins < 60) return `${mins}min`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return `${Math.floor(hrs / 24)}d`;
}

export function ClienteResumoPanel({ clienteId }: { clienteId: number }) {
  const [resumo, setResumo] = useState<ClienteResumo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    clienteResumoApi
      .getResumo(clienteId)
      .then(setResumo)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [clienteId]);

  if (loading) return <div className="animate-pulse h-32 bg-gray-100 rounded-xl" />;
  if (!resumo) return null;

  const ativas = [
    ...resumo.import_tasks_recentes,
    ...resumo.calculo_tasks_recentes,
    ...resumo.relatorio_tasks_recentes,
  ].filter((t) => t.status === 'PROCESSING' || t.status === 'processing' || t.status === 'PENDING' || t.status === 'pending').length;

  const sections = [
    { title: 'Importações', icon: Upload, items: resumo.import_tasks_recentes },
    { title: 'Cálculos', icon: Calculator, items: resumo.calculo_tasks_recentes },
    { title: 'Relatórios', icon: FileBarChart, items: resumo.relatorio_tasks_recentes },
  ];

  return (
    <div className="space-y-4">
      {/* KPI row */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white rounded-xl border border-gray-100 p-4 flex items-center gap-3">
          <Bell className="w-5 h-5 text-amber-500" />
          <div>
            <p className="text-2xl font-bold text-gray-900">{resumo.notificacoes_nao_lidas}</p>
            <p className="text-xs text-gray-500">Notificações pendentes</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4 flex items-center gap-3">
          <Activity className="w-5 h-5 text-blue-500" />
          <div>
            <p className="text-2xl font-bold text-gray-900">{ativas}</p>
            <p className="text-xs text-gray-500">Tarefas em andamento</p>
          </div>
        </div>
      </div>

      {/* Task sections */}
      {sections.map(
        ({ title, icon: Icon, items }) =>
          items.length > 0 && (
            <div key={title} className="bg-white rounded-xl border border-gray-100 p-4">
              <div className="flex items-center gap-2 mb-3">
                <Icon className="w-4 h-4 text-gray-500" />
                <h3 className="text-sm font-semibold text-gray-700">{title} Recentes</h3>
              </div>
              <div className="space-y-2">
                {items.slice(0, 3).map((item) => (
                  <div key={item.id} className="flex items-center justify-between gap-2">
                    <span className="text-xs text-gray-500 font-mono truncate max-w-[120px]">
                      {item.id.slice(0, 8)}&hellip;
                    </span>
                    <StatusBadge status={item.status} />
                    <span className="text-xs text-gray-400">{tempoRelativo(item.created_at)}</span>
                  </div>
                ))}
              </div>
            </div>
          ),
      )}
      {/* Link para relatório de divergências */}
      <div className="bg-white rounded-xl border border-gray-100 p-4">
        <Link
          href={`/gestao/clientes/${clienteId}/divergencias`}
          className="inline-flex items-center gap-1.5 text-xs text-[#1e3a8a] hover:text-[#f59e0b] transition-colors font-medium"
        >
          <TrendingUp className="w-3.5 h-3.5" />
          Ver relatório de divergências de taxas →
        </Link>
      </div>
    </div>
  );
}

'use client';
import { useEffect, useState } from 'react';
import {
  Activity,
  Database,
  Server,
  Users,
  Upload,
  Calculator,
  FileBarChart,
  RefreshCw,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { sistemaApi, type SistemaStatus } from '@/lib/api/sistema';

function StatusIndicator({ status }: { status: string }) {
  const ok = status === 'ok';
  return (
    <div className={`flex items-center gap-2 ${ok ? 'text-green-600' : 'text-red-600'}`}>
      {ok ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
      <span className="text-sm font-medium">{ok ? 'Operacional' : 'Com Problema'}</span>
    </div>
  );
}

function BadgeStatus({ status }: { status: string }) {
  const map: Record<string, string> = {
    SUCCESS: 'bg-green-100 text-green-700',
    PROCESSING: 'bg-blue-100 text-blue-700',
    PENDING: 'bg-gray-100 text-gray-600',
    FAILED: 'bg-red-100 text-red-700',
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
  if (mins < 60) return `${mins}min atrás`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h atrás`;
  return `${Math.floor(hrs / 24)}d atrás`;
}

export default function StatusPage() {
  const [status, setStatus] = useState<SistemaStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const carregar = async () => {
    setLoading(true);
    try {
      const data = await sistemaApi.getStatus();
      setStatus(data);
      setLastUpdate(new Date());
    } catch {
      // silencioso
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
    const interval = setInterval(carregar, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="w-6 h-6 text-[#1e3a8a]" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">Status do Sistema</h1>
            {lastUpdate && (
              <p className="text-xs text-gray-500">
                Atualizado: {lastUpdate.toLocaleTimeString('pt-BR')}
              </p>
            )}
          </div>
        </div>
        <button
          onClick={carregar}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 text-sm text-[#1e3a8a] border border-[#1e3a8a] rounded-lg hover:bg-blue-50 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Atualizar
        </button>
      </div>

      {loading && !status ? (
        <div className="text-center py-12 text-gray-400 text-sm">Carregando...</div>
      ) : status ? (
        <>
          {/* Serviços */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-xl border border-gray-100 p-5">
              <div className="flex items-center gap-2 mb-3">
                <Server className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-semibold text-gray-700">API</span>
              </div>
              <StatusIndicator status={status.api} />
            </div>
            <div className="bg-white rounded-xl border border-gray-100 p-5">
              <div className="flex items-center gap-2 mb-3">
                <Database className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-semibold text-gray-700">Banco de Dados</span>
              </div>
              <StatusIndicator status={status.database} />
            </div>
          </div>

          {/* Métricas */}
          <div className="bg-white rounded-xl border border-gray-100 p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Métricas do Sistema</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Clientes', value: status.metricas.total_clientes, icon: Users },
                { label: 'Importações', value: status.metricas.total_importacoes, icon: Upload },
                { label: 'Cálculos', value: status.metricas.total_calculos, icon: Calculator },
                { label: 'Relatórios', value: status.metricas.total_relatorios, icon: FileBarChart },
              ].map(({ label, value, icon: Icon }) => (
                <div key={label} className="text-center p-3 bg-gray-50 rounded-lg">
                  <Icon className="w-5 h-5 text-[#1e3a8a] mx-auto mb-1" />
                  <p className="text-2xl font-bold text-gray-900">{value.toLocaleString('pt-BR')}</p>
                  <p className="text-xs text-gray-500">{label}</p>
                </div>
              ))}
            </div>
            {status.metricas.tarefas_ativas > 0 && (
              <div className="mt-3 p-3 bg-blue-50 rounded-lg flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-600 animate-pulse" />
                <span className="text-sm text-blue-700 font-medium">
                  {status.metricas.tarefas_ativas} tarefa
                  {status.metricas.tarefas_ativas > 1 ? 's' : ''} em andamento
                </span>
              </div>
            )}
          </div>

          {/* Últimas tarefas */}
          {[
            { title: 'Últimas Importações', items: status.ultimas_tarefas.importacoes, icon: Upload },
            { title: 'Últimos Cálculos', items: status.ultimas_tarefas.calculos, icon: Calculator },
            { title: 'Últimos Relatórios', items: status.ultimas_tarefas.relatorios, icon: FileBarChart },
          ].map(
            ({ title, items, icon: Icon }) =>
              items.length > 0 && (
                <div key={title} className="bg-white rounded-xl border border-gray-100 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Icon className="w-4 h-4 text-gray-500" />
                    <h2 className="text-sm font-semibold text-gray-700">{title}</h2>
                  </div>
                  <div className="space-y-2">
                    {items.map((item) => (
                      <div key={item.id} className="flex items-center justify-between py-1">
                        <span className="text-xs font-mono text-gray-500">
                          {item.id.slice(0, 12)}…
                        </span>
                        <BadgeStatus status={item.status} />
                        <span className="text-xs text-gray-400">
                          {tempoRelativo(item.created_at)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ),
          )}
        </>
      ) : (
        <div className="text-center py-12 text-red-400 text-sm">
          Não foi possível carregar o status do sistema.
        </div>
      )}
    </div>
  );
}

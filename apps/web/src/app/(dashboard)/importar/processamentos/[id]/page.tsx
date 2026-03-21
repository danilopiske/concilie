'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Upload,
  Calculator,
  FileBarChart,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
} from 'lucide-react';
import { processamentosApi, type ProcessamentoDetalhes, type ProcessamentoTaskItem, type SumarioFinanceiro } from '@/lib/api/processamentos';

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; className: string }> = {
    SUCCESS: { label: 'Concluído', className: 'bg-green-100 text-green-700' },
    ready: { label: 'Pronto', className: 'bg-green-100 text-green-700' },
    PROCESSING: { label: 'Processando', className: 'bg-blue-100 text-blue-700' },
    PENDING: { label: 'Pendente', className: 'bg-gray-100 text-gray-600' },
    pending: { label: 'Pendente', className: 'bg-gray-100 text-gray-600' },
    FAILED: { label: 'Falhou', className: 'bg-red-100 text-red-700' },
    error: { label: 'Erro', className: 'bg-red-100 text-red-700' },
  };
  const cfg = map[status] ?? { label: status, className: 'bg-gray-100 text-gray-600' };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cfg.className}`}>
      {cfg.label}
    </span>
  );
}

function StatusGeral({ status }: { status: string }) {
  const map = {
    concluido: {
      icon: <CheckCircle2 className="w-5 h-5 text-green-500" />,
      label: 'Concluído',
      cls: 'bg-green-50 text-green-700',
    },
    em_andamento: {
      icon: <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />,
      label: 'Em Andamento',
      cls: 'bg-blue-50 text-blue-700',
    },
    com_erro: {
      icon: <XCircle className="w-5 h-5 text-red-500" />,
      label: 'Com Erro',
      cls: 'bg-red-50 text-red-700',
    },
    parcial: {
      icon: <Clock className="w-5 h-5 text-amber-500" />,
      label: 'Parcial',
      cls: 'bg-amber-50 text-amber-700',
    },
    sem_dados: {
      icon: <Clock className="w-5 h-5 text-gray-400" />,
      label: 'Sem Dados',
      cls: 'bg-gray-50 text-gray-600',
    },
  };
  const cfg = map[status as keyof typeof map] ?? map.sem_dados;
  return (
    <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${cfg.cls}`}>
      {cfg.icon}
      <span className="text-sm font-medium">{cfg.label}</span>
    </div>
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

interface TaskSectionProps {
  title: string;
  items: ProcessamentoTaskItem[];
  icon: React.ElementType;
  emptyMsg: string;
}

function TaskSection({ title, items, icon: Icon, emptyMsg }: TaskSectionProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5">
      <div className="flex items-center gap-2 mb-4">
        <Icon className="w-4 h-4 text-gray-500" />
        <h2 className="text-sm font-semibold text-gray-700">{title}</h2>
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-gray-400">{emptyMsg}</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div
              key={item.id}
              className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0"
            >
              <span className="text-xs font-mono text-gray-500">{item.id.slice(0, 12)}…</span>
              <div className="flex items-center gap-3">
                {item.progress !== undefined && (
                  <div className="w-16 bg-gray-100 rounded-full h-1.5">
                    <div
                      className="bg-[#1e3a8a] h-1.5 rounded-full"
                      style={{ width: `${item.progress}%` }}
                    />
                  </div>
                )}
                <StatusBadge status={item.status} />
                <span className="text-xs text-gray-400">{tempoRelativo(item.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProcessamentoDetalhesPage() {
  const { id } = useParams<{ id: string }>();
  const [detalhes, setDetalhes] = useState<ProcessamentoDetalhes | null>(null);
  const [financeiro, setFinanceiro] = useState<SumarioFinanceiro | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    if (!id) return;
    processamentosApi
      .getDetalhes(id)
      .then(setDetalhes)
      .catch(() => setErro(true))
      .finally(() => setLoading(false));
    processamentosApi
      .getSumarioFinanceiro(id)
      .then(setFinanceiro)
      .catch(() => {}); // não-bloqueante: sumário financeiro é opcional
  }, [id]);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/importar/processamentos"
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </Link>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-gray-900">Detalhes do Processamento</h1>
          <p className="text-xs text-gray-400 font-mono mt-0.5">{id}</p>
        </div>
        {detalhes && <StatusGeral status={detalhes.status_geral} />}
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 text-sm">Carregando...</div>
      ) : erro ? (
        <div className="text-center py-12 text-red-400 text-sm">
          Não foi possível carregar os detalhes.
        </div>
      ) : detalhes ? (
        <>
          {/* Totais */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: 'Importações', value: detalhes.totais.importacoes, icon: Upload, color: 'text-blue-500' },
              { label: 'Cálculos', value: detalhes.totais.calculos, icon: Calculator, color: 'text-purple-500' },
              { label: 'Relatórios', value: detalhes.totais.relatorios, icon: FileBarChart, color: 'text-green-500' },
              { label: 'Abusividade', value: detalhes.totais.abusividades, icon: AlertTriangle, color: 'text-amber-500' },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="bg-white rounded-xl border border-gray-100 p-4 text-center">
                <Icon className={`w-6 h-6 ${color} mx-auto mb-2`} />
                <p className="text-2xl font-bold text-gray-900">{value}</p>
                <p className="text-xs text-gray-500">{label}</p>
              </div>
            ))}
          </div>

          {/* Sumário Financeiro */}
          {financeiro && financeiro.tem_dados && (
            <div className="bg-gradient-to-r from-[#1e3a8a] to-[#1e40af] rounded-xl p-5 text-white">
              <h2 className="text-sm font-semibold opacity-80 mb-4">Sumário Financeiro</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs opacity-70">Total de Vendas</p>
                  <p className="text-xl font-bold">
                    {financeiro.total_vendas_rs.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </p>
                </div>
                <div>
                  <p className="text-xs opacity-70">Taxas Cobradas</p>
                  <p className="text-xl font-bold text-amber-300">
                    {financeiro.total_taxa_cobrada_rs.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </p>
                </div>
                <div>
                  <p className="text-xs opacity-70">Taxas Contratadas</p>
                  <p className="text-xl font-bold text-green-300">
                    {financeiro.total_taxa_contratada_rs.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </p>
                </div>
                <div>
                  <p className="text-xs opacity-70">Diferença (Contestável)</p>
                  <p className={`text-xl font-bold ${financeiro.diferenca_rs > 0 ? 'text-red-300' : 'text-green-300'}`}>
                    {financeiro.diferenca_rs.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </p>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-white/20 flex flex-wrap gap-4 text-xs opacity-70">
                <span>{financeiro.count_transacoes.toLocaleString('pt-BR')} transações processadas</span>
                <span>Taxa média cobrada: {financeiro.taxa_media_cobrada_pct.toFixed(4)}%</span>
                <span>Taxa média contratada: {financeiro.taxa_media_contratada_pct.toFixed(4)}%</span>
              </div>
            </div>
          )}

          {/* Seções de tasks */}
          <TaskSection
            title="Importações"
            items={detalhes.importacoes}
            icon={Upload}
            emptyMsg="Nenhuma importação realizada"
          />
          <TaskSection
            title="Cálculos"
            items={detalhes.calculos}
            icon={Calculator}
            emptyMsg="Nenhum cálculo realizado"
          />
          <TaskSection
            title="Relatórios"
            items={detalhes.relatorios}
            icon={FileBarChart}
            emptyMsg="Nenhum relatório gerado"
          />
          <TaskSection
            title="Análise de Abusividade"
            items={detalhes.abusividades}
            icon={AlertTriangle}
            emptyMsg="Nenhuma análise de abusividade"
          />
        </>
      ) : null}
    </div>
  );
}

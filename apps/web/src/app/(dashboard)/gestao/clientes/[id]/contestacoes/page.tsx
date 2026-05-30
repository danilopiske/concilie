'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Edit3,
} from 'lucide-react';
import { contestacaoApi, type ContestacoesPorCliente, type ContestacaoResumoItem } from '@/lib/api/contestacao';

const STATUS_CONFIG: Record<
  string,
  { label: string; icon: React.ReactNode; color: string; dot: string }
> = {
  rascunho: {
    label: 'Rascunho',
    icon: <Edit3 className="w-4 h-4" />,
    color: 'text-gray-600',
    dot: 'bg-gray-400',
  },
  pendente: {
    label: 'Pendente',
    icon: <Clock className="w-4 h-4" />,
    color: 'text-amber-600',
    dot: 'bg-amber-400',
  },
  enviada: {
    label: 'Enviada',
    icon: <FileText className="w-4 h-4" />,
    color: 'text-blue-600',
    dot: 'bg-blue-400',
  },
  deferida: {
    label: 'Deferida',
    icon: <CheckCircle2 className="w-4 h-4" />,
    color: 'text-green-600',
    dot: 'bg-green-400',
  },
  indeferida: {
    label: 'Indeferida',
    icon: <XCircle className="w-4 h-4" />,
    color: 'text-red-600',
    dot: 'bg-red-400',
  },
  em_analise: {
    label: 'Em Análise',
    icon: <AlertCircle className="w-4 h-4" />,
    color: 'text-purple-600',
    dot: 'bg-purple-400',
  },
};

function formatData(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

function formatValor(valor: number): string {
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function TimelineItem({ c }: { c: ContestacaoResumoItem }) {
  const cfg = STATUS_CONFIG[c.status] ?? {
    label: c.status,
    icon: <FileText className="w-4 h-4" />,
    color: 'text-gray-600',
    dot: 'bg-gray-400',
  };

  return (
    <div className="relative pl-10">
      <div className={`absolute left-2.5 top-3 w-3 h-3 rounded-full border-2 border-white ${cfg.dot}`} />
      <div className="bg-white rounded-xl border border-gray-100 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className={`flex items-center gap-1.5 ${cfg.color} mb-1`}>
              {cfg.icon}
              <span className="text-sm font-semibold">{cfg.label}</span>
              <span className="text-xs text-gray-400 ml-1">— {c.adquirente}</span>
            </div>

            {c.periodo_inicio && c.periodo_fim && (
              <p className="text-xs text-gray-500 mb-1">
                Período: {formatData(c.periodo_inicio)} a {formatData(c.periodo_fim)}
              </p>
            )}

            {c.processamento_id && (
              <p className="text-xs text-gray-500">
                Processamento:{' '}
                <Link
                  href={`/importar/processamentos/${c.processamento_id}`}
                  className="text-[#1e3a8a] hover:underline font-mono"
                >
                  #{c.processamento_id}
                </Link>
              </p>
            )}

            <p className="text-xs text-gray-400 mt-1 font-mono">{c.id.slice(0, 16)}…</p>
          </div>

          <div className="text-right flex-shrink-0">
            <p className="text-sm font-semibold text-gray-700">{formatValor(c.valor_excesso_total)}</p>
            <p className="text-xs text-gray-500 mt-1">{formatData(c.created_at)}</p>
            {c.updated_at && c.updated_at !== c.created_at && (
              <p className="text-xs text-gray-400">Atualizado: {formatData(c.updated_at)}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ContestacoesPorClientePage() {
  const { id } = useParams<{ id: string }>();
  const [dados, setDados] = useState<ContestacoesPorCliente | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    contestacaoApi
      .porCliente(parseInt(id))
      .then(setDados)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/gestao/clientes/${id}`} className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-gray-900">Contestações</h1>
          {dados && (
            <p className="text-sm text-gray-500">
              {dados.nome} · {dados.total} contestação(ões)
            </p>
          )}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12 text-gray-400 text-sm">Carregando...</div>
      ) : !dados || dados.contestacoes.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-100 p-8 text-center">
          <FileText className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Nenhuma contestação registrada para este cliente.</p>
          <Link
            href="/contestacoes"
            className="inline-block mt-3 text-sm text-[#1e3a8a] hover:text-[#f59e0b] transition-colors"
          >
            Ir para o módulo de contestações →
          </Link>
        </div>
      ) : (
        <div className="relative">
          {/* Linha vertical da timeline */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-100" />
          <div className="space-y-4">
            {dados.contestacoes.map((c) => (
              <TimelineItem key={c.id} c={c} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


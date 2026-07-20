'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Download, Plus, RefreshCw } from 'lucide-react';
import { abusividadeApi, AbusividadeHistoricoItem } from '@/lib/api/abusividade';

const STATUS_BADGE: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-600',
  ready: 'bg-green-100 text-green-700',
  error: 'bg-red-100 text-red-700',
};

const STATUS_LABEL: Record<string, string> = {
  pending: 'Pendente',
  ready: 'Concluído',
  error: 'Erro',
};

function formatDate(iso: string): string {
  if (!iso) return '-';
  try {
    return new Date(iso).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export default function AbusividadeHistoricoPage() {
  const params = useParams();
  const router = useRouter();
  const clienteId = Number(params.id);

  const [historico, setHistorico] = useState<AbusividadeHistoricoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const carregar = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await abusividadeApi.getHistorico(clienteId);
      setHistorico(data);
    } catch {
      setError('Erro ao carregar histórico de análises de abusividade.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
  }, [clienteId]);

  return (
    <div className="max-w-5xl mx-auto pb-10 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 border-b pb-4">
        <Link href={`/gestao/clientes/${clienteId}`} className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-gray-800">Histórico de Abusividade</h1>
          <p className="text-sm text-gray-500">Cliente #{clienteId}</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={carregar}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border rounded hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
          <button
            onClick={() =>
              window.open(
                `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/api/v1/abusividade/historico/${clienteId}/exportar-csv`,
                '_blank',
              )
            }
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-green-600 text-green-700 rounded hover:bg-green-50"
          >
            <Download className="w-3.5 h-3.5" />
            Exportar CSV
          </button>
          <button
            onClick={() => router.push('/abusividade')}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Nova Análise
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>
      )}

      {/* Tabela de histórico */}
      <div className="bg-white border rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50">
          <h2 className="font-semibold text-gray-700 text-sm">Análises Realizadas</h2>
        </div>
        {loading ? (
          <div className="py-8 text-center text-gray-400 text-sm">Carregando...</div>
        ) : historico.length === 0 ? (
          <div className="py-8 text-center text-gray-400 text-sm">
            Nenhuma análise de abusividade encontrada para este cliente.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                {['Data', 'Processamento', 'Arquivo', 'Status', 'Erro'].map((h) => (
                  <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {historico.map((item) => (
                <tr key={item.id} className="border-b hover:bg-gray-50">
                  <td className="px-3 py-2 text-gray-600 whitespace-nowrap">
                    {formatDate(item.created_at)}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-gray-700">
                    {item.processamento_id}
                  </td>
                  <td className="px-3 py-2 text-gray-500 text-xs max-w-[200px] truncate">
                    {item.nome_arquivo ?? '-'}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_BADGE[item.status] ?? 'bg-gray-100 text-gray-600'}`}
                    >
                      {STATUS_LABEL[item.status] ?? item.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-red-500 text-xs max-w-[200px] truncate">
                    {item.error_message ?? '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}


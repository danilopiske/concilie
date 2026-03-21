'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Download, TrendingUp, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { divergenciasApi, type DivergenciasRelatorio } from '@/lib/api/divergencias';

export default function DivergenciasClientePage() {
  const { id } = useParams<{ id: string }>();
  const clienteId = parseInt(id);
  const [dados, setDados] = useState<DivergenciasRelatorio | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    if (!clienteId) return;
    divergenciasApi
      .getRelatorio(clienteId)
      .then(setDados)
      .catch(() => setErro(true))
      .finally(() => setLoading(false));
  }, [clienteId]);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href={`/gestao/clientes/${id}`}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </Link>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-gray-900">Relatório de Divergências</h1>
          {dados && <p className="text-sm text-gray-500">{dados.nome}</p>}
        </div>
        {dados && dados.divergencias.length > 0 && (
          <a
            href={divergenciasApi.exportarCsvUrl(clienteId)}
            download
            className="flex items-center gap-2 px-4 py-2 text-sm border border-[#1e3a8a] text-[#1e3a8a] rounded-lg hover:bg-blue-50 transition-colors"
          >
            <Download className="w-4 h-4" />
            Exportar CSV
          </a>
        )}
      </div>

      {/* States */}
      {loading && (
        <div className="text-center py-12 text-gray-400 text-sm">Carregando...</div>
      )}

      {!loading && erro && (
        <div className="text-center py-12 text-red-400 text-sm">
          Erro ao carregar relatório.
        </div>
      )}

      {!loading && !erro && dados && (
        <>
          {/* Nota informativa (ex: sem EC vinculado) */}
          {dados.nota && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-800">
              {dados.nota}
            </div>
          )}

          {/* KPIs */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-xl border border-gray-100 p-5 flex items-center gap-4">
              {dados.total_divergencias > 0 ? (
                <AlertTriangle className="w-8 h-8 text-amber-500 shrink-0" />
              ) : (
                <CheckCircle2 className="w-8 h-8 text-green-500 shrink-0" />
              )}
              <div>
                <p className="text-3xl font-bold text-gray-900">{dados.total_divergencias}</p>
                <p className="text-sm text-gray-500">Divergências encontradas</p>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-100 p-5 flex items-center gap-4">
              <TrendingUp className="w-8 h-8 text-[#1e3a8a] shrink-0" />
              <div>
                <p className="text-3xl font-bold text-gray-900">
                  {dados.divergencias.length > 0
                    ? `${Math.max(...dados.divergencias.map((d) => d.diferenca_pct)).toFixed(2)}%`
                    : '0%'}
                </p>
                <p className="text-sm text-gray-500">Maior divergência</p>
              </div>
            </div>
          </div>

          {/* Tabela ou estado vazio */}
          {dados.divergencias.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-100 p-8 text-center">
              <CheckCircle2 className="w-10 h-10 text-green-400 mx-auto mb-3" />
              <p className="text-gray-500 font-medium">Nenhuma divergência encontrada</p>
              <p className="text-sm text-gray-400 mt-1">
                As taxas cobradas estão dentro do contratado.
              </p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left text-xs font-semibold text-gray-500 px-4 py-3">
                      Bandeira
                    </th>
                    <th className="text-left text-xs font-semibold text-gray-500 px-4 py-3">
                      Modalidade
                    </th>
                    <th className="text-right text-xs font-semibold text-gray-500 px-4 py-3">
                      Contratada
                    </th>
                    <th className="text-right text-xs font-semibold text-gray-500 px-4 py-3">
                      Cobrada
                    </th>
                    <th className="text-right text-xs font-semibold text-gray-500 px-4 py-3">
                      Diferença
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {dados.divergencias.map((d, i) => (
                    <tr key={i} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 text-sm text-gray-800">{d.bandeira}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{d.modalidade}</td>
                      <td className="px-4 py-3 text-sm text-gray-600 text-right">
                        {d.taxa_contratada.toFixed(2)}%
                      </td>
                      <td className="px-4 py-3 text-sm text-right">
                        <span className="text-red-600 font-medium">
                          {d.taxa_cobrada.toFixed(2)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="px-2 py-0.5 bg-red-50 text-red-700 text-xs font-medium rounded-full">
                          +{d.diferenca_pct.toFixed(2)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

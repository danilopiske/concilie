'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, AlertTriangle, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { taxasComparativoApi, type ComparativoResponse, type ComparativoItem } from '@/lib/api/taxasComparativo';

const STATUS_BADGE: Record<ComparativoItem['status'], string> = {
  ok: 'bg-green-100 text-green-700',
  divergente: 'bg-yellow-100 text-yellow-700',
  critico: 'bg-red-100 text-red-700',
};

const STATUS_LABEL: Record<ComparativoItem['status'], string> = {
  ok: 'OK',
  divergente: 'Divergente',
  critico: 'Crítico',
};

export default function TaxasComparativoPage() {
  const params = useParams();
  const clienteId = Number(params.id);

  const [dados, setDados] = useState<ComparativoResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const carregar = async () => {
    setLoading(true);
    setErro(null);
    try {
      const data = await taxasComparativoApi.listar(clienteId);
      setDados(data);
    } catch {
      setErro('Erro ao carregar comparativo de taxas.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
  }, [clienteId]);

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href={`/gestao/clientes/${clienteId}`}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </Link>
        <div className="flex-1">
          <h1 className="text-xl font-bold text-gray-900">Comparativo de Taxas</h1>
          <p className="text-sm text-gray-500">Taxas contratadas vs média cobrada em todos os processamentos</p>
        </div>
        <button
          onClick={carregar}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50 text-gray-600 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Atualizar
        </button>
      </div>

      {/* Resumo */}
      {dados && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white border rounded-xl p-4 flex items-center gap-3">
            <div className="p-2 bg-red-50 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{dados.total_critico}</p>
              <p className="text-xs text-gray-500">Crítico (&gt;0,5pp acima)</p>
            </div>
          </div>
          <div className="bg-white border rounded-xl p-4 flex items-center gap-3">
            <div className="p-2 bg-yellow-50 rounded-lg">
              <AlertCircle className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{dados.total_divergente}</p>
              <p className="text-xs text-gray-500">Divergente (até 0,5pp)</p>
            </div>
          </div>
          <div className="bg-white border rounded-xl p-4 flex items-center gap-3">
            <div className="p-2 bg-green-50 rounded-lg">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{dados.total_ok}</p>
              <p className="text-xs text-gray-500">OK (dentro do contratado)</p>
            </div>
          </div>
        </div>
      )}

      {/* Tabela */}
      <div className="bg-white border rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50">
          <h2 className="font-semibold text-gray-700 text-sm">Detalhamento por Bandeira / Modalidade</h2>
        </div>

        {loading && (
          <div className="py-12 text-center text-gray-400 text-sm">Carregando...</div>
        )}

        {erro && (
          <div className="p-4 text-sm text-red-600 bg-red-50">{erro}</div>
        )}

        {!loading && !erro && dados && dados.itens.length === 0 && (
          <div className="py-12 text-center text-gray-400 text-sm">
            Nenhuma taxa contratada cadastrada ou sem processamentos para este cliente.
          </div>
        )}

        {!loading && !erro && dados && dados.itens.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                {['Status', 'Bandeira', 'Modalidade', 'Taxa Contratada %', 'Taxa Cobrada %', 'Diferença (pp)', 'Transações'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {dados.itens.map((item, i) => (
                <tr key={i} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[item.status]}`}>
                      {STATUS_LABEL[item.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">{item.bandeira}</td>
                  <td className="px-4 py-3 text-gray-700">{item.modalidade}</td>
                  <td className="px-4 py-3 text-gray-700">{item.taxa_contratada.toFixed(2)}%</td>
                  <td className="px-4 py-3 text-gray-700">{item.taxa_media_cobrada.toFixed(2)}%</td>
                  <td className={`px-4 py-3 font-semibold ${item.diferenca > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {item.diferenca > 0 ? '+' : ''}{item.diferenca.toFixed(4)}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{item.quantidade_transacoes.toLocaleString('pt-BR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Legenda */}
      <div className="text-xs text-gray-400 space-y-1">
        <p><span className="font-medium text-red-500">Crítico:</span> taxa cobrada excede a contratada em mais de 0,5 pontos percentuais.</p>
        <p><span className="font-medium text-yellow-500">Divergente:</span> taxa cobrada excede a contratada em até 0,5 pontos percentuais.</p>
        <p><span className="font-medium text-green-500">OK:</span> taxa cobrada está dentro ou abaixo da taxa contratada.</p>
      </div>
    </div>
  );
}


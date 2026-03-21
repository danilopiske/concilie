'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, BarChart3, FileText, GitCompare } from 'lucide-react';
import { ClienteResumoPanel } from '@/components/gestao/ClienteResumoPanel';

export default function ClienteDetalhePage() {
  const params = useParams();
  const clienteId = Number(params.id);

  return (
    <div className="max-w-4xl mx-auto pb-10 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 border-b pb-4">
        <Link href="/gestao/clientes" className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-gray-800">Resumo do Cliente</h1>
          <p className="text-sm text-gray-500">Cliente #{clienteId}</p>
        </div>
      </div>

      {/* Links de ações rápidas */}
      <div className="flex flex-wrap gap-3">
        <Link
          href={`/gestao/clientes/${clienteId}/taxas-contratadas`}
          className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 text-gray-700"
        >
          <BarChart3 className="w-4 h-4 text-blue-500" />
          Taxas Contratadas
        </Link>
        <Link
          href={`/gestao/clientes/${clienteId}/taxas-comparativo`}
          className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 text-gray-700"
        >
          <GitCompare className="w-4 h-4 text-purple-500" />
          Comparativo de Taxas
        </Link>
        <Link
          href={`/clientes/${clienteId}/extratos`}
          className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 text-gray-700"
        >
          <FileText className="w-4 h-4 text-green-500" />
          Extratos
        </Link>
      </div>

      {/* Painel de resumo executivo */}
      <ClienteResumoPanel clienteId={clienteId} />
    </div>
  );
}

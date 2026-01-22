/**
 * Página de Gestão de Termos Filtráveis
 */

'use client';

import { useState } from 'react';
import { TermosFiltravelisForm } from '@/components/gestao/TermosFiltravelisForm';
import { Breadcrumb } from '@/components/layout';
import { useClientes } from '@/lib/hooks/useClientes';
import { useECs } from '@/lib/hooks/useECs';
import { useContextos } from '@/lib/hooks/useContextos';

export default function GestaoTermosPage() {
  const [clienteSelecionado, setClienteSelecionado] = useState<number | null>(null);
  const [ecSelecionado, setEcSelecionado] = useState<string>('');
  const [contextoSelecionado, setContextoSelecionado] = useState('padrao');

  const { clientes, loading: loadingClientes } = useClientes();
  const { ecs, loading: loadingECs } = useECs(clienteSelecionado);
  const { contextos, loading: loadingContextos } = useContextos();

  const handleClienteChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const clienteId = e.target.value ? parseInt(e.target.value) : null;
    setClienteSelecionado(clienteId);
    setEcSelecionado(''); // Resetar EC ao trocar cliente
  };

  const handleEcChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setEcSelecionado(e.target.value);
  };

  const handleContextoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setContextoSelecionado(e.target.value);
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: 'Gestão', href: '/gestao' },
          { label: 'Termos Filtráveis' },
        ]}
      />

      {/* Cabeçalho */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Gestão de Termos Filtráveis</h1>
        <p className="mt-2 text-sm text-gray-600">
          Configure termos que serão usados para filtrar transações automaticamente
        </p>
      </div>

      {/* Seletores */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Cliente */}
          <div>
            <label htmlFor="cliente" className="block text-sm font-medium text-gray-700 mb-1">
              Cliente
            </label>
            <select
              id="cliente"
              value={clienteSelecionado || ''}
              onChange={handleClienteChange}
              disabled={loadingClientes}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Selecione um cliente</option>
              {clientes.map((cliente) => (
                <option key={cliente.cliente_id} value={cliente.cliente_id}>
                  {cliente.cliente_id} - {cliente.nome_fantasia}
                </option>
              ))}
            </select>
          </div>

          {/* EC */}
          <div>
            <label htmlFor="ec" className="block text-sm font-medium text-gray-700 mb-1">
              Estabelecimento (EC)
            </label>
            <select
              id="ec"
              value={ecSelecionado}
              onChange={handleEcChange}
              disabled={!clienteSelecionado || loadingECs}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Selecione um EC</option>
              {ecs.map((ec) => (
                <option key={ec} value={ec}>
                  {ec}
                </option>
              ))}
            </select>
          </div>

          {/* Contexto */}
          <div>
            <label htmlFor="contexto" className="block text-sm font-medium text-gray-700 mb-1">
              Contexto
            </label>
            <select
              id="contexto"
              value={contextoSelecionado}
              onChange={handleContextoChange}
              disabled={loadingContextos}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {contextos.map((ctx) => (
                <option key={ctx.nome} value={ctx.nome}>
                  {ctx.nome}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Formulário de Termos */}
      {ecSelecionado ? (
        <TermosFiltravelisForm
          ec={ecSelecionado}
          contexto={contextoSelecionado}
        />
      ) : (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <div className="text-gray-400 mb-4">
            <svg
              className="mx-auto h-12 w-12"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Nenhum EC selecionado
          </h3>
          <p className="text-gray-500">
            Selecione um Cliente e um EC acima para gerenciar os termos filtráveis
          </p>
        </div>
      )}
    </div>
  );
}

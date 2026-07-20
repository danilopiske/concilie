/**
 * Página de Gestão de Termos Filtráveis
 */

'use client';

import { useState } from 'react';
import { TermosFiltravelisForm } from '@/components/gestao/TermosFiltravelisForm';
import { Breadcrumb } from '@/components/layout';
import { Select } from '@/components/ui/Select';
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
    const value = e.target.value;
    const clienteId = value ? parseInt(value) : null;
    setClienteSelecionado(clienteId);
    setEcSelecionado(''); // Resetar EC ao trocar cliente
  };

  const handleEcChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setEcSelecionado(e.target.value);
  };

  const handleContextoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setContextoSelecionado(e.target.value);
  };

  const clienteOptions = clientes.map(cliente => ({
    value: cliente.cliente_id,
    label: `${cliente.cliente_id} - ${cliente.nome_fantasia}`
  }));

  const ecOptions = ecs.map(ec => ({
    value: ec,
    label: ec
  }));

  const contextoOptions = contextos.map(ctx => ({
    value: ctx.nome,
    label: ctx.nome
  }));

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
            <Select
              id="cliente"
              label="Cliente"
              value={clienteSelecionado || ''}
              onChange={handleClienteChange}
              disabled={loadingClientes}
              options={clienteOptions}
              placeholder="Selecione um cliente"
            />
          </div>

          {/* EC */}
          <div>
            <Select
              id="ec"
              label="Estabelecimento (EC)"
              value={ecSelecionado}
              onChange={handleEcChange}
              disabled={!clienteSelecionado || loadingECs}
              options={ecOptions}
              placeholder="Selecione um EC"
            />
          </div>

          {/* Contexto */}
          <div>
            <Select
              id="contexto"
              label="Contexto"
              value={contextoSelecionado}
              onChange={handleContextoChange}
              disabled={loadingContextos}
              options={contextoOptions}
            />
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

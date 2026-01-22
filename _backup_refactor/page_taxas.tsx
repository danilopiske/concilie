/**
 * Página de Gestão de Taxas
 * Configuração de taxas por EC, bandeira e forma de pagamento
 */

'use client';

import { useState } from 'react';
import { Copy } from 'lucide-react';
import { Breadcrumb } from '@/components/layout';
import { TaxasForm } from '@/components/gestao/TaxasForm';
import { CopiarTaxasModal } from '@/components/gestao/CopiarTaxasModal';
import { useClientes } from '@/lib/hooks/useClientes';
import { useECs } from '@/lib/hooks/useECs';
import { useContextos } from '@/lib/hooks/useContextos';
import { useTodosECs } from '@/lib/hooks/useTodosECs';
import { Alert } from '@/components/ui/Alert';

export default function GestaoTaxasPage() {
  const [clienteSelecionado, setClienteSelecionado] = useState<number | null>(null);
  const [ecSelecionado, setEcSelecionado] = useState<string>('');
  const [contextoSelecionado, setContextoSelecionado] = useState('padrao');
  const [modalCopiarAberto, setModalCopiarAberto] = useState(false);

  const { clientes, loading: loadingClientes } = useClientes();
  const { ecs, loading: loadingECs } = useECs(clienteSelecionado);
  const { contextos, loading: loadingContextos } = useContextos();
  const { todosECs, loading: loadingTodosECs, error: errorTodosECs } = useTodosECs();

  console.log('📄 [GestaoTaxasPage] Estado todosECs:', {
    todosECs_length: todosECs?.length || 0,
    todosECs_sample: todosECs?.slice(0, 3),
    loading: loadingTodosECs,
    error: errorTodosECs,
  });

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
          { label: 'Taxas' },
        ]}
      />

      {/* Cabeçalho */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Gestão de Taxas</h1>
            <p className="mt-2 text-sm text-gray-600">
              Configure taxas por EC, bandeira e forma de pagamento. Taxas genéricas aplicam-se a todas as bandeiras.
            </p>
          </div>
          <button
            onClick={() => setModalCopiarAberto(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 shadow-sm"
          >
            <Copy className="w-4 h-4" />
            Copiar Taxas
          </button>
        </div>
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            >
              {contextos.map((ctx) => (
                <option key={ctx.id} value={ctx.nome}>
                  {ctx.nome}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Mensagem informativa */}
        {!ecSelecionado && (
          <Alert variant="info" className="mt-4">
            Selecione um cliente e um EC para gerenciar as taxas
          </Alert>
        )}
      </div>

      {/* Formulário de Taxas */}
      {ecSelecionado && (
        <TaxasForm ec={ecSelecionado} contexto={contextoSelecionado} />
      )}

      {/* Modal Copiar Taxas */}
      <CopiarTaxasModal
        isOpen={modalCopiarAberto}
        onClose={() => setModalCopiarAberto(false)}
        contextoAtual={contextoSelecionado}
        todosECs={todosECs}
        onCopiaCompleta={() => {
          // Atualizar lista de taxas se estiver visualizando um EC
          if (ecSelecionado) {
            window.location.reload(); // Força reload para atualizar TaxasForm
          }
        }}
      />
    </div>
  );
}

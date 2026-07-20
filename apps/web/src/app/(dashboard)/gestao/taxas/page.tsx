/**
 * Página de Gestão de Taxas
 * Configuração de taxas por EC, bandeira e forma de pagamento
 */

'use client';

import { useState } from 'react';
import { Copy } from 'lucide-react';
import { Breadcrumb } from '@/components/layout';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { TaxasForm } from '@/components/gestao/TaxasForm';
import { CopiarTaxasModal } from '@/components/gestao/CopiarTaxasModal';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
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
          <Button onClick={() => setModalCopiarAberto(true)} className="flex items-center gap-2">
            <Copy className="w-4 h-4" />
            Copiar Taxas
          </Button>
        </div>
      </div>

      {errorTodosECs && (
        <div className="mb-4">
          <ErrorMessage message="Erro ao carregar lista de ECs para cópia de taxas." />
        </div>
      )}

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

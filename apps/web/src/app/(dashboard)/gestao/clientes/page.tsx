/**
 * Página de Gestão de Clientes
 * Conversão do módulo ui_gestao.py (gestão de clientes)
 */
'use client';

import { useState } from 'react';
import { useClientes } from '@/lib/hooks/useClientes';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { Breadcrumb } from '@/components/layout';
import { ClientesTable } from '@/components/gestao/ClientesTable';
import { ClienteFormModal } from '@/components/gestao/ClienteFormModal';
import { ECsModal } from '@/components/gestao/ECsModal';
import { Cliente } from '@/lib/types/gestao';

export default function ClientesPage() {
  const { clientes, loading, error, deletarCliente, refetch } = useClientes();
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isECsModalOpen, setIsECsModalOpen] = useState(false);
  const [selectedCliente, setSelectedCliente] = useState<Cliente | null>(null);
  const [clienteParaExcluir, setClienteParaExcluir] = useState<number | null>(null);
  const [selectedClienteForECs, setSelectedClienteForECs] = useState<{
    id: number;
    nome: string;
  } | null>(null);

  const handleEdit = (cliente: Cliente) => {
    setSelectedCliente(cliente);
    setIsFormModalOpen(true);
  };

  const handleDeleteClick = (clienteId: number) => {
    setClienteParaExcluir(clienteId);
  };

  const handleConfirmDelete = async () => {
    if (!clienteParaExcluir) return;

    try {
      setDeleteError(null);
      await deletarCliente(clienteParaExcluir);
      setClienteParaExcluir(null);
    } catch (err: any) {
      setDeleteError(err.message);
      setClienteParaExcluir(null);
    }
  };

  const handleViewECs = (clienteId: number) => {
    const cliente = clientes.find(c => c.cliente_id === clienteId);
    if (cliente) {
      setSelectedClienteForECs({
        id: clienteId,
        nome: cliente.razao_social || cliente.nome_fantasia || `Cliente ${clienteId}`,
      });
      setIsECsModalOpen(true);
    }
  };

  const handleNovoCliente = () => {
    setSelectedCliente(null);
    setIsFormModalOpen(true);
  };

  const handleCloseFormModal = () => {
    setIsFormModalOpen(false);
    setSelectedCliente(null);
  };

  const handleSaved = () => {
    refetch();
  };

  return (
    <div className="max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: 'Gestão', href: '/gestao' },
          { label: 'Clientes' },
        ]}
      />

      {/* Cabeçalho */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Gestão de Clientes
        </h1>
        <p className="text-gray-600">
          Gerencie clientes, endereços, contatos e estabelecimentos comerciais
        </p>
      </div>

      {/* Mensagens de Erro */}
      {error && (
        <div className="mb-6">
          <ErrorMessage message={error} />
        </div>
      )}

      {deleteError && (
        <div className="mb-6">
          <ErrorMessage message={deleteError} />
        </div>
      )}

      {/* Card Principal */}
      <Card
        title="Clientes Cadastrados"
        actions={
          <Button onClick={handleNovoCliente}>
            + Novo Cliente
          </Button>
        }
      >
        {loading ? (
          <Loading message="Carregando clientes..." />
        ) : (
          <ClientesTable
            clientes={clientes}
            onEdit={handleEdit}
            onDelete={handleDeleteClick}
            onViewECs={handleViewECs}
          />
        )}
      </Card>

      {/* Informações */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-700">
          💡 <strong>Total de clientes:</strong> {clientes.length}
        </p>
      </div>

      {/* Modais */}
      <ClienteFormModal
        isOpen={isFormModalOpen}
        onClose={handleCloseFormModal}
        cliente={selectedCliente}
        onSaved={handleSaved}
      />

      <ECsModal
        isOpen={isECsModalOpen}
        onClose={() => setIsECsModalOpen(false)}
        clienteId={selectedClienteForECs?.id || null}
        clienteNome={selectedClienteForECs?.nome || ''}
      />

      <ConfirmDialog
        isOpen={!!clienteParaExcluir}
        onClose={() => setClienteParaExcluir(null)}
        onConfirm={handleConfirmDelete}
        title="Excluir Cliente"
        message="Tem certeza que deseja excluir este cliente? Esta ação não pode ser desfeita."
        confirmText="Excluir"
        variant="danger"
        loading={loading}
      />
    </div>
  );
}

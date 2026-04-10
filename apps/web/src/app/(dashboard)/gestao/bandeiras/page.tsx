/**
 * Página de Gestão de Bandeiras
 * Migrado de modules/ui_gestao.py - tela de bandeiras
 * Refatorado para seguir UI Design System
 */
'use client';

import { useState } from 'react';
import { useBandeiras } from '@/lib/hooks/useBandeiras';
import { Table, Badge, Button, Alert, ConfirmDialog, Card, TableColumn } from '@/components/ui';
import { Loading } from '@/components/shared/Loading';
import { Breadcrumb } from '@/components/layout';
import { BandeiraFormModal } from '@/components/gestao/BandeiraFormModal';
import { gestaoApi } from '@/lib/api/gestao';
import { BandeiraDisponivel } from '@/lib/types/gestao';

export default function BandeirasPage() {
  const { bandeiras, loading, error, refetch } = useBandeiras();
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<BandeiraDisponivel | null>(null);
  const [deleting, setDeleting] = useState(false);

  const handleNovaBandeira = () => {
    setIsFormModalOpen(true);
  };

  const handleDeleteClick = (bandeira: BandeiraDisponivel) => {
    setDeleteError(null);
    setConfirmDelete(bandeira);
  };

  const handleConfirmDelete = async () => {
    if (!confirmDelete) return;

    try {
      setDeleting(true);
      setDeleteError(null);
      await gestaoApi.bandeiras.deletar(confirmDelete.id);
      setConfirmDelete(null);
      refetch();
    } catch (err: unknown) {
      setDeleteError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao excluir bandeira');
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  const handleSaved = () => {
    refetch();
  };

  // Definição das colunas da tabela
  const columns: TableColumn<BandeiraDisponivel>[] = [
    {
      key: 'id',
      label: 'ID',
      width: '80px',
    },
    {
      key: 'nome',
      label: 'Nome',
      sortable: true,
    },
    {
      key: 'padrao',
      label: 'Padrão',
      width: '120px',
      render: (value) => (
        <Badge variant={value ? 'success' : 'default'}>
          {value ? 'Sim' : 'Não'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: 'Ações',
      width: '100px',
      render: (_, bandeira) => (
        <Button
          variant="danger"
          size="sm"
          onClick={() => handleDeleteClick(bandeira)}
        >
          Excluir
        </Button>
      ),
    },
  ];

  if (loading) return <Loading />;

  if (error) {
    return (
      <div>
        <Alert variant="error">{error}</Alert>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: 'Gestão', href: '/gestao' },
          { label: 'Bandeiras' },
        ]}
      />

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Gestão de Bandeiras
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Configure as bandeiras de cartão disponíveis no sistema
          </p>
        </div>
        <Button variant="primary" onClick={handleNovaBandeira}>
          Nova Bandeira
        </Button>
      </div>

      {/* Error Alert */}
      {deleteError && (
        <Alert variant="error" onClose={() => setDeleteError(null)}>
          {deleteError}
        </Alert>
      )}

      {/* Info Alert */}
      <Alert variant="info">
        Bandeiras marcadas como &quot;Padrão&quot; serão selecionadas automaticamente para novos clientes.
      </Alert>

      {/* Table */}
      <Card>
        <Table
          variant="simple"
          columns={columns}
          data={bandeiras}
          emptyMessage="Nenhuma bandeira cadastrada"
        />
      </Card>

      {/* Modals */}
      <BandeiraFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        onSaved={handleSaved}
      />

      <ConfirmDialog
        isOpen={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleConfirmDelete}
        title="Confirmar Exclusão"
        message={`Deseja realmente excluir a bandeira "${confirmDelete?.nome}"? Esta ação não pode ser desfeita.`}
        confirmText="Excluir"
        cancelText="Cancelar"
        variant="danger"
        loading={deleting}
      />
    </div>
  );
}

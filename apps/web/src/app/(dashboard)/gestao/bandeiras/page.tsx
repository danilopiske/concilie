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
  const [editingBandeira, setEditingBandeira] = useState<BandeiraDisponivel | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<BandeiraDisponivel | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Seleção em massa
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [confirmBulkDelete, setConfirmBulkDelete] = useState(false);

  const allSelected = bandeiras.length > 0 && selectedIds.size === bandeiras.length;
  const someSelected = selectedIds.size > 0;

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(bandeiras.map(b => b.id)));
    }
  };

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleNovaBandeira = () => {
    setEditingBandeira(null);
    setIsFormModalOpen(true);
  };

  const handleEditClick = (bandeira: BandeiraDisponivel) => {
    setEditingBandeira(bandeira);
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
      setSelectedIds(prev => { const n = new Set(prev); n.delete(confirmDelete.id); return n; });
      refetch();
    } catch (err: unknown) {
      setDeleteError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao excluir bandeira');
    } finally {
      setDeleting(false);
    }
  };

  const handleBulkDelete = async () => {
    try {
      setBulkDeleting(true);
      setDeleteError(null);
      await Promise.all([...selectedIds].map(id => gestaoApi.bandeiras.deletar(id)));
      setSelectedIds(new Set());
      setConfirmBulkDelete(false);
      refetch();
    } catch (err: unknown) {
      setDeleteError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao excluir bandeiras');
    } finally {
      setBulkDeleting(false);
    }
  };

  const columns: TableColumn<BandeiraDisponivel>[] = [
    {
      key: 'id' as keyof BandeiraDisponivel,
      label: (
        <input
          type="checkbox"
          checked={allSelected}
          onChange={toggleSelectAll}
          className="h-4 w-4 text-blue-600 rounded"
        />
      ) as unknown as string,
      width: '48px',
      render: (_, bandeira) => (
        <input
          type="checkbox"
          checked={selectedIds.has(bandeira.id)}
          onChange={() => toggleSelect(bandeira.id)}
          className="h-4 w-4 text-blue-600 rounded"
          onClick={e => e.stopPropagation()}
        />
      ),
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
      width: '160px',
      render: (_, bandeira) => (
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => handleEditClick(bandeira)}>
            Editar
          </Button>
          <Button variant="danger" size="sm" onClick={() => handleDeleteClick(bandeira)}>
            Excluir
          </Button>
        </div>
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
      <Breadcrumb
        items={[
          { label: 'Gestão', href: '/gestao' },
          { label: 'Bandeiras' },
        ]}
      />

      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestão de Bandeiras</h1>
          <p className="text-sm text-gray-600 mt-1">
            Configure as bandeiras de cartão disponíveis no sistema
          </p>
        </div>
        <Button variant="primary" onClick={handleNovaBandeira}>
          Nova Bandeira
        </Button>
      </div>

      {deleteError && (
        <Alert variant="error" onClose={() => setDeleteError(null)}>
          {deleteError}
        </Alert>
      )}

      <Alert variant="info">
        Bandeiras marcadas como &quot;Padrão&quot; serão selecionadas automaticamente para novos clientes.
      </Alert>

      {/* Barra de ações em massa */}
      {someSelected && (
        <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
          <span className="text-sm font-medium text-blue-800">
            {selectedIds.size} {selectedIds.size === 1 ? 'bandeira selecionada' : 'bandeiras selecionadas'}
          </span>
          <Button
            variant="danger"
            size="sm"
            onClick={() => setConfirmBulkDelete(true)}
            disabled={bulkDeleting}
          >
            Excluir selecionadas
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setSelectedIds(new Set())}
          >
            Cancelar seleção
          </Button>
        </div>
      )}

      <Card>
        <Table
          variant="simple"
          columns={columns}
          data={bandeiras}
          emptyMessage="Nenhuma bandeira cadastrada"
        />
      </Card>

      <BandeiraFormModal
        isOpen={isFormModalOpen}
        onClose={() => { setIsFormModalOpen(false); setEditingBandeira(null); }}
        onSaved={() => refetch()}
        bandeira={editingBandeira}
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

      <ConfirmDialog
        isOpen={confirmBulkDelete}
        onClose={() => setConfirmBulkDelete(false)}
        onConfirm={handleBulkDelete}
        title="Confirmar Exclusão em Massa"
        message={`Deseja realmente excluir ${selectedIds.size} bandeiras? Esta ação não pode ser desfeita.`}
        confirmText="Excluir todas"
        cancelText="Cancelar"
        variant="danger"
        loading={bulkDeleting}
      />
    </div>
  );
}

'use client';

import { useState } from 'react';
import { useContextos } from '@/lib/hooks/useContextos';
import { Table, Badge, Button, Checkbox, Alert, ConfirmDialog, Card, TableColumn } from '@/components/ui';
import { Loading } from '@/components/shared/Loading';
import { Breadcrumb } from '@/components/layout';
import { ContextoFormModal } from '@/components/gestao/ContextoFormModal';
import { gestaoApi } from '@/lib/api/gestao';
import { Contexto } from '@/lib/types/gestao';

export default function ContextosPage() {
  const [incluirInativos, setIncluirInativos] = useState(false);
  const { contextos, loading, error, refetch } = useContextos(incluirInativos);
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [selectedContexto, setSelectedContexto] = useState<Contexto | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Contexto | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Seleção em massa
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [bulkToggling, setBulkToggling] = useState(false);
  const [confirmBulkDelete, setConfirmBulkDelete] = useState(false);

  const allSelected = contextos.length > 0 && selectedIds.size === contextos.length;
  const someSelected = selectedIds.size > 0;

  const toggleSelectAll = () => {
    if (allSelected) setSelectedIds(new Set());
    else setSelectedIds(new Set(contextos.map(c => c.id)));
  };

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleNovoContexto = () => {
    setSelectedContexto(null);
    setIsFormModalOpen(true);
  };

  const handleEditContexto = (contexto: Contexto) => {
    setSelectedContexto(contexto);
    setIsFormModalOpen(true);
  };

  const handleDeleteClick = (contexto: Contexto) => {
    setDeleteError(null);
    setConfirmDelete(contexto);
  };

  const handleConfirmDelete = async () => {
    if (!confirmDelete) return;
    try {
      setDeleting(true);
      setDeleteError(null);
      await gestaoApi.contextos.deletar(confirmDelete.id);
      setConfirmDelete(null);
      setSelectedIds(prev => { const n = new Set(prev); n.delete(confirmDelete.id); return n; });
      refetch();
    } catch (err: unknown) {
      setDeleteError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao excluir contexto');
    } finally {
      setDeleting(false);
    }
  };

  const handleBulkDelete = async () => {
    try {
      setBulkDeleting(true);
      setDeleteError(null);
      await Promise.all([...selectedIds].map(id => gestaoApi.contextos.deletar(id)));
      setSelectedIds(new Set());
      setConfirmBulkDelete(false);
      refetch();
    } catch (err: unknown) {
      setDeleteError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao excluir contextos');
    } finally {
      setBulkDeleting(false);
    }
  };

  const handleBulkToggleAtivo = async (ativo: boolean) => {
    try {
      setBulkToggling(true);
      setDeleteError(null);
      await Promise.all([...selectedIds].map(id => gestaoApi.contextos.atualizar(id, { ativo })));
      setSelectedIds(new Set());
      refetch();
    } catch (err: unknown) {
      setDeleteError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao atualizar contextos');
    } finally {
      setBulkToggling(false);
    }
  };

  const columns: TableColumn<Contexto>[] = [
    {
      key: 'id' as keyof Contexto,
      label: (
        <input
          type="checkbox"
          checked={allSelected}
          onChange={toggleSelectAll}
          className="h-4 w-4 text-blue-600 rounded"
        />
      ) as unknown as string,
      width: '48px',
      render: (_, contexto) => (
        <input
          type="checkbox"
          checked={selectedIds.has(contexto.id)}
          onChange={() => toggleSelect(contexto.id)}
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
      key: 'descricao',
      label: 'Descrição',
      render: (value) => value || '-',
    },
    {
      key: 'criado_em',
      label: 'Criado em',
      width: '150px',
      render: (value) => value ? new Date(value).toLocaleDateString('pt-BR') : '-',
    },
    {
      key: 'ativo',
      label: 'Status',
      width: '120px',
      render: (value) => (
        <Badge variant={value ? 'success' : 'error'}>
          {value ? 'Ativo' : 'Inativo'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: 'Ações',
      width: '160px',
      render: (_, contexto) => (
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => handleEditContexto(contexto)}>
            Editar
          </Button>
          <Button variant="danger" size="sm" onClick={() => handleDeleteClick(contexto)}>
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
          { label: 'Contextos' },
        ]}
      />

      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestão de Contextos</h1>
          <p className="text-sm text-gray-600 mt-1">
            Configure os contextos para classificação de transações
          </p>
        </div>
        <div className="flex gap-3 items-center">
          <Checkbox
            label="Incluir inativos"
            checked={incluirInativos}
            onChange={setIncluirInativos}
          />
          <Button variant="primary" onClick={handleNovoContexto}>
            Novo Contexto
          </Button>
        </div>
      </div>

      {deleteError && (
        <Alert variant="error" onClose={() => setDeleteError(null)}>
          {deleteError}
        </Alert>
      )}

      {/* Barra de ações em massa */}
      {someSelected && (
        <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
          <span className="text-sm font-medium text-blue-800">
            {selectedIds.size} {selectedIds.size === 1 ? 'contexto selecionado' : 'contextos selecionados'}
          </span>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleBulkToggleAtivo(true)}
            disabled={bulkToggling}
          >
            Ativar selecionados
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleBulkToggleAtivo(false)}
            disabled={bulkToggling}
          >
            Desativar selecionados
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => setConfirmBulkDelete(true)}
            disabled={bulkDeleting}
          >
            Excluir selecionados
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setSelectedIds(new Set())}>
            Cancelar seleção
          </Button>
        </div>
      )}

      <Card>
        <Table
          variant="simple"
          columns={columns}
          data={contextos}
          emptyMessage="Nenhum contexto encontrado"
        />
      </Card>

      <ContextoFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        contexto={selectedContexto}
        onSaved={() => refetch()}
      />

      <ConfirmDialog
        isOpen={!!confirmDelete}
        onClose={() => setConfirmDelete(null)}
        onConfirm={handleConfirmDelete}
        title="Confirmar Exclusão"
        message={`Deseja realmente excluir o contexto "${confirmDelete?.nome}"? Esta ação não pode ser desfeita.`}
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
        message={`Deseja realmente excluir ${selectedIds.size} contextos? Esta ação não pode ser desfeita.`}
        confirmText="Excluir todos"
        cancelText="Cancelar"
        variant="danger"
        loading={bulkDeleting}
      />
    </div>
  );
}

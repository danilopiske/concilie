/**
 * Página de Gestão de Contextos
 * Migrado de modules/ui_gestao.py - tela de contextos
 * Refatorado para seguir UI Design System
 */
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
      refetch();
    } catch (err: unknown) {
      setDeleteError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao excluir contexto');
      console.error(err);
    } finally {
      setDeleting(false);
    }
  };

  const handleSaved = () => {
    refetch();
  };

  // Definição das colunas da tabela
  const columns: TableColumn<Contexto>[] = [
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
      key: 'atualizado_em',
      label: 'Atualizado em',
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
      width: '150px',
      render: (_, contexto) => (
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleEditContexto(contexto)}
          >
            Editar
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => handleDeleteClick(contexto)}
          >
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
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: 'Gestão', href: '/gestao' },
          { label: 'Contextos' },
        ]}
      />

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Gestão de Contextos
          </h1>
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

      {/* Error Alert */}
      {deleteError && (
        <Alert variant="error" onClose={() => setDeleteError(null)}>
          {deleteError}
        </Alert>
      )}

      {/* Table */}
      <Card>
        <Table
          variant="simple"
          columns={columns}
          data={contextos}
          emptyMessage="Nenhum contexto encontrado"
        />
      </Card>

      {/* Modals */}
      <ContextoFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        contexto={selectedContexto}
        onSaved={handleSaved}
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
    </div>
  );
}

'use client';

import { useState } from 'react';
import { useTermos } from '@/lib/hooks/useTermos';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { Table, TableColumn } from '@/components/ui/Table';
import { Alert } from '@/components/ui/Alert';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { TermoFiltravel } from '@/lib/types/gestao';

interface TermosFiltravelisFormProps {
  ec: string;
  contexto: string;
  onSuccess?: () => void;
}

const TIPOS_TERMO = [
  { value: 'v', label: 'Venda/Lançamento' },
  { value: 'r', label: 'Recebíveis' },
  { value: 'l', label: 'Lançamento (apenas)' },
  { value: 'status', label: 'Status (filtrar por status)' },
];

const TIPO_LABEL: Record<string, string> = {
  v: 'Venda/Lançamento',
  r: 'Recebíveis',
  l: 'Lançamento',
  status: 'Status',
};

export function TermosFiltravelisForm({ ec, contexto, onSuccess }: TermosFiltravelisFormProps) {
  const [novoTermo, setNovoTermo] = useState('');
  const [tipoSelecionado, setTipoSelecionado] = useState('v');
  const [mensagem, setMensagem] = useState<{ tipo: 'success' | 'error'; texto: string } | null>(null);
  const [termoParaExcluir, setTermoParaExcluir] = useState<{ id: number; nome: string } | null>(null);

  // Seleção em massa
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [confirmBulkDelete, setConfirmBulkDelete] = useState(false);

  // Edição inline
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTermo, setEditTermo] = useState('');
  const [editTipo, setEditTipo] = useState('v');
  const [editSaving, setEditSaving] = useState(false);

  const { termos, loading, error, adicionar, atualizar, excluir } = useTermos({ ec, contexto });

  const allSelected = termos.length > 0 && selectedIds.size === termos.length;
  const someSelected = selectedIds.size > 0;

  const toggleSelectAll = () => {
    if (allSelected) setSelectedIds(new Set());
    else setSelectedIds(new Set(termos.map(t => t.id)));
  };

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const showMsg = (tipo: 'success' | 'error', texto: string) => {
    setMensagem({ tipo, texto });
    setTimeout(() => setMensagem(null), 3000);
  };

  const handleAdicionar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!novoTermo.trim()) {
      showMsg('error', 'Digite um termo para adicionar');
      return;
    }
    try {
      await adicionar({ ec, termo: novoTermo.toUpperCase(), tipo: tipoSelecionado, contexto });
      showMsg('success', `Termo "${novoTermo}" adicionado com sucesso!`);
      setNovoTermo('');
      onSuccess?.();
    } catch (err: unknown) {
      showMsg('error', (err as Error).message);
    }
  };

  const handleExcluir = async () => {
    if (!termoParaExcluir) return;
    try {
      await excluir(termoParaExcluir.id);
      showMsg('success', `Termo "${termoParaExcluir.nome}" excluído com sucesso!`);
      setSelectedIds(prev => { const n = new Set(prev); n.delete(termoParaExcluir.id); return n; });
      setTermoParaExcluir(null);
      onSuccess?.();
    } catch (err: unknown) {
      showMsg('error', (err as Error).message);
      setTermoParaExcluir(null);
    }
  };

  const handleBulkDelete = async () => {
    try {
      setBulkDeleting(true);
      await Promise.all([...selectedIds].map(id => excluir(id)));
      showMsg('success', `${selectedIds.size} termos excluídos com sucesso!`);
      setSelectedIds(new Set());
      setConfirmBulkDelete(false);
      onSuccess?.();
    } catch (err: unknown) {
      showMsg('error', (err as Error).message);
    } finally {
      setBulkDeleting(false);
    }
  };

  const handleEditStart = (termo: TermoFiltravel) => {
    setEditingId(termo.id);
    setEditTermo(termo.termo);
    setEditTipo(termo.tipo);
  };

  const handleEditSave = async (id: number) => {
    try {
      setEditSaving(true);
      await atualizar(id, { termo: editTermo.toUpperCase(), tipo: editTipo });
      showMsg('success', 'Termo atualizado com sucesso!');
      setEditingId(null);
    } catch (err: unknown) {
      showMsg('error', (err as Error).message);
    } finally {
      setEditSaving(false);
    }
  };

  const columns: TableColumn<TermoFiltravel>[] = [
    {
      key: 'id' as keyof TermoFiltravel,
      label: (
        <input
          type="checkbox"
          checked={allSelected}
          onChange={toggleSelectAll}
          className="h-4 w-4 text-blue-600 rounded"
        />
      ) as unknown as string,
      width: '48px',
      render: (_, t) => (
        <input
          type="checkbox"
          checked={selectedIds.has(t.id)}
          onChange={() => toggleSelect(t.id)}
          className="h-4 w-4 text-blue-600 rounded"
          onClick={e => e.stopPropagation()}
          disabled={editingId === t.id}
        />
      ),
    },
    {
      key: 'termo',
      label: 'Termo',
      render: (valor, t) =>
        editingId === t.id ? (
          <Input
            value={editTermo}
            onChange={e => setEditTermo(e.target.value)}
            className="!mt-0"
          />
        ) : (
          <span className="font-medium text-gray-900">{valor}</span>
        ),
    },
    {
      key: 'tipo',
      label: 'Tipo',
      width: '200px',
      render: (valor, t) =>
        editingId === t.id ? (
          <Select
            value={editTipo}
            onChange={e => setEditTipo(e.target.value)}
            options={TIPOS_TERMO}
          />
        ) : (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {TIPO_LABEL[valor] || valor}
          </span>
        ),
    },
    {
      key: 'actions',
      label: 'Ações',
      width: '180px',
      render: (_, t) =>
        editingId === t.id ? (
          <div className="flex gap-1">
            <Button variant="primary" size="sm" onClick={() => handleEditSave(t.id)} disabled={editSaving}>
              {editSaving ? '...' : 'Salvar'}
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setEditingId(null)} disabled={editSaving}>
              Cancelar
            </Button>
          </div>
        ) : (
          <div className="flex gap-1">
            <Button variant="secondary" size="sm" onClick={() => handleEditStart(t)}>
              Editar
            </Button>
            <Button variant="danger" size="sm" onClick={() => setTermoParaExcluir({ id: t.id, nome: t.termo })}>
              Excluir
            </Button>
          </div>
        ),
    },
  ];

  return (
    <div className="space-y-4">
      {mensagem && (
        <Alert variant={mensagem.tipo} onClose={() => setMensagem(null)}>
          {mensagem.texto}
        </Alert>
      )}
      {error && <Alert variant="error">{error}</Alert>}

      {/* Formulário adicionar */}
      <form onSubmit={handleAdicionar} className="flex gap-3 items-end">
        <div className="flex-1">
          <Input
            label="Novo Termo"
            value={novoTermo}
            onChange={e => setNovoTermo(e.target.value)}
            placeholder="Digite o termo..."
          />
        </div>
        <div className="w-52">
          <Select
            label="Tipo"
            value={tipoSelecionado}
            onChange={e => setTipoSelecionado(e.target.value)}
            options={TIPOS_TERMO}
          />
        </div>
        <Button type="submit" variant="primary">
          Adicionar
        </Button>
      </form>

      {/* Barra de ações em massa */}
      {someSelected && (
        <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
          <span className="text-sm font-medium text-blue-800">
            {selectedIds.size} {selectedIds.size === 1 ? 'termo selecionado' : 'termos selecionados'}
          </span>
          <Button variant="danger" size="sm" onClick={() => setConfirmBulkDelete(true)} disabled={bulkDeleting}>
            Excluir selecionados
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setSelectedIds(new Set())}>
            Cancelar seleção
          </Button>
        </div>
      )}

      {/* Tabela */}
      <div>
        {loading && termos.length === 0 ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            <p className="mt-2 text-sm text-gray-500">Carregando termos...</p>
          </div>
        ) : (
          <Table
            data={termos}
            columns={columns}
            emptyMessage="Nenhum termo cadastrado. Adicione termos usando o formulário acima."
          />
        )}
      </div>

      <ConfirmDialog
        isOpen={!!termoParaExcluir}
        onClose={() => setTermoParaExcluir(null)}
        onConfirm={handleExcluir}
        title="Confirmar Exclusão"
        message={`Deseja realmente excluir o termo "${termoParaExcluir?.nome}"?`}
        confirmText="Excluir"
        cancelText="Cancelar"
        variant="danger"
      />

      <ConfirmDialog
        isOpen={confirmBulkDelete}
        onClose={() => setConfirmBulkDelete(false)}
        onConfirm={handleBulkDelete}
        title="Confirmar Exclusão em Massa"
        message={`Deseja realmente excluir ${selectedIds.size} termos? Esta ação não pode ser desfeita.`}
        confirmText="Excluir todos"
        cancelText="Cancelar"
        variant="danger"
        loading={bulkDeleting}
      />
    </div>
  );
}

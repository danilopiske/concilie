'use client';

import { useState } from 'react';
import { useTaxas } from '@/lib/hooks/useTaxas';
import { Taxa, TaxaCreate } from '@/lib/api/taxas';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { Card } from '@/components/ui/Card';
import { Table, TableColumn } from '@/components/ui/Table';
import { Checkbox } from '@/components/ui/Checkbox';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Modal } from '@/components/ui/Modal';
import { formatDate } from '@/lib/utils/formatters';

interface TaxasFormProps {
  ec: string;
  contexto: string;
}

export function TaxasForm({ ec, contexto }: TaxasFormProps) {
  const { taxas, loading, error, adicionar, atualizar, excluir } = useTaxas(ec, contexto);

  // Form state (nova taxa)
  const [taxaGenerica, setTaxaGenerica] = useState(false);
  const [bandeira, setBandeira] = useState('');
  const [formaPagamento, setFormaPagamento] = useState('');
  const [parcelado, setParcelado] = useState<'S' | 'N'>('N');
  const [parcelasIni, setParcelasIni] = useState(1);
  const [parcelasFim, setParcelasFim] = useState(1);
  const [dataIni, setDataIni] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [taxa, setTaxa] = useState('');

  // UI state
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<Taxa | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Seleção em massa
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [confirmBulkDelete, setConfirmBulkDelete] = useState(false);

  // Edição
  const [editingTaxa, setEditingTaxa] = useState<Taxa | null>(null);
  const [editForm, setEditForm] = useState<Partial<TaxaCreate>>({});
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const allSelected = taxas.length > 0 && selectedIds.size === taxas.length;
  const someSelected = selectedIds.size > 0;

  const toggleSelectAll = () => {
    if (allSelected) setSelectedIds(new Set());
    else setSelectedIds(new Set(taxas.map(t => t.id)));
  };

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    if (!formaPagamento.trim() || parseFloat(taxa) <= 0 || !dataIni) {
      setFormError('Preencha forma de pagamento, taxa e data de início');
      return;
    }
    if (!taxaGenerica && !bandeira.trim()) {
      setFormError('Preencha a bandeira ou marque "Taxa Genérica"');
      return;
    }
    if (parcelasFim < parcelasIni) {
      setFormError('Parcela final deve ser maior ou igual à parcela inicial');
      return;
    }
    if (dataFim && dataFim < dataIni) {
      setFormError('Data fim deve ser maior ou igual à data de início');
      return;
    }

    try {
      const novaTaxa: TaxaCreate = {
        ec,
        bandeira: taxaGenerica ? null : bandeira.trim(),
        forma_pagamento: formaPagamento.trim().toUpperCase(),
        parcelado,
        parcelas_ini: parcelasIni,
        parcelas_fim: parcelasFim,
        data_ini: dataIni,
        data_fim: dataFim || null,
        taxa: parseFloat(taxa),
        contexto,
      };
      await adicionar(novaTaxa);
      const tipoTaxa = taxaGenerica ? 'genérica (todas bandeiras)' : 'específica';
      setSuccessMessage(`Taxa ${tipoTaxa} inserida com sucesso!`);
      setBandeira(''); setFormaPagamento(''); setParcelado('N');
      setParcelasIni(1); setParcelasFim(1); setDataFim(''); setTaxa(''); setTaxaGenerica(false);
    } catch {
      // erro tratado no hook
    }
  };

  const handleConfirmDelete = async () => {
    if (!confirmDelete) return;
    try {
      setDeleting(true);
      await excluir(confirmDelete.id);
      setSuccessMessage('Taxa excluída com sucesso!');
      setSelectedIds(prev => { const n = new Set(prev); n.delete(confirmDelete.id); return n; });
      setConfirmDelete(null);
    } catch {
      setFormError('Erro ao excluir taxa');
    } finally {
      setDeleting(false);
    }
  };

  const handleBulkDelete = async () => {
    try {
      setBulkDeleting(true);
      await Promise.all([...selectedIds].map(id => excluir(id)));
      setSuccessMessage(`${selectedIds.size} taxas excluídas com sucesso!`);
      setSelectedIds(new Set());
      setConfirmBulkDelete(false);
    } catch {
      setFormError('Erro ao excluir taxas');
    } finally {
      setBulkDeleting(false);
    }
  };

  const handleEditClick = (t: Taxa) => {
    setEditingTaxa(t);
    setEditError(null);
    setEditForm({
      bandeira: t.bandeira ?? undefined,
      forma_pagamento: t.forma_pagamento,
      parcelado: t.parcelado as 'S' | 'N',
      parcelas_ini: t.parcelas_ini,
      parcelas_fim: t.parcelas_fim,
      data_ini: t.data_ini,
      data_fim: t.data_fim ?? undefined,
      taxa: t.taxa,
    });
  };

  const handleEditSave = async () => {
    if (!editingTaxa) return;
    try {
      setEditSaving(true);
      setEditError(null);
      await atualizar(editingTaxa.id, editForm);
      setSuccessMessage('Taxa atualizada com sucesso!');
      setEditingTaxa(null);
    } catch (err: unknown) {
      setEditError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao salvar taxa');
    } finally {
      setEditSaving(false);
    }
  };

  const columns: TableColumn<Taxa>[] = [
    {
      key: 'id' as keyof Taxa,
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
        />
      ),
    },
    {
      key: 'bandeira',
      label: 'Bandeira',
      width: '150px',
      render: (value) => value || <span className="text-blue-600 font-semibold">TODAS (Genérica)</span>,
    },
    {
      key: 'forma_pagamento',
      label: 'Forma Pagamento',
      width: '180px',
    },
    {
      key: 'parcelado',
      label: 'Parc.',
      width: '70px',
      render: (value) => value === 'S' ? 'Sim' : 'Não',
    },
    {
      key: 'parcelas_ini',
      label: 'P.Ini',
      width: '60px',
    },
    {
      key: 'parcelas_fim',
      label: 'P.Fim',
      width: '60px',
    },
    {
      key: 'data_ini',
      label: 'Início',
      width: '110px',
      render: (value) => formatDate(value),
    },
    {
      key: 'data_fim',
      label: 'Fim',
      width: '110px',
      render: (value) => value ? formatDate(value) : '-',
    },
    {
      key: 'taxa',
      label: 'Taxa (%)',
      width: '90px',
      render: (value) => parseFloat(value).toFixed(2) + '%',
    },
    {
      key: 'actions',
      label: 'Ações',
      width: '140px',
      render: (_, t) => (
        <div className="flex gap-1">
          <Button variant="secondary" size="sm" onClick={() => handleEditClick(t)}>
            Editar
          </Button>
          <Button variant="danger" size="sm" onClick={() => setConfirmDelete(t)}>
            Excluir
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {successMessage && (
        <Alert variant="success" onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}
      {(error || formError) && (
        <Alert variant="error" onClose={() => setFormError(null)}>
          {error || formError}
        </Alert>
      )}

      {/* Formulário Nova Taxa */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Nova Taxa</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <Checkbox
              label="Taxa Genérica (aplica a todas as bandeiras)"
              checked={taxaGenerica}
              onChange={setTaxaGenerica}
            />
            <p className="text-sm text-gray-600 mt-1 ml-6">
              Marque esta opção para criar uma taxa que se aplica a todas as bandeiras de cartão
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Bandeira"
              value={bandeira}
              onChange={(e) => setBandeira(e.target.value)}
              placeholder="Ex: Visa, Mastercard, Elo"
              disabled={taxaGenerica}
              helperText={taxaGenerica ? 'Desabilitado para taxa genérica' : ''}
            />
            <Input
              label="Forma de Pagamento"
              value={formaPagamento}
              onChange={(e) => setFormaPagamento(e.target.value)}
              placeholder="Ex: CRÉDITO À VISTA"
              required
            />
            <div className="flex items-center h-full pt-6">
              <Checkbox
                label="Parcelado?"
                checked={parcelado === 'S'}
                onChange={(checked) => setParcelado(checked ? 'S' : 'N')}
              />
            </div>
            <Input
              label="Taxa (%)"
              type="number"
              step="0.01"
              min="0"
              value={taxa}
              onChange={(e) => setTaxa(e.target.value)}
              placeholder="Ex: 2.35"
              required
            />
            <Input
              label="Parcela Inicial"
              type="number"
              min="1"
              value={parcelasIni}
              onChange={(e) => setParcelasIni(parseInt(e.target.value))}
              required
            />
            <Input
              label="Parcela Final"
              type="number"
              min="1"
              value={parcelasFim}
              onChange={(e) => setParcelasFim(parseInt(e.target.value))}
              required
            />
            <Input
              label="Data de Início"
              type="date"
              value={dataIni}
              onChange={(e) => setDataIni(e.target.value)}
              required
            />
            <Input
              label="Data de Fim (opcional)"
              type="date"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
            />
          </div>
          <div className="flex justify-end">
            <Button type="submit" variant="primary">Inserir Taxa</Button>
          </div>
        </form>
      </Card>

      {/* Tabela de Taxas */}
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Taxas Cadastradas</h3>
          <span className="text-sm text-gray-600">Total: {taxas.length}</span>
        </div>

        {/* Barra de ações em massa */}
        {someSelected && (
          <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 mb-4">
            <span className="text-sm font-medium text-blue-800">
              {selectedIds.size} {selectedIds.size === 1 ? 'taxa selecionada' : 'taxas selecionadas'}
            </span>
            <Button
              variant="danger"
              size="sm"
              onClick={() => setConfirmBulkDelete(true)}
              disabled={bulkDeleting}
            >
              Excluir selecionadas
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setSelectedIds(new Set())}>
              Cancelar seleção
            </Button>
          </div>
        )}

        {loading ? (
          <div className="text-center py-8 text-gray-600">Carregando taxas...</div>
        ) : taxas.length === 0 ? (
          <div className="text-center py-8 text-gray-600">Nenhuma taxa cadastrada para este EC</div>
        ) : (
          <Table variant="simple" columns={columns} data={taxas} />
        )}
      </Card>

      {/* Modal de Edição */}
      <Modal
        isOpen={!!editingTaxa}
        onClose={() => setEditingTaxa(null)}
        title="Editar Taxa"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditingTaxa(null)} disabled={editSaving}>
              Cancelar
            </Button>
            <Button onClick={handleEditSave} disabled={editSaving}>
              {editSaving ? 'Salvando...' : 'Salvar'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {editError && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {editError}
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Bandeira (vazio = genérica)"
              value={editForm.bandeira ?? ''}
              onChange={e => setEditForm(p => ({ ...p, bandeira: e.target.value || undefined }))}
              placeholder="Ex: Visa, Mastercard, Elo"
            />
            <Input
              label="Forma de Pagamento"
              value={editForm.forma_pagamento ?? ''}
              onChange={e => setEditForm(p => ({ ...p, forma_pagamento: e.target.value.toUpperCase() }))}
            />
            <div className="flex items-center pt-6">
              <Checkbox
                label="Parcelado?"
                checked={editForm.parcelado === 'S'}
                onChange={checked => setEditForm(p => ({ ...p, parcelado: checked ? 'S' : 'N' }))}
              />
            </div>
            <Input
              label="Taxa (%)"
              type="number"
              step="0.01"
              min="0"
              value={editForm.taxa ?? ''}
              onChange={e => setEditForm(p => ({ ...p, taxa: parseFloat(e.target.value) }))}
            />
            <Input
              label="Parcela Inicial"
              type="number"
              min="1"
              value={editForm.parcelas_ini ?? 1}
              onChange={e => setEditForm(p => ({ ...p, parcelas_ini: parseInt(e.target.value) }))}
            />
            <Input
              label="Parcela Final"
              type="number"
              min="1"
              value={editForm.parcelas_fim ?? 1}
              onChange={e => setEditForm(p => ({ ...p, parcelas_fim: parseInt(e.target.value) }))}
            />
            <Input
              label="Data de Início"
              type="date"
              value={editForm.data_ini ?? ''}
              onChange={e => setEditForm(p => ({ ...p, data_ini: e.target.value }))}
            />
            <Input
              label="Data de Fim (opcional)"
              type="date"
              value={editForm.data_fim ?? ''}
              onChange={e => setEditForm(p => ({ ...p, data_fim: e.target.value || undefined }))}
            />
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        title="Confirmar Exclusão"
        message={`Deseja realmente excluir a taxa ${confirmDelete?.bandeira || 'GENÉRICA'} - ${confirmDelete?.forma_pagamento} (${confirmDelete?.taxa}%)?`}
        confirmText="Excluir"
        cancelText="Cancelar"
        onConfirm={handleConfirmDelete}
        onClose={() => setConfirmDelete(null)}
        isOpen={!!confirmDelete}
        variant="danger"
        loading={deleting}
      />

      <ConfirmDialog
        isOpen={confirmBulkDelete}
        onClose={() => setConfirmBulkDelete(false)}
        onConfirm={handleBulkDelete}
        title="Confirmar Exclusão em Massa"
        message={`Deseja realmente excluir ${selectedIds.size} taxas? Esta ação não pode ser desfeita.`}
        confirmText="Excluir todas"
        cancelText="Cancelar"
        variant="danger"
        loading={bulkDeleting}
      />
    </div>
  );
}

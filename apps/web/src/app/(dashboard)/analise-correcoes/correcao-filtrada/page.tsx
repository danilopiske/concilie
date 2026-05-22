'use client';

import { useState, useEffect } from 'react';
import type { ComponentType } from 'react';
import { Panel, PanelHeader, PanelBody } from '@/components/ui/Panel';
import { Button } from '@/components/ui/Button';
import { Table, TableColumn } from '@/components/ui/Table';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { importacaoApi } from '@/lib/api/importacao';
import { correcaoService } from '@/lib/api/correcao';
import { useAuth } from '@/hooks/useAuth';
import { Processamento } from '@/lib/types/importacao';
import { ResumoResponse, ResumoItem } from '@/lib/types/correcao';
import { formatCurrency } from '@/lib/utils/formatters';
import {
  AlertTriangle,
  List,
  Wallet,
  CreditCard,
  DollarSign,
  Info,
  RefreshCw,
  Trash2,
  Edit2,
  Undo2,
} from 'lucide-react';

export default function CorrecaoFiltradaPage() {
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [selectedProcessamento, setSelectedProcessamento] = useState<string>('');
  const [resumo, setResumo] = useState<ResumoResponse | null>(null);
  const [loadingProc, setLoadingProc] = useState(true);
  const [loadingResumo, setLoadingResumo] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [actionItem, setActionItem] = useState<{ campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento'; item: ResumoItem } | null>(null);
  const [newValue, setNewValue] = useState('');
  const [processingAction, setProcessingAction] = useState(false);

  const [selectedItems, setSelectedItems] = useState<Record<string, string[]>>({
    forma_pagamento: [],
    bandeira: [],
    status: [],
    lancamento: [],
  });

  const { user } = useAuth();

  useEffect(() => {
    fetchProcessamentos();
  }, []);

  useEffect(() => {
    if (selectedProcessamento) {
      fetchResumo(selectedProcessamento);
    } else {
      setResumo(null);
    }
  }, [selectedProcessamento]);

  const fetchProcessamentos = async () => {
    try {
      setLoadingProc(true);
      const data = await importacaoApi.processamentos.listar(undefined, undefined, true);
      setProcessamentos(data);
    } catch (err) {
      setError('Erro ao carregar lista de processamentos');
      console.error(err);
    } finally {
      setLoadingProc(false);
    }
  };

  const fetchResumo = async (id: string) => {
    try {
      if (!resumo) setLoadingResumo(true);
      else setIsRefreshing(true);
      const data = await correcaoService.obterResumoFiltradas(id);
      setResumo(data);
    } catch (err) {
      setError('Erro ao carregar dados filtrados');
      console.error(err);
    } finally {
      setLoadingResumo(false);
      setIsRefreshing(false);
    }
  };

  const handleEdit = (
    campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento',
    item: ResumoItem | 'selected'
  ) => {
    if (item === 'selected') {
      const selected = selectedItems[campo];
      if (!selected || selected.length === 0) {
        alert('Selecione ao menos um item');
        return;
      }
      setActionItem({ campo, item: { valor: selected.join(', '), quantidade: 0, valor_total: 0 } });
    } else {
      setActionItem({ campo, item });
    }
    setNewValue(typeof item === 'string' ? '' : item.valor);
    setEditModalOpen(true);
  };

  const handleDelete = (
    campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento',
    item: ResumoItem | 'selected'
  ) => {
    if (item === 'selected') {
      const selected = selectedItems[campo];
      if (!selected || selected.length === 0) {
        alert('Selecione ao menos um item');
        return;
      }
      setActionItem({ campo, item: { valor: selected.join(', '), quantidade: 0, valor_total: 0 } });
    } else {
      setActionItem({ campo, item });
    }
    setDeleteDialogOpen(true);
  };

  const handleRestore = (
    campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento',
    item: ResumoItem | 'selected'
  ) => {
    if (item === 'selected') {
      const selected = selectedItems[campo];
      if (!selected || selected.length === 0) {
        alert('Selecione ao menos um item');
        return;
      }
      setActionItem({ campo, item: { valor: selected.join(', '), quantidade: 0, valor_total: 0 } });
    } else {
      setActionItem({ campo, item });
    }
    setRestoreDialogOpen(true);
  };

  const confirmRestore = async () => {
    if (!actionItem || !selectedProcessamento) return;
    try {
      setProcessingAction(true);
      const isBatch = actionItem.item.quantidade === 0 && actionItem.item.valor.includes(', ');
      const valores = isBatch ? selectedItems[actionItem.campo] : [actionItem.item.valor];
      await correcaoService.restaurarFiltradas({
        processamento_id: selectedProcessamento,
        campo: actionItem.campo,
        valores,
        usuario: user?.usuario,
      });
      setSuccess('Registros restaurados para processadas com sucesso!');
    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(`Erro ao restaurar: ${apiErr.response?.data?.detail || apiErr.message || 'Erro desconhecido'}`);
      return;
    } finally {
      setProcessingAction(false);
      setRestoreDialogOpen(false);
      setActionItem(null);
      setSelectedItems(prev => ({ ...prev, [actionItem.campo]: [] }));
    }
    await fetchResumo(selectedProcessamento);
  };

  const confirmEdit = async () => {
    if (!actionItem || !selectedProcessamento) return;
    try {
      setProcessingAction(true);
      const isBatch = actionItem.item.quantidade === 0 && actionItem.item.valor.includes(', ');
      const valores_antigos = isBatch ? selectedItems[actionItem.campo] : [actionItem.item.valor];
      await correcaoService.atualizarFiltradas({
        processamento_id: selectedProcessamento,
        campo: actionItem.campo,
        valores_antigos,
        valor_novo: newValue,
        usuario: user?.usuario,
      });
      setSuccess('Atualização realizada com sucesso!');
    } catch (err) {
      setError('Erro ao atualizar: ' + err);
      return;
    } finally {
      setProcessingAction(false);
      setEditModalOpen(false);
      setActionItem(null);
      setSelectedItems(prev => ({ ...prev, [actionItem.campo]: [] }));
    }
    await fetchResumo(selectedProcessamento);
  };

  const confirmDelete = async () => {
    if (!actionItem || !selectedProcessamento) return;
    try {
      setProcessingAction(true);
      const isBatch = actionItem.item.quantidade === 0 && actionItem.item.valor.includes(', ');
      const valores = isBatch ? selectedItems[actionItem.campo] : [actionItem.item.valor];
      await correcaoService.excluirFiltradas({
        processamento_id: selectedProcessamento,
        campo: actionItem.campo,
        valores,
        usuario: user?.usuario,
      });
      setSuccess('Registros excluídos permanentemente!');
    } catch (err: unknown) {
      console.error(err);
      const apiErr = err as { response?: { data?: { detail?: string } }; message?: string };
      const msg = apiErr.response?.data?.detail || apiErr.message || 'Erro desconhecido';
      setError(`Erro ao excluir: ${msg}`);
      return;
    } finally {
      setProcessingAction(false);
      setDeleteDialogOpen(false);
      setActionItem(null);
      setSelectedItems(prev => ({ ...prev, [actionItem.campo]: [] }));
    }
    await fetchResumo(selectedProcessamento);
  };

  const renderSection = (
    title: string,
    data: ResumoItem[],
    campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento',
    icon: ComponentType<{ className?: string }>
  ) => {
    const selected = selectedItems[campo] || [];
    const isAllSelected = data.length > 0 && selected.length === data.length;

    const toggleAll = () => {
      setSelectedItems(prev => ({
        ...prev,
        [campo]: isAllSelected ? [] : data.map(i => i.valor),
      }));
    };

    const toggleItem = (valor: string) => {
      setSelectedItems(prev => {
        const current = prev[campo] || [];
        return current.includes(valor)
          ? { ...prev, [campo]: current.filter(v => v !== valor) }
          : { ...prev, [campo]: [...current, valor] };
      });
    };

    const columns: TableColumn<ResumoItem>[] = [
      {
        key: 'select',
        label: (
          <input
            type="checkbox"
            checked={isAllSelected}
            onChange={toggleAll}
            className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
          />
        ),
        width: '40px',
        render: (_, item) => (
          <input
            type="checkbox"
            checked={selected.includes(item.valor)}
            onChange={() => toggleItem(item.valor)}
            className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
          />
        ),
      },
      { key: 'valor', label: 'Valor' },
      { key: 'quantidade', label: 'Qtd', width: '100px' },
      {
        key: 'valor_total',
        label: 'Total',
        render: (v) => formatCurrency(v),
        width: '150px',
      },
      {
        key: 'acoes',
        label: 'Ações',
        width: '310px',
        render: (_, item) => (
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" size="sm" onClick={() => handleRestore(campo, item)} className="text-green-700 border-green-200 hover:bg-green-50">
              <Undo2 className="w-4 h-4" /> Restaurar
            </Button>
            <Button variant="secondary" size="sm" onClick={() => handleEdit(campo, item)}>
              <Edit2 className="w-4 h-4" /> Editar
            </Button>
            <Button variant="danger" size="sm" onClick={() => handleDelete(campo, item)}>
              <Trash2 className="w-4 h-4" /> Excluir
            </Button>
          </div>
        ),
      },
    ];

    return (
      <Panel className="mb-6">
        <PanelHeader icon={icon}>
          <div className="flex justify-between items-center w-full">
            <span>{title}</span>
            {selected.length > 0 && (
              <div className="flex gap-2 mr-4">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleRestore(campo, 'selected')}
                  className="bg-green-50 text-green-700 border-green-200 hover:bg-green-100 shadow-none border"
                >
                  <Undo2 className="w-4 h-4 mr-1" /> Restaurar {selected.length}
                </Button>
                <Button variant="primary" size="sm" onClick={() => handleEdit(campo, 'selected')}>
                  <Edit2 className="w-4 h-4 mr-1" /> Mapear {selected.length}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleDelete(campo, 'selected')}
                  className="bg-red-50 text-red-600 border-red-200 hover:bg-red-100 shadow-none border"
                >
                  <Trash2 className="w-4 h-4 mr-1" /> Excluir {selected.length}
                </Button>
              </div>
            )}
          </div>
        </PanelHeader>
        <PanelBody className="p-0 relative">
          {isRefreshing && (
            <div className="absolute inset-0 bg-white/50 backdrop-blur-[1px] z-10 flex items-center justify-center">
              <div className="flex flex-col items-center gap-2">
                <RefreshCw className="w-8 h-8 text-orange-500 animate-spin" />
                <span className="text-xs font-bold text-orange-700 uppercase tracking-widest animate-pulse">Atualizando dados...</span>
              </div>
            </div>
          )}
          <Table
            columns={columns}
            data={data}
            emptyMessage="Nenhum registro filtrado encontrado."
            pagination={data.length > 10}
            pageSize={10}
            rowKey="valor"
          />
        </PanelBody>
      </Panel>
    );
  };

  return (
    <div className="max-w-7xl mx-auto pb-10 relative">
      {processingAction && (
        <div className="fixed inset-0 bg-black/10 backdrop-blur-[2px] z-[9999] flex items-center justify-center">
          <div className="bg-white p-8 rounded-xl shadow-2xl border border-gray-100 flex flex-col items-center gap-4">
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 border-4 border-orange-100 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-orange-500 rounded-full border-t-transparent animate-spin"></div>
            </div>
            <div className="text-center">
              <h3 className="text-lg font-bold text-gray-900">Processando Operação...</h3>
              <p className="text-sm text-gray-500">Isso pode levar alguns segundos.</p>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-6 border-b pb-4">
        <div className="flex items-center gap-2 text-gray-700 mb-1">
          <AlertTriangle className="w-6 h-6 text-orange-500" />
          <h1 className="text-2xl font-bold">Correção de Registros Filtrados</h1>
        </div>
        <p className="text-sm text-gray-500">
          Gerencie os registros que foram removidos das vendas e recebíveis processados.
          Você pode editar valores ou <strong>excluir permanentemente</strong> — atenção, exclusões aqui não podem ser desfeitas.
        </p>
      </div>

      <div className="bg-orange-50 border border-orange-200 text-orange-800 px-4 py-3 rounded text-sm flex items-center gap-2 mb-6">
        <AlertTriangle className="w-4 h-4 shrink-0" />
        <span><strong>Atenção:</strong> Excluir registros desta tela é uma ação permanente e irreversível.</span>
      </div>

      {error && <ErrorMessage message={error} />}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded relative mb-6 animate-in fade-in duration-300">
          <span className="block sm:inline">{success}</span>
          <button className="absolute top-0 bottom-0 right-0 px-4 py-3" onClick={() => setSuccess(null)}>
            <span className="text-xl">&times;</span>
          </button>
        </div>
      )}

      {/* Selecionar Processamento */}
      <Panel>
        <PanelHeader icon={List}>1. Selecionar Processamento</PanelHeader>
        <PanelBody>
          <div className="flex flex-col md:flex-row gap-4 items-start md:items-end">
            <div className="flex-1 w-full">
              <label className="text-sm font-medium text-gray-700 mb-1 block">Processamento</label>
              <select
                className="w-full border-gray-300 rounded-md shadow-sm focus:border-orange-500 focus:ring-orange-500 min-h-[40px]"
                value={selectedProcessamento}
                onChange={(e) => setSelectedProcessamento(e.target.value)}
                disabled={loadingProc}
              >
                <option value="">Selecione...</option>
                {processamentos.map(p => {
                  const dMin = p.data_min ? new Date(p.data_min).toLocaleDateString() : '?';
                  const dMax = p.data_max ? new Date(p.data_max).toLocaleDateString() : '?';
                  const periodo = p.data_min || p.data_max ? `Período: ${dMin} a ${dMax}` : '';
                  const qtd = p.qtd_processadas || p.linhas_processadas || 0;
                  return (
                    <option key={p.id} value={String(p.id)}>
                      {p.id} - {p.tipo_arquivo} - {p.nome_arquivo} | Qtd: {qtd} | {periodo}
                    </option>
                  );
                })}
              </select>
            </div>
            <div className="flex gap-2">
              <Button onClick={fetchProcessamentos} variant="primary" disabled={loadingProc}>
                🔄 Carregar Processamentos
              </Button>
              <Button
                onClick={() => selectedProcessamento && fetchResumo(selectedProcessamento)}
                variant="secondary"
                disabled={!selectedProcessamento || isRefreshing}
                loading={isRefreshing}
              >
                🔄 Atualizar
              </Button>
            </div>
          </div>
        </PanelBody>
      </Panel>

      {loadingResumo && <Loading message="Carregando registros filtrados..." />}

      {resumo && !loadingResumo && (
        <div className="space-y-6">
          {/* Vendas Filtradas */}
          {renderSection('Formas de Pagamento — Filtradas', (resumo.formas_pagamento || []).filter(i => i.valor !== 'N/A'), 'forma_pagamento', Wallet)}
          {renderSection('Bandeiras — Filtradas', (resumo.bandeiras || []).filter(i => i.valor !== 'N/A'), 'bandeira', CreditCard)}
          {renderSection('Status — Filtrados', resumo.status || [], 'status', Info)}

          {/* Recebíveis Filtrados */}
          {renderSection('Recebíveis — Filtrados', (resumo.recebiveis || []).filter(i => i.valor !== 'N/A'), 'lancamento', DollarSign)}
        </div>
      )}

      {/* Edit Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title={`Editar ${actionItem?.item.valor}`}
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Digite o novo nome para todas as ocorrências de <strong>{actionItem?.item.valor}</strong>:
          </p>
          <Input
            value={newValue}
            onChange={(e) => setNewValue(e.target.value)}
            placeholder="Novo valor"
          />
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="text" onClick={() => setEditModalOpen(false)}>Cancelar</Button>
            <Button onClick={confirmEdit} disabled={processingAction}>
              {processingAction ? 'Salvando...' : 'Salvar Alteração'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={deleteDialogOpen}
        onClose={() => { setDeleteDialogOpen(false); setActionItem(null); }}
        onConfirm={confirmDelete}
        title="Excluir Permanentemente"
        message={`Tem certeza que deseja EXCLUIR PERMANENTEMENTE todas as ocorrências de "${actionItem?.item.valor}"? Esta ação não pode ser desfeita.`}
        confirmText={processingAction ? 'Excluindo...' : 'Sim, Excluir Permanentemente'}
        loading={processingAction}
        variant="danger"
      />

      {/* Restore Confirmation */}
      <ConfirmDialog
        isOpen={restoreDialogOpen}
        onClose={() => { setRestoreDialogOpen(false); setActionItem(null); }}
        onConfirm={confirmRestore}
        title="Restaurar para Processadas"
        message={`Deseja restaurar todos os registros de "${actionItem?.item.valor}" de volta para vendas/recebíveis processados?`}
        confirmText={processingAction ? 'Restaurando...' : 'Sim, Restaurar'}
        loading={processingAction}
        variant="info"
      />
    </div>
  );
}

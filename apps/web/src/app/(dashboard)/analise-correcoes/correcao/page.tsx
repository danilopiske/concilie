'use client';

import { useState, useEffect } from 'react';
import type { ComponentType } from 'react';
import { Panel, PanelHeader, PanelBody } from '@/components/ui/Panel';
import { Button } from '@/components/ui/Button';
import { Table, TableColumn } from '@/components/ui/Table';
import { Select } from '@/components/ui/Select';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { importacaoApi } from '@/lib/api/importacao';
import { correcaoService } from '@/lib/api/correcao';
import { useAuth } from '@/hooks/useAuth';
import { Processamento } from '@/lib/types/importacao';
import { ResumoResponse, ResumoItem, HistoricoItem } from '@/lib/types/correcao';
import { formatCurrency } from '@/lib/utils/formatters';
import { 
  Wrench, 
  List, 
  FileText, 
  CreditCard, 
  Wallet, 
  DollarSign, 
  Info,
  RefreshCw,
  History,
  Trash2,
  Edit2,
  AlertTriangle
} from 'lucide-react';

export default function CorrecaoToolPage() {
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [selectedProcessamento, setSelectedProcessamento] = useState<string>('');
  const [resumo, setResumo] = useState<ResumoResponse | null>(null);
  const [loadingProc, setLoadingProc] = useState(true);
  const [loadingResumo, setLoadingResumo] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Historico
  const [historicoOpen, setHistoricoOpen] = useState(false);
  const [historicoData, setHistoricoData] = useState<HistoricoItem[]>([]);
  const [loadingHistorico, setLoadingHistorico] = useState(false);



  // Dialog states
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [actionItem, setActionItem] = useState<{ campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento'; item: ResumoItem } | null>(null);
  const [newValue, setNewValue] = useState('');
  const [processingAction, setProcessingAction] = useState(false);

  // Taxa BC
  const [bcFiltros, setBcFiltros] = useState<{ formas: string[], bandeiras: string[] }>({ formas: [], bandeiras: [] });
  const [bcSelectedForma, setBcSelectedForma] = useState('TODOS');
  const [bcSelectedBandeira, setBcSelectedBandeira] = useState('TODOS');
  const [bcDataIni, setBcDataIni] = useState('');
  const [bcDataFim, setBcDataFim] = useState('');
  const [bcNovaTaxa, setBcNovaTaxa] = useState<number | ''>('');
  const [loadingBcFiltros, setLoadingBcFiltros] = useState(false);
  const [applyingBC, setApplyingBC] = useState(false);

  // Auth
  const { user } = useAuth();

  // Multi-selection
  const [selectedItems, setSelectedItems] = useState<Record<string, string[]>>({
    forma_pagamento: [],
    bandeira: [],
    status: [],
    lancamento: []
  });



  useEffect(() => {
    fetchProcessamentos();
  }, []);

  useEffect(() => {
    if (selectedProcessamento) {
      fetchResumo(selectedProcessamento);
      fetchBcFiltros(selectedProcessamento);
    } else {
      setResumo(null);
      setBcFiltros({ formas: [], bandeiras: [] });
    }
  }, [selectedProcessamento]);

  // DEBUG: Monitor state changes
  useEffect(() => {
    console.log('[DEBUG] ActionItem changed:', actionItem);
  }, [actionItem]);

  useEffect(() => {
    console.log('[DEBUG] DeleteDialog open:', deleteDialogOpen);
  }, [deleteDialogOpen]);

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
      if(!resumo) setLoadingResumo(true);
      else setIsRefreshing(true);
      
      const data = await correcaoService.obterResumo(id);
      setResumo(data);
    } catch (err) {
      setError('Erro ao carregar resumo do processamento');
      console.error(err);
    } finally {
      setLoadingResumo(false);
      setIsRefreshing(false);
    }
  };

  const fetchHistorico = async () => {
    if (!selectedProcessamento) return;
    setLoadingHistorico(true);
    setHistoricoOpen(true);
    try {
      const data = await correcaoService.obterHistorico(selectedProcessamento);
      setHistoricoData(data);
    } catch (err) {
      console.error(err);
      alert('Erro ao carregar histórico');
    } finally {
      setLoadingHistorico(false);
    }
  };

  const fetchBcFiltros = async (id: string) => {
    try {
      setLoadingBcFiltros(true);
      const data = await correcaoService.obterFiltrosTaxaBC(id);
      setBcFiltros(data);
    } catch (err) {
      console.error('Erro ao carregar filtros BC:', err);
    } finally {
      setLoadingBcFiltros(false);
    }
  };

  const handleAplicarTaxaBC = async () => {
    if (!selectedProcessamento || bcNovaTaxa === '') {
        alert('Selecione um processamento e informe a nova taxa.');
        return;
    }
    
    try {
      setApplyingBC(true);
      setError(null);
      setSuccess(null);
      const res = await correcaoService.aplicarTaxaBC({
        processamento_id: selectedProcessamento,
        forma_pagamento: bcSelectedForma,
        bandeira: bcSelectedBandeira,
        data_ini: bcDataIni || undefined,
        data_fim: bcDataFim || undefined,
        nova_taxa: Number(bcNovaTaxa)
      });
      setSuccess(`Sucesso! ${res.linhas_afetadas} linhas atualizadas.`);
      if (selectedProcessamento) await fetchResumo(selectedProcessamento);
    } catch (err) {
      setError('Erro ao aplicar Taxa BC: ' + err);
    } finally {
      setApplyingBC(false);
    }
  };



  const handleEdit = (campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento', item: ResumoItem | 'selected', customNewValue?: string) => {
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
    setNewValue(customNewValue || (typeof item === 'string' ? '' : item.valor));
    setEditModalOpen(true);
  };

  const handleDelete = (campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento', item: ResumoItem | 'selected') => {
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

  const confirmEdit = async () => {
    if (!actionItem || !selectedProcessamento) return;

    try {
      setProcessingAction(true);
      const isBatch = actionItem.item.quantidade === 0 && actionItem.item.valor.includes(', ');
      const valores_antigos = isBatch ? selectedItems[actionItem.campo] : [actionItem.item.valor];

      await correcaoService.atualizarEmMassa({
        processamento_id: selectedProcessamento,
        campo: actionItem.campo,
        valores_antigos,
        valor_novo: newValue,
        usuario: user?.usuario
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

      await correcaoService.removerEmMassa({
        processamento_id: selectedProcessamento,
        campo: actionItem.campo,
        valores,
        usuario: user?.usuario
      });
      setSuccess('Registros removidos com sucesso!');
    } catch (err: unknown) {
      console.error(err);
      const apiErr = err as { response?: { data?: { detail?: string } }; message?: string };
      const msg = apiErr.response?.data?.detail || apiErr.message || 'Erro desconhecido';
      setError(`Erro ao remover: ${msg}`);
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
        [campo]: isAllSelected ? [] : data.map(i => i.valor)
      }));
    };

    const toggleItem = (valor: string) => {
      setSelectedItems(prev => {
        const current = prev[campo] || [];
        if (current.includes(valor)) {
          return { ...prev, [campo]: current.filter(v => v !== valor) };
        } else {
          return { ...prev, [campo]: [...current, valor] };
        }
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
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
        ),
        width: '40px',
        render: (_, item) => (
          <input
            type="checkbox"
            checked={selected.includes(item.valor)}
            onChange={() => toggleItem(item.valor)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
        )
      },
      { key: 'valor', label: 'Nome Original' },
      { key: 'quantidade', label: 'Qtd', width: '100px' },
      {
        key: 'valor_total',
        label: 'Total',
        render: (v) => formatCurrency(v),
        width: '150px'
      },
      {
        key: 'acoes',
        label: 'Ações',
        width: '200px',
        render: (_, item) => (
          <div className="flex gap-2 justify-end">
            <Button variant="secondary" size="sm" onClick={() => handleEdit(campo, item)} title="Editar">
              <Edit2 className="w-4 h-4" /> Editar
            </Button>
            <Button variant="danger" size="sm" onClick={() => handleDelete(campo, item)} title="Remover">
              <Trash2 className="w-4 h-4" /> Remover
            </Button>
          </div>
        )
      }
    ];

    return (
      <Panel className="mb-6">
        <PanelHeader icon={icon}>
          <div className="flex justify-between items-center w-full">
            <span>{title}</span>
            {selected.length > 0 && (
              <div className="flex gap-2 mr-4">
                <Button variant="primary" size="sm" onClick={() => handleEdit(campo, 'selected')}>
                  <Edit2 className="w-4 h-4 mr-1" /> Mapear {selected.length}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleDelete(campo, 'selected')}
                  className="bg-red-50 text-red-600 border-red-200 hover:bg-red-100 shadow-none border"
                >
                  <Trash2 className="w-4 h-4 mr-1" /> Remover {selected.length}
                </Button>
              </div>
            )}
          </div>
        </PanelHeader>
        <PanelBody className="p-0 relative">
          {isRefreshing && (
            <div className="absolute inset-0 bg-white/50 backdrop-blur-[1px] z-10 flex items-center justify-center">
              <div className="flex flex-col items-center gap-2">
                <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
                <span className="text-xs font-bold text-blue-800 uppercase tracking-widest animate-pulse">Atualizando dados...</span>
              </div>
            </div>
          )}
          <Table
            columns={columns}
            data={data}
            emptyMessage="Nenhum registro encontrado."
            pagination={data.length > 10}
            pageSize={10}
            rowKey="valor"
          />
        </PanelBody>
      </Panel>
    );
  };

  const historyColumns: TableColumn<HistoricoItem>[] = [
    { key: 'data_correcao', label: 'Data', render: (v) => new Date(v).toLocaleString('pt-BR') },
    { key: 'usuario', label: 'Usuário' },
    { key: 'tipo_correcao', label: 'Ação' },
    { key: 'valor_antigo', label: 'Valor Antigo' },
    { key: 'valor_novo', label: 'Valor Novo' },
    { key: 'linhas_afetadas', label: 'Linhas' },
  ];

  return (
    <div className="max-w-7xl mx-auto pb-10 relative">
      {(processingAction || applyingBC) && (
        <div className="fixed inset-0 bg-black/10 backdrop-blur-[2px] z-[9999] flex items-center justify-center">
            <div className="bg-white p-8 rounded-xl shadow-2xl border border-gray-100 flex flex-col items-center gap-4">
                <div className="relative w-16 h-16">
                    <div className="absolute inset-0 border-4 border-blue-100 rounded-full"></div>
                    <div className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent animate-spin"></div>
                </div>
                <div className="text-center">
                    <h3 className="text-lg font-bold text-gray-900">Processando Operação...</h3>
                    <p className="text-sm text-gray-500">Isso pode levar alguns segundos dependendo do volume.</p>
                </div>
            </div>
        </div>
      )}
      
      {/* Header Legacy Style */}
      <div className="mb-6 border-b pb-4">
        <div className="flex items-center gap-2 text-gray-700 mb-1">
            <Wrench className="w-6 h-6" />
            <h1 className="text-2xl font-bold">Correção de Importações</h1>
        </div>
        <p className="text-sm text-gray-500">
            Esta ferramenta permite corrigir dados já importados. Você pode atualizar valores ou remover linhas com base em Forma de Pagamento ou Bandeira.
            Importante: Dados removidos são movidos para vendas_filtradas, não deletados permanentemente.
        </p>
      </div>

      {error && <ErrorMessage message={error} />}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded relative mb-6 animate-in fade-in duration-300">
           <span className="block sm:inline">{success}</span>
           <button 
             className="absolute top-0 bottom-0 right-0 px-4 py-3"
             onClick={() => setSuccess(null)}
           >
             <span className="text-xl">&times;</span>
           </button>
        </div>
      )}

      {/* 1. Selecionar Processamento */}
      <Panel>
          <PanelHeader icon={List}>1. Selecionar Processamento</PanelHeader>
          <PanelBody>
              <div className="flex flex-col md:flex-row gap-4 items-start md:items-end">
                  <div className="flex-1 w-full">
                    <label className="text-sm font-medium text-gray-700 mb-1 block">Processamento</label>
                    <select
                        className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 min-h-[40px]"
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
                    <Button onClick={fetchHistorico} variant="secondary" disabled={!selectedProcessamento}>
                        📜 Ver Histórico
                    </Button>
                  </div>
              </div>
          </PanelBody>
      </Panel>

      {/* 2. Resumo do Processamento (Instruções) */}
      <Panel>
          <PanelHeader icon={FileText}>2. Resumo do Processamento</PanelHeader>
          <PanelBody>
              <div className="flex justify-end mb-4">
                  <Button 
                    size="sm" 
                    variant="success" 
                    onClick={() => selectedProcessamento && fetchResumo(selectedProcessamento)} 
                    disabled={!selectedProcessamento || loadingResumo || isRefreshing}
                    loading={isRefreshing}
                  >
                      {isRefreshing ? 'Atualizando...' : '🔄 Atualizar Resumo'}
                  </Button>
              </div>
              
              <div className="bg-gray-50 p-4 border border-gray-200 rounded text-sm text-gray-700">
                  <strong className="block mb-2 text-gray-900">Instruções:</strong>
                  <ol className="list-decimal pl-5 space-y-1">
                      <li>Carregue a lista de processamentos</li>
                      <li>Selecione um processamento (verá o resumo de formas de pagamento e bandeiras)</li>
                      <li>Para <strong>Atualizar</strong>: Clique no botão &apos;Editar&apos; na linha desejada</li>
                      <li>Para <strong>Remover</strong>: Clique no botão &apos;Remover&apos; na linha desejada (move para vendas_filtradas)</li>
                  </ol>
                  <p className="mt-3 text-xs text-gray-500">Nota: Após cada operação, o resumo é atualizado automaticamente.</p>
              </div>
          </PanelBody>
      </Panel>

      {loadingResumo && <Loading message="Carregando resumo..." />}

      {resumo && !loadingResumo && (
        <div className="space-y-6">
          {renderSection('3. Formas de Pagamento', (resumo.formas_pagamento || []).filter(i => i.valor !== 'N/A'), 'forma_pagamento', Wallet)}
          {renderSection('4. Bandeiras', (resumo.bandeiras || []).filter(i => i.valor !== 'N/A'), 'bandeira', CreditCard)}
          {renderSection('5. Recebíveis', (resumo.recebiveis || []).filter(i => i.valor !== 'N/A'), 'lancamento', DollarSign)}
          {renderSection('6. Status', resumo.status || [], 'status', Info)}

          {/* 7. Ferramenta de Taxa BC */}
          <Panel>
              <PanelHeader icon={RefreshCw}>7. Ferramenta de Aplicar Taxa BC</PanelHeader>
              <PanelBody>
                  <div className="bg-blue-50 p-4 border border-blue-200 rounded text-sm text-blue-800 mb-6">
                      <p><strong>Atenção:</strong> Esta ferramenta aplica uma taxa percentual fixa e recalcula automaticamente o desconto, valor líquido e perda na tabela <code>vendas_calculos</code>.</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                          <div>
                              <label className="text-sm font-medium text-gray-700 mb-1 block">Forma de Pagamento</label>
                              <select 
                                  className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 min-h-[40px]"
                                  value={bcSelectedForma}
                                  onChange={(e) => setBcSelectedForma(e.target.value)}
                                  disabled={loadingBcFiltros || !selectedProcessamento}
                              >
                                  <option value="TODOS">TODOS</option>
                                  {bcFiltros.formas.map(f => <option key={f} value={f}>{f}</option>)}
                              </select>
                          </div>
                          <div>
                              <label className="text-sm font-medium text-gray-700 mb-1 block">Bandeira</label>
                              <select 
                                  className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 min-h-[40px]"
                                  value={bcSelectedBandeira}
                                  onChange={(e) => setBcSelectedBandeira(e.target.value)}
                                  disabled={loadingBcFiltros || !selectedProcessamento}
                              >
                                  <option value="TODOS">TODOS</option>
                                  {bcFiltros.bandeiras.map(b => <option key={b} value={b}>{b}</option>)}
                              </select>
                          </div>
                      </div>

                      <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                              <div>
                                  <label className="text-sm font-medium text-gray-700 mb-1 block">Data Inicial</label>
                                  <Input 
                                      type="date" 
                                      value={bcDataIni} 
                                      onChange={(e) => setBcDataIni(e.target.value)} 
                                      disabled={!selectedProcessamento}
                                  />
                              </div>
                              <div>
                                  <label className="text-sm font-medium text-gray-700 mb-1 block">Data Final</label>
                                  <Input 
                                      type="date" 
                                      value={bcDataFim} 
                                      onChange={(e) => setBcDataFim(e.target.value)}
                                      disabled={!selectedProcessamento}
                                  />
                              </div>
                          </div>
                          <div>
                              <label className="text-sm font-medium text-gray-700 mb-1 block font-bold text-blue-600">Nova Taxa BC (%)</label>
                              <div className="flex gap-2">
                                  <Input 
                                      type="number" 
                                      step="0.0001"
                                      placeholder="Ex: 2.50"
                                      value={bcNovaTaxa}
                                      onChange={(e) => setBcNovaTaxa(e.target.value === '' ? '' : Number(e.target.value))}
                                      className="flex-1"
                                      disabled={!selectedProcessamento}
                                  />
                                  <Button 
                                      variant="primary" 
                                      onClick={handleAplicarTaxaBC}
                                      disabled={!selectedProcessamento || applyingBC || bcNovaTaxa === ''}
                                      loading={applyingBC}
                                  >
                                      🚀 Aplicar Taxa BC
                                  </Button>
                              </div>
                          </div>
                      </div>
                  </div>
              </PanelBody>
          </Panel>
        </div>
      )}

      {/* Edit Modal */}
      <Modal
        isOpen={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        title={`Editar ${actionItem?.item.valor}`}
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">Digite o novo nome para todas as ocorrências de <strong>{actionItem?.item.valor}</strong>:</p>
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
        key={`confirm-${actionItem?.item.valor}-${deleteDialogOpen ? 'open' : 'closed'}`} // Force remount logic
        isOpen={deleteDialogOpen}
        onClose={() => {
            console.log('[DEBUG] Closing dialog via onClose');
            setDeleteDialogOpen(false);
            setActionItem(null);
        }}
        onConfirm={confirmDelete}
        title="Confirmar Remoção"
        message={`Tem certeza que deseja remover todas as ocorrências de "${actionItem?.item.valor}"? (DEBUG: ItemID=${actionItem?.item?.valor})`}
        confirmText={processingAction ? 'Removendo...' : 'Sim, Remover'}
        loading={processingAction}
        variant="danger"
      />

      {/* History Modal */}
      <Modal
        isOpen={historicoOpen}
        onClose={() => setHistoricoOpen(false)}
        title="Histórico de Correções"
      >
        <div className="space-y-4">
          {loadingHistorico ? (
            <Loading message="Carregando histórico..." />
          ) : (
            <div className="max-h-[60vh] overflow-y-auto">
              <Table 
                columns={historyColumns}
                data={historicoData}
                emptyMessage="Nenhuma correção encontrada."
              />
            </div>
          )}
          <div className="flex justify-end mt-4">
            <Button variant="secondary" onClick={() => setHistoricoOpen(false)}>Fechar</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

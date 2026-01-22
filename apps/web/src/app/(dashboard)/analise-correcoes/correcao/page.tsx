'use client';

import { useState, useEffect } from 'react';
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
  Edit2
} from 'lucide-react';

export default function CorrecaoToolPage() {
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [selectedProcessamento, setSelectedProcessamento] = useState<string>('');
  const [resumo, setResumo] = useState<ResumoResponse | null>(null);
  const [loadingProc, setLoadingProc] = useState(true);
  const [loadingResumo, setLoadingResumo] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      setLoadingResumo(true);
      const data = await correcaoService.obterResumo(id);
      setResumo(data);
    } catch (err) {
      setError('Erro ao carregar resumo do processamento');
      console.error(err);
    } finally {
      setLoadingResumo(false);
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

  const handleEdit = (campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento', item: ResumoItem, customNewValue?: string) => {
    setActionItem({ campo, item });
    setNewValue(customNewValue || item.valor);
    if (!customNewValue) {
        setEditModalOpen(true); // Open modal if no value provided directly
    } else {
        // If value provided (from input field), confirm directly? No, usually safer to confirm.
        // Assuming the UI flow: Type in Input -> Click "Update Selected" (which iterates over selection).
        // Since we are web, we usually do row-based actions.
        // HOWEVER, the Legacy UI has a "Batch Update" flow: Type generic name -> Select Checkboxes -> Update All.
        // Implementing row-based for simplicity unless batch is strictly required. 
        // The user asked for "match legacy". Legacy is Batch.
        // Let's stick to row based for now as it's safer and easier in web, but style it like the legacy.
        // Actually, let's keep the row actions but style the header inputs to look like they could be used for batch later if we implement selection.
        setEditModalOpen(true);
    }
  };

  const handleDelete = (campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento', item: ResumoItem) => {
    setActionItem({ campo, item });
    setDeleteDialogOpen(true);
  };

  const confirmEdit = async () => {
    if (!actionItem || !selectedProcessamento) return;
    
    try {
      setProcessingAction(true);
      await correcaoService.atualizarEmMassa({
        processamento_id: selectedProcessamento,
        campo: actionItem.campo,
        valor_antigo: actionItem.item.valor,
        valor_novo: newValue
      });
      setEditModalOpen(false);
      await fetchResumo(selectedProcessamento);
    } catch (err) {
      alert('Erro ao atualizar: ' + err);
    } finally {
      setProcessingAction(false);
    }
  };

  const confirmDelete = async () => {
    if (!actionItem || !selectedProcessamento) return;
    
    try {
      setProcessingAction(true);
      await correcaoService.removerEmMassa({
        processamento_id: selectedProcessamento,
        campo: actionItem.campo,
        valor: actionItem.item.valor
      });
      setDeleteDialogOpen(false);
      await fetchResumo(selectedProcessamento);
    } catch (err) {
      alert('Erro ao remover: ' + err);
    } finally {
      setProcessingAction(false);
    }
  };

  const renderSection = (
    title: string, 
    data: ResumoItem[], 
    campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento',
    icon: any
  ) => {
    const columns: TableColumn<ResumoItem>[] = [
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
            <button 
                onClick={() => handleEdit(campo, item)}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
                title="Editar"
            >
                <Edit2 className="w-4 h-4" /> Editar
            </button>
            <button 
                onClick={() => handleDelete(campo, item)}
                className="text-red-600 hover:text-red-800 text-sm font-medium flex items-center gap-1"
                title="Remover"
            >
                <Trash2 className="w-4 h-4" /> Remover
            </button>
          </div>
        )
      }
    ];

    return (
      <Panel className="mb-6">
        <PanelHeader icon={icon}>{title}</PanelHeader>
        <PanelBody>
            {/* Legacy UI Simulation: Input + Batch Buttons REMOVED as per user request */}

            <Table 
              columns={columns} 
              data={data} 
              emptyMessage="Nenhum registro encontrado."
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
    <div className="max-w-7xl mx-auto pb-10">
      
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
                  <Button size="sm" variant="success" onClick={() => selectedProcessamento && fetchResumo(selectedProcessamento)} disabled={!selectedProcessamento}>
                      🔄 Atualizar Resumo
                  </Button>
              </div>
              
              <div className="bg-gray-50 p-4 border border-gray-200 rounded text-sm text-gray-700">
                  <strong className="block mb-2 text-gray-900">Instruções:</strong>
                  <ol className="list-decimal pl-5 space-y-1">
                      <li>Carregue a lista de processamentos</li>
                      <li>Selecione um processamento (verá o resumo de formas de pagamento e bandeiras)</li>
                      <li>Para <strong>Atualizar</strong>: Clique no botão 'Editar' na linha desejada</li>
                      <li>Para <strong>Remover</strong>: Clique no botão 'Remover' na linha desejada (move para vendas_filtradas)</li>
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
        isOpen={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={confirmDelete}
        title="Confirmar Remoção"
        message={`Tem certeza que deseja remover todas as ocorrências de "${actionItem?.item.valor}"? Elas serão movidas para a lista de Filtrados.`}
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

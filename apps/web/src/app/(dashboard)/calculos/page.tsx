'use client';

import { useState, useEffect } from 'react';
import { Panel, PanelHeader, PanelBody } from '@/components/ui/Panel';
import { Button } from '@/components/ui/Button';
import { Table, TableColumn } from '@/components/ui/Table';
import { Select } from '@/components/ui/Select';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { importacaoApi } from '@/lib/api/importacao';
import { calculoApi, CalculoStats, CalculoResultado } from '@/lib/api/calculo';
import { useCalculo } from '@/hooks/useCalculo';
import { Processamento } from '@/lib/types/importacao';
import { formatCurrency } from '@/lib/utils/formatters';
import {
  Calculator,
  Search,
  Play,
  TrendingDown,
  AlertTriangle,
  Settings,
  BarChart2,
  RefreshCw,
  FileSpreadsheet
} from 'lucide-react';
import { Card } from '@/components/ui/Card';

export default function CalculosToolPage() {
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [selectedProcessamento, setSelectedProcessamento] = useState<string>('');
  const [loadingProc, setLoadingProc] = useState(true);
  
  // Options
  const [tipoTaxa, setTipoTaxa] = useState('log_mensal');
  const [usarTaxaCad, setUsarTaxaCad] = useState(false);
  const [temRecebaRapido, setTemRecebaRapido] = useState(false);
  const [substituir, setSubstituir] = useState(false);

  // States
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<CalculoStats | null>(null);
  const [resultsData, setResultsData] = useState<CalculoResultado[]>([]);

  const { task, loading: loadingAsync, error: errorAsync, startCalculo, resetTask } = useCalculo();

  // Unified error handling
  const displayError = error || errorAsync;

  useEffect(() => {
    fetchProcessamentos();
  }, []);


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

  const handlePreview = async () => {
    if (!selectedProcessamento) return;
    setError(null);
    setSuccessMsg(null);
    setLoadingPreview(true);
    setPreviewData(null);
    
    try {
      const data = await calculoApi.preview({
        processamento_id: selectedProcessamento,
        tipo_taxa: tipoTaxa,
        usar_taxa_cad: usarTaxaCad,
        tem_receba_rapido: temRecebaRapido
      });
      setPreviewData(data);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string };
      setError('Erro ao gerar preview: ' + (e.response?.data?.detail || e.message));
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleProcessar = async () => {
    if (!selectedProcessamento) return;
    if (!confirm('Esta operação pode demorar alguns minutos. Deseja continuar?')) return;
    
    setError(null);
    setSuccessMsg(null);
    resetTask();
    
    startCalculo({
      processamento_id: selectedProcessamento,
      tipo_taxa: tipoTaxa,
      usar_taxa_cad: usarTaxaCad,
      tem_receba_rapido: temRecebaRapido,
      substituir: substituir
    });
  };

  useEffect(() => {
    if (task?.status === 'SUCCESS') {
      setSuccessMsg('Cálculo realizado com sucesso!');
      fetchResultados();
    }
  }, [task?.status]);

  const fetchResultados = async () => {
    if (!selectedProcessamento) return;
    try {
      const data = await calculoApi.listarResultados(selectedProcessamento);
      setResultsData(data);
    } catch (err) {
      console.error('Erro ao buscar resultados', err);
    }
  };

  const resultsColumns: TableColumn<CalculoResultado>[] = [
    { key: 'bandeira', label: 'Bandeira' },
    { key: 'forma_pagamento', label: 'Forma Pgto' },
    { key: 'vl_venda', label: 'Vl. Venda', format: 'currency' },
    { key: 'tx_venda', label: 'Tx. Venda (%)', render: (v) => `${v}%` },
    { key: 'tx_calc', label: 'Tx. Calc (%)', render: (v) => v ? `${v}%` : '-' },
    { 
      key: 'perda', 
      label: 'Diferença (Perda)', 
      render: (v) => <span className={v < 0 ? 'text-red-600 font-bold' : 'text-gray-600'}>{formatCurrency(v || 0)}</span>,
      sortable: true
    },
  ];

  const anyLoading = loadingProc || loadingPreview || loadingAsync;

  return (
    <div className="max-w-7xl mx-auto pb-10 space-y-6">
      
      <div className="border-b pb-4">
        <div className="flex items-center gap-2 text-gray-700 mb-1">
            <Calculator className="w-6 h-6" />
            <h1 className="text-2xl font-bold">Cálculo e Conferência de Taxas</h1>
        </div>
        <p className="text-sm text-gray-500">
            Verifique se as taxas cobradas (Log ou Cadastradas) batem com o esperado. Identifique perdas financeiras.
        </p>
      </div>

      {displayError && <ErrorMessage message={displayError} />}
      {successMsg && (
        <div className="bg-green-50 text-green-700 p-4 rounded border border-green-200 flex items-center gap-2">
            <span>✅</span> {successMsg}
        </div>
      )}

      {/* Progress Bar for Async Task */}
      {task && task.status !== 'SUCCESS' && task.status !== 'FAILED' && (
        <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg space-y-2 animate-pulse">
          <div className="flex justify-between items-center text-sm font-medium text-blue-700">
            <span>{task.message}</span>
            <span>{task.progress}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2.5">
            <div 
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-500" 
              style={{ width: `${task.progress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* 1. Configuração */}
      <Panel>
          <PanelHeader icon={Settings}>Configuração do Cálculo</PanelHeader>
          <PanelBody>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Select Processamento */}
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1 block">1. Selecione o Processamento</label>
                    <div className="flex gap-2">
                        <select
                            className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 min-h-[40px]"
                            value={selectedProcessamento}
                            onChange={(e) => {
                                setSelectedProcessamento(e.target.value);
                                setPreviewData(null);
                                setResultsData([]);
                                setSuccessMsg(null);
                            }}
                            disabled={anyLoading}
                        >
                            <option value="">Selecione...</option>
                            {processamentos.map(p => (
                                <option key={p.id} value={String(p.id)}>
                                    {p.id} - {p.tipo_arquivo} - {p.nome_arquivo}
                                </option>
                            ))}
                        </select>
                        <Button 
                            variant="secondary" 
                            onClick={fetchProcessamentos} 
                            disabled={anyLoading}
                            title="Atualizar lista"
                        >
                            🔄
                        </Button>
                    </div>
                  </div>

                  {/* Options */}
                  <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-gray-700 mb-1 block">2. Tipo de Taxa (Log)</label>
                        <select
                            className="w-full border-gray-300 rounded-md shadow-sm"
                            value={tipoTaxa}
                            onChange={(e) => setTipoTaxa(e.target.value)}
                            disabled={anyLoading}
                        >
                            <option value="log_mensal">Log Mensal (Menor taxa do mês)</option>
                            <option value="log_trimestral">Log Trimestral</option>
                            <option value="log_semestral">Log Semestral</option>
                            <option value="log_anual">Log Anual</option>
                        </select>
                      </div>

                      <div className="flex flex-col gap-2">
                          <label className="flex items-center gap-2 cursor-pointer">
                              <input 
                                type="checkbox" 
                                checked={usarTaxaCad} 
                                onChange={(e) => setUsarTaxaCad(e.target.checked)}
                                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
                                disabled={anyLoading}
                              />
                              <span className="text-sm text-gray-700 font-medium">Usar Taxa CAD quando disponível?</span>
                          </label>

                          <label className="flex items-center gap-2 cursor-pointer">
                              <input 
                                type="checkbox" 
                                checked={temRecebaRapido} 
                                onChange={(e) => setTemRecebaRapido(e.target.checked)}
                                className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4"
                                disabled={anyLoading}
                              />
                              <span className="text-sm text-gray-700 font-medium">Cliente tem Receba Rápido?</span>
                          </label>

                          <label className="flex items-center gap-2 cursor-pointer pt-2 border-t mt-2">
                              <input 
                                type="checkbox" 
                                checked={substituir} 
                                onChange={(e) => setSubstituir(e.target.checked)}
                                className="rounded text-orange-600 focus:ring-orange-500 w-4 h-4"
                                disabled={anyLoading}
                              />
                              <span className="text-sm text-orange-700 font-bold">Substituir cálculo existente?</span>
                          </label>
                      </div>
                  </div>
              </div>

              <div className="flex gap-3 mt-6 pt-4 border-t justify-end">
                  <Button 
                    onClick={handlePreview} 
                    disabled={!selectedProcessamento || anyLoading}
                    loading={loadingPreview}
                    variant="secondary"
                    className="w-40"
                  >
                    {!loadingPreview && <><Search className="w-4 h-4 mr-2" /> Preview</>}
                  </Button>
                  
                   <Button 
                    onClick={handleProcessar} 
                    disabled={!selectedProcessamento || loadingPreview}
                    loading={loadingAsync}
                    variant="primary"
                    className="w-48"
                  >
                    {!loadingAsync && <><Play className="w-4 h-4 mr-2" /> Calcular Taxas</>}
                  </Button>
              </div>

          </PanelBody>
      </Panel>

      {/* 2. Preview Area */}
      {previewData && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
              <Card className="p-4 border-l-4 border-blue-500">
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Resumo Vendas</h3>
                  <div className="space-y-1">
                      <div className="flex justify-between">
                          <span>Total Vendas:</span>
                          <span className="font-bold">{previewData.total_vendas}</span>
                      </div>
                      <div className="flex justify-between">
                          <span>Valor Total:</span>
                          <span className="font-bold text-blue-600">{formatCurrency(previewData.valor_total)}</span>
                      </div>
                      <div className="flex justify-between">
                          <span>Valor Médio:</span>
                          <span className="text-gray-600">{formatCurrency(previewData.valor_medio)}</span>
                      </div>
                  </div>
              </Card>

              <Card className="p-4 border-l-4 border-orange-500">
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Taxas Originais</h3>
                  <div className="space-y-1">
                      <div className="flex justify-between">
                          <span>Média:</span>
                          <span className="font-bold">{previewData.media_taxa_orig != null ? Number(previewData.media_taxa_orig).toFixed(2) : '0.00'}%</span>
                      </div>
                      <div className="flex justify-between text-sm text-gray-600">
                          <span>Mínima:</span>
                          <span>{previewData.min_taxa_orig != null ? Number(previewData.min_taxa_orig).toFixed(2) : '0.00'}%</span>
                      </div>
                      <div className="flex justify-between text-sm text-gray-600">
                          <span>Máxima:</span>
                          <span>{previewData.max_taxa_orig != null ? Number(previewData.max_taxa_orig).toFixed(2) : '0.00'}%</span>
                      </div>
                  </div>
              </Card>

              <Card className="p-4 border-l-4 border-green-500">
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">Estratégia</h3>
                  <div className="space-y-1">
                      <div className="flex justify-between">
                          <span>Via Cadastro:</span>
                          <span className="font-bold">{previewData.vendas_com_cad}</span>
                      </div>
                      <div className="flex justify-between">
                          <span>Via Log ({tipoTaxa}):</span>
                          <span className="font-bold">{previewData.vendas_com_log}</span>
                      </div>
                      {temRecebaRapido && (
                          <div className="mt-2 pt-2 border-t text-xs text-green-700 font-semibold">
                              + Receba Rápido Ativo
                          </div>
                      )}
                  </div>
              </Card>
          </div>
      )}

      {/* 3. Resultados */}
      {resultsData.length > 0 && (
          <Panel>
              <PanelHeader icon={BarChart2}>
                  Resultados (Top 100 Discrepâncias)
              </PanelHeader>
              <PanelBody>
                  <Table
                    columns={resultsColumns}
                    data={resultsData}
                    emptyMessage="Nenhuma discrepância encontrada ou cálculo ainda não realizado."
                  />
                  <div className="mt-3 flex items-center justify-between">
                      <span className="text-xs text-gray-500">Mostrando apenas os 100 maiores desvios.</span>
                      <Button
                        variant="secondary"
                        onClick={() => calculoApi.exportExcel(selectedProcessamento)}
                        disabled={!selectedProcessamento}
                      >
                        <FileSpreadsheet className="w-4 h-4 mr-2 text-green-600" />
                        Exportar Excel (completo)
                      </Button>
                  </div>
              </PanelBody>
          </Panel>
      )}


    </div>
  );
}

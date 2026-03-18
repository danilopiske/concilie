'use client';

import { useState, useEffect } from 'react';
import { Panel, PanelHeader, PanelBody } from '@/components/ui/Panel';
import { Button } from '@/components/ui/Button';
import { Table, TableColumn } from '@/components/ui/Table';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { calculoApi, CalculoHistoryItem, CalculoResultado } from '@/lib/api/calculo';
import { formatCurrency } from '@/lib/utils/formatters';
import { 
  History, 
  Search, 
  Trash2, 
  RefreshCw,
  Calculator,
  BarChart2
} from 'lucide-react';

export default function GestaoCalculosPage() {
  const [history, setHistory] = useState<CalculoHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [resultsData, setResultsData] = useState<CalculoResultado[]>([]);
  const [loadingResults, setLoadingResults] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoadingHistory(true);
      setError(null);
      const data = await calculoApi.getHistory();
      setHistory(data);
    } catch (err) {
      console.error('Erro ao buscar histórico de cálculos', err);
      setError('Erro ao carregar histórico de cálculos');
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleDelete = async (calcId: string) => {
    if (!confirm(`Deseja realmente excluir o cálculo ${calcId}?`)) return;
    try {
      await calculoApi.deleteCalculo(calcId);
      setSuccessMsg('Cálculo excluído com sucesso');
      fetchHistory();
      if (resultsData.length > 0 && resultsData[0].calc_id === calcId) {
        setResultsData([]);
      }
    } catch (err) {
      setError('Erro ao excluir cálculo');
    }
  };

  const fetchResultados = async (calcId: string) => {
    try {
      setLoadingResults(true);
      setError(null);
      const data = await calculoApi.listarResultados(calcId);
      setResultsData(data);
    } catch (err) {
      console.error('Erro ao buscar resultados', err);
      setError('Erro ao carregar resultados do cálculo');
    } finally {
      setLoadingResults(false);
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

  return (
    <div className="max-w-7xl mx-auto pb-10 space-y-6">
      <div className="border-b pb-4">
        <div className="flex items-center gap-2 text-gray-700 mb-1">
            <History className="w-6 h-6" />
            <h1 className="text-2xl font-bold">Gestão de Cálculos Salvos</h1>
        </div>
        <p className="text-sm text-gray-500">
            Visualize, analise e gerencie o histórico de cálculos de taxas realizados.
        </p>
      </div>

      {error && <ErrorMessage message={error} />}
      {successMsg && (
        <div className="bg-green-50 text-green-700 p-4 rounded border border-green-200 flex items-center gap-2">
            <span>✅</span> {successMsg}
        </div>
      )}

      {/* Tabela de Histórico */}
      <Panel>
          <PanelHeader icon={History}>
              <div className="flex justify-between items-center w-full pr-4">
                  <span>Histórico de Cálculos</span>
                  <Button variant="secondary" size="sm" onClick={fetchHistory} disabled={loadingHistory}>
                      <RefreshCw className={`w-4 h-4 ${loadingHistory ? 'animate-spin' : ''}`} />
                  </Button>
              </div>
          </PanelHeader>
          <PanelBody>
              {loadingHistory ? (
                  <Loading message="Carregando histórico..." />
              ) : (
                  <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                              <tr>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID do Cálculo</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data Realização</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Qtd Vendas</th>
                                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                              </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                              {history.map((item, index) => (
                                  <tr key={`${item.calc_id}-${index}`} className="hover:bg-gray-50">
                                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.calc_id}</td>
                                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                                              {item.calc_tipo}
                                          </span>
                                      </td>
                                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                          {new Date(item.calc_data).toLocaleString()}
                                      </td>
                                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-bold">
                                          {item.total_registros}
                                      </td>
                                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                                          <Button 
                                            variant="secondary" 
                                            size="sm"
                                            onClick={() => fetchResultados(item.calc_id)}
                                            title="Ver resultados"
                                          >
                                              <Search className="w-4 h-4" />
                                          </Button>
                                          <Button 
                                            variant="secondary" 
                                            size="sm"
                                            className="text-red-600 hover:text-red-800"
                                            onClick={() => handleDelete(item.calc_id)}
                                            title="Excluir cálculo"
                                          >
                                              <Trash2 className="w-4 h-4" />
                                          </Button>
                                      </td>
                                  </tr>
                              ))}
                              {history.length === 0 && (
                                  <tr>
                                      <td colSpan={5} className="px-6 py-10 text-center text-gray-500 italic">
                                          Nenhum cálculo salvo encontrado.
                                      </td>
                                  </tr>
                              )}
                          </tbody>
                      </table>
                  </div>
              )}
          </PanelBody>
      </Panel>

      {/* Resultados do cálculo selecionado */}
      {(resultsData.length > 0 || loadingResults) && (
          <Panel>
              <PanelHeader icon={BarChart2}>
                  Resultados (Top 100 Discrepâncias) {resultsData.length > 0 && `- ${resultsData[0].calc_id}`}
              </PanelHeader>
              <PanelBody>
                  {loadingResults ? (
                      <Loading message="Carregando resultados..." />
                  ) : (
                      <>
                        <Table 
                          columns={resultsColumns} 
                          data={resultsData} 
                          emptyMessage="Nenhuma discrepância encontrada para este cálculo."
                        />
                        <div className="mt-2 text-right text-xs text-gray-500">
                            Mostrando apenas os 100 maiores desvios.
                        </div>
                      </>
                  )}
              </PanelBody>
          </Panel>
      )}
    </div>
  );
}

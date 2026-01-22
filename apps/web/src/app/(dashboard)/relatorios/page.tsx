'use client';

import { useState, useEffect } from 'react';
import { Panel, PanelHeader, PanelBody } from '@/components/ui/Panel';
import { Button } from '@/components/ui/Button';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { importacaoApi } from '@/lib/api/importacao';
import { relatorioApi, RelatorioResponse } from '@/lib/api/relatorio';
import { Processamento } from '@/lib/types/importacao';
import { 
  FileText, 
  Download, 
  ExternalLink,
  Filter,
  Calendar,
  Settings
} from 'lucide-react';
import { Card } from '@/components/ui/Card';

export default function RelatoriosPage() {
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [selectedProcessamento, setSelectedProcessamento] = useState<string>('');
  const [loadingProc, setLoadingProc] = useState(true);
  
  // Filtros
  const [adquirenteOptions, setAdquirenteOptions] = useState<string[]>(['Todos']);
  const [selectedAdquirente, setSelectedAdquirente] = useState('Todos');
  const [loadingAdquirentes, setLoadingAdquirentes] = useState(false);
  
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  
  const [tipoRelatorio, setTipoRelatorio] = useState<'retroativo' | 'mensal'>('retroativo');
  const [calcTipo, setCalcTipo] = useState('log_mensal');
  
  // Checkboxes
  const [incluirFiltradas, setIncluirFiltradas] = useState(false);
  const [incluirRecebiveis, setIncluirRecebiveis] = useState(false);
  const [apenasPerdas, setApenasPerdas] = useState(false);

  // States
  const [loadingAction, setLoadingAction] = useState(false);
  const [result, setResult] = useState<RelatorioResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProcessamentos();
  }, []);

  useEffect(() => {
    if (selectedProcessamento) {
      fetchAdquirentes(selectedProcessamento);
    } else {
      setAdquirenteOptions(['Todos']);
      setSelectedAdquirente('Todos');
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

  const fetchAdquirentes = async (procId: string) => {
    try {
      setLoadingAdquirentes(true);
      const data = await relatorioApi.getAdquirentes(procId);
      setAdquirenteOptions(data);
      setSelectedAdquirente('Todos');
    } catch (err) {
      console.error('Erro ao carregar adquirentes', err);
    } finally {
      setLoadingAdquirentes(false);
    }
  };

  const handleGerar = async () => {
    if (!selectedProcessamento) return;
    
    setError(null);
    setResult(null);
    setLoadingAction(true);
    
    try {
      const data = await relatorioApi.gerar({
        processamento_id: selectedProcessamento,
        tipo_relatorio: tipoRelatorio,
        calc_tipo: calcTipo,
        adquirente: selectedAdquirente,
        data_inicio: dataInicio || undefined,
        data_fim: dataFim || undefined,
        incluir_filtradas: incluirFiltradas,
        incluir_recebiveis_filtrados: incluirRecebiveis,
        apenas_com_perdas: apenasPerdas
      });
      setResult(data);
    } catch (err: any) {
      setError('Erro ao gerar relatório: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoadingAction(false);
    }
  };

  const openFile = (path: string) => {
    const url = relatorioApi.downloadUrl(path);
    window.open(url, '_blank');
  };

  return (
    <div className="max-w-7xl mx-auto pb-10 space-y-6">
      
      <div className="border-b pb-4">
        <div className="flex items-center gap-2 text-gray-700 mb-1">
            <FileText className="w-6 h-6" />
            <h1 className="text-2xl font-bold">Relatórios de Conciliação</h1>
        </div>
        <p className="text-sm text-gray-500">
            Gere relatórios detalhados (HTML/Excel) para auditoria e conferência.
        </p>
      </div>

      {error && <ErrorMessage message={error} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Filters */}
        <div className="lg:col-span-2 space-y-6">
          <Panel>
            <PanelHeader icon={Settings}>Configuração do Relatório</PanelHeader>
            <PanelBody className="space-y-6">
                
                {/* 1. Processamento */}
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-1 block">Processamento</label>
                  <select
                      className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      value={selectedProcessamento}
                      onChange={(e) => setSelectedProcessamento(e.target.value)}
                      disabled={loadingProc || loadingAction}
                  >
                      <option value="">Selecione...</option>
                      {processamentos.map(p => (
                          <option key={p.id} value={String(p.id)}>
                              {p.id} - {p.tipo_arquivo} - {p.nome_arquivo}
                          </option>
                      ))}
                  </select>
                </div>

                {/* 2. Tipo e Adquirente Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                   <div>
                      <label className="text-sm font-medium text-gray-700 mb-1 block">Tipo de Relatório</label>
                      <div className="flex gap-4 mt-2">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input 
                            type="radio" 
                            name="tipoRelatorio"
                            value="retroativo"
                            checked={tipoRelatorio === 'retroativo'}
                            onChange={() => setTipoRelatorio('retroativo')}
                            className="text-blue-600 focus:ring-blue-500" 
                            disabled={loadingAction}
                          />
                          <span className="text-sm text-gray-700">Retroativo (Completo)</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input 
                            type="radio" 
                            name="tipoRelatorio"
                            value="mensal"
                            checked={tipoRelatorio === 'mensal'}
                            onChange={() => setTipoRelatorio('mensal')} 
                            className="text-blue-600 focus:ring-blue-500"
                            disabled={loadingAction}
                          />
                          <span className="text-sm text-gray-700">Mensal</span>
                        </label>
                      </div>
                   </div>

                   <div>
                      <label className="text-sm font-medium text-gray-700 mb-1 block">
                        Adquirente {loadingAdquirentes && '(Carregando...)'}
                      </label>
                      <select
                          className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                          value={selectedAdquirente}
                          onChange={(e) => setSelectedAdquirente(e.target.value)}
                          disabled={!selectedProcessamento || loadingAdquirentes || loadingAction}
                      >
                          {adquirenteOptions.map(opt => (
                              <option key={opt} value={opt}>{opt}</option>
                          ))}
                      </select>
                   </div>
                </div>

                {/* 3. Dates */}
                <div>
                   <label className="text-sm font-medium text-gray-700 mb-1 block flex items-center gap-2">
                      <Calendar className="w-4 h-4" /> Período (Opcional)
                   </label>
                   <div className="grid grid-cols-2 gap-4">
                      <input 
                        type="date" 
                        className="border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 w-full"
                        value={dataInicio}
                        onChange={(e) => setDataInicio(e.target.value)}
                        disabled={loadingAction}
                      />
                      <input 
                        type="date" 
                        className="border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 w-full"
                        value={dataFim}
                        onChange={(e) => setDataFim(e.target.value)}
                        disabled={loadingAction}
                      />
                   </div>
                </div>

                {/* 4. Options Checkboxes */}
                <div className="space-y-3 pt-2 border-t border-gray-100">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={apenasPerdas} 
                          onChange={(e) => setApenasPerdas(e.target.checked)}
                          className="rounded text-blue-600 focus:ring-blue-500"
                          disabled={loadingAction}
                        />
                        <span className="text-sm text-gray-700">Apenas transações com perdas</span>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={incluirFiltradas} 
                          onChange={(e) => setIncluirFiltradas(e.target.checked)}
                          className="rounded text-blue-600 focus:ring-blue-500"
                          disabled={loadingAction}
                        />
                        <span className="text-sm text-gray-700">Incluir Vendas Filtradas (Removidas)</span>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={incluirRecebiveis} 
                          onChange={(e) => setIncluirRecebiveis(e.target.checked)}
                          className="rounded text-blue-600 focus:ring-blue-500"
                          disabled={loadingAction}
                        />
                        <span className="text-sm text-gray-700">Incluir Recebíveis Filtrados</span>
                    </label>
                </div>

                <div className="pt-4 mt-2 border-t flex justify-end">
                    <Button 
                      onClick={handleGerar}
                      disabled={!selectedProcessamento || loadingAction}
                      className="w-full md:w-auto min-w-[200px]"
                    >
                      {loadingAction ? 'Gerando Relatório...' : 'Gerar Relatório'}
                    </Button>
                </div>

            </PanelBody>
          </Panel>
        </div>

        {/* Right Column: Results/Status */}
        <div className="lg:col-span-1">
           {result ? (
             <Card className="p-6 bg-green-50 border-green-200 h-full animate-in fade-in slide-in-from-right-4 duration-500">
                <div className="flex flex-col h-full items-center justify-center text-center space-y-6">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center text-3xl">
                      ✅
                    </div>
                    <h3 className="text-xl font-bold text-green-800">Sucesso!</h3>
                    <p className="text-sm text-green-700">
                      O relatório foi gerado e salvo no servidor.
                    </p>
                    
                    <div className="w-full space-y-3">
                        {result.html_path && (
                          <Button 
                            variant="primary" 
                            className="w-full flex items-center justify-center gap-2"
                            onClick={() => openFile(result.html_path!)}
                          >
                            <ExternalLink className="w-4 h-4" /> Abrir Relatório HTML
                          </Button>
                        )}
                        
                        {result.excel_path && (
                          <Button 
                            variant="secondary" 
                            className="w-full flex items-center justify-center gap-2"
                            onClick={() => openFile(result.excel_path!)}
                          >
                            <Download className="w-4 h-4" /> Baixar Excel
                          </Button>
                        )}

                       {result.sintetico_path && (
                          <Button 
                            variant="secondary" 
                            className="w-full flex items-center justify-center gap-2"
                            onClick={() => openFile(result.sintetico_path!)}
                          >
                            <FileText className="w-4 h-4" /> Abrir Resumo Sintético
                          </Button>
                        )}
                    </div>
                </div>
             </Card>
           ) : (
             <Card className="p-6 h-full flex flex-col items-center justify-center text-center text-gray-400 border-dashed">
                <FileText className="w-12 h-12 mb-4 opacity-50" />
                <p>Configure os filtros e clique em "Gerar" para visualizar os resultados.</p>
             </Card>
           )}
        </div>

      </div>
    </div>
  );
}

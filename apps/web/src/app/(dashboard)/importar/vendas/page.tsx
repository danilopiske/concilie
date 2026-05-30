'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Checkbox } from '@/components/ui/Checkbox';
import { FileUpload } from '@/components/ui/FileUpload';
import { Breadcrumb } from '@/components/layout';
import { Alert } from '@/components/ui/Alert';
import { importacaoApi } from '@/lib/api/importacao';
import { clientesApi, Cliente } from '@/lib/api/clientes';
import { contextosApi, Contexto } from '@/lib/api/contextos';
import { Processamento } from '@/lib/types/importacao';
import { useImportacao } from '@/hooks/useImportacao';
import {
  History,
  Upload,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
  Layers,
  Search,
  Zap
} from 'lucide-react';

export default function ImportarVendasPage() {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Data Lists
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [contextos, setContextos] = useState<Contexto[]>([]);
  const [ecs, setEcs] = useState<string[]>([]);
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [loadingProcessamentos, setLoadingProcessamentos] = useState(false);
  
  // Form State
  const [clienteId, setClienteId] = useState<string>('');
  const [ec, setEc] = useState<string>('');
  const [layout, setLayout] = useState<string>(''); 
  const [tipoArquivo, setTipoArquivo] = useState<string>('V'); 
  const [continuarProcessamento, setContinuarProcessamento] = useState(false);
  const [processamentoId, setProcessamentoId] = useState<string>('');
  
  const [files, setFiles] = useState<File[] | null>(null);

  // Preview State
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [previewColumns, setPreviewColumns] = useState<string[]>([]);
  const [fileId, setFileId] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [uploadResult, setUploadResult] = useState<any>(null);

  // Hook for Async Import
  const { 
    task, 
    loading: loadingAsync, 
    error: errorAsync, 
    startImport, 
    resetTask,
    setError: setTaskError 
  } = useImportacao();

  const displayError = error || errorAsync;

  // Load initial data
  useEffect(() => {
    async function loadData() {
      try {
        const [clientesData, contextosData] = await Promise.all([
          clientesApi.listar(),
          contextosApi.listar()
        ]);
        setClientes(clientesData);
        setContextos(contextosData);
      } catch (err) {
        console.error('Falha ao carregar dados iniciais', err);
        setError('Não foi possível carregar a lista de clientes ou contextos.');
      }
    }
    loadData();
  }, []);

  // Load ECs when client changes
  useEffect(() => {
    async function loadEcs() {
      if (!clienteId) {
        setEcs([]);
        setEc('');
        return;
      }
      try {
        const ecsData = await clientesApi.listarEcs(parseInt(clienteId));
        setEcs(ecsData);
        if (ecsData.length === 1) {
          setEc(ecsData[0]);
        } else {
          setEc('');
        }
      } catch (err) {
        console.error('Falha ao carregar ECs', err);
      }
    }
    loadEcs();
  }, [clienteId]);

  // Load Processamentos when checkbox checked
  useEffect(() => {
    async function loadProcessamentos() {
      if (!continuarProcessamento) {
        setProcessamentoId('');
        return;
      }
      try {
        setLoadingProcessamentos(true);
        const procData = await importacaoApi.processamentos.listar();
        setProcessamentos(procData);
      } catch (err) {
        console.error('Falha ao carregar processamentos', err);
        setError('Erro ao carregar lista de processamentos.');
      } finally {
        setLoadingProcessamentos(false);
      }
    }
    loadProcessamentos();
  }, [continuarProcessamento]);

  // Sync client and EC when processamentoId changes
  useEffect(() => {
    if (continuarProcessamento && processamentoId) {
      const selectedProc = processamentos.find(p => String(p.id) === String(processamentoId));
      if (selectedProc) {
        if (selectedProc.cliente_id) {
          setClienteId(String(selectedProc.cliente_id));
        }
        if (selectedProc.ec_id) {
          setEc(selectedProc.ec_id);
        }
      }
    }
  }, [processamentoId, continuarProcessamento, processamentos]);

  // Removing inline polling useEffect since it's now in the hook

  const handleUploadPreview = async () => {
    if (!files || files.length === 0) {
      setError('Por favor, selecione um ou mais arquivos (ou um ZIP).');
      return;
    }
    if (!layout) {
      setError('Por favor, selecione o Layout (Contexto).');
      return;
    }
    if (!clienteId) {
      setError('Por favor, selecione um cliente.');
      return;
    }
    if (!ec) {
      setError('Por favor, selecione ou informe o EC.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      setPreviewData([]);
      setFileId(null);
      
      const response = await importacaoApi.upload(
        files,
        parseInt(clienteId),
        ec,
        layout, 
        tipoArquivo
      );

      setPreviewData(response.preview || []);
      setPreviewColumns(response.columns || []);
      setFileId(response.file_id);
      setUploadResult(response);
      
      if (response.total_rows_preview === 0) {
        setError(`Atenção: Os arquivos foram lidos (${response.total_files}), mas nenhuma linha foi mapeada. Verifique se o Layout '${layout}' possui regras de De-Para ativas.`);
        setSuccess(null);
        return;
      }

      if (response.is_partial) {
        setSuccess(`Preview do lote: Sorteados ${response.files_in_preview} de ${response.total_files} arquivos para amostra (~${response.total_rows_preview} linhas). Ao clicar em "Gravar", os arquivos originais inteiros serão processados.`);
      } else {
        setSuccess(`Arquivos analisados! Mostrando ${response.total_files} arquivo(s). Amostra rápida gerada com ${response.total_rows_preview} linhas iniciais. Ao clicar em "Gravar", o arquivo completo (todas as linhas) será processado em segundo plano.`);
      }
      
    } catch (err: unknown) {
      console.error(err);
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Ocorreu um erro ao enviar o arquivo. Tente novamente.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmar = async () => {
    if (!fileId) return;
    
    if (continuarProcessamento && !processamentoId) {
      setError('Por favor, selecione o ID do processamento para continuar.');
      return;
    }

    resetTask();
    setError(null);
    setSuccess(null);
    
    startImport({
      file_id: fileId,
      cliente_id: parseInt(clienteId),
      ec_id: ec,
      contexto: layout,
      tipo: tipoArquivo,
      processamentoid: continuarProcessamento ? processamentoId : undefined
    });
  };

  useEffect(() => {
    if (task?.status === 'SUCCESS') {
      setSuccess('Importação finalizada com sucesso! Verifique o painel de processamentos.');
      setFileId(null);
      setPreviewData([]);
      setFiles(null);
    }
  }, [task?.status]);

  return (
    <div className="max-w-6xl mx-auto">
      <Breadcrumb
        items={[
          { label: 'Importar' },
          { label: 'Vendas' },
        ]}
      />

      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Importar Vendas
        </h1>
        <p className="text-gray-600">
          Envie arquivos de vendas para conciliação.
        </p>
      </div>

      <Card className="p-6">
        <div className="space-y-6">
          
          {displayError && (
            <Alert variant="error">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <div className="flex flex-col">
                  <strong>Erro no Processamento</strong>
                  <span className="text-sm opacity-90">{displayError}</span>
                </div>
              </div>
            </Alert>
          )}

          {(success || task?.status === 'SUCCESS') && (
            <Alert variant="success">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                <span>{success || task?.message || 'Importação concluída com sucesso!'}</span>
              </div>
            </Alert>
          )}

          {/* Progress Section (Glassmorphism) */}
          {task && (task.status === 'PROCESSING' || task.status === 'PENDING') && (
            <div className="relative overflow-hidden bg-blue-100/30 backdrop-blur-md border border-blue-200/50 p-6 rounded-xl shadow-inner animate-in fade-in zoom-in duration-300">
               <div className="flex justify-between items-end mb-3">
                 <div className="space-y-1">
                   <h3 className="text-sm font-bold text-blue-900 flex items-center gap-2">
                      <Zap className="w-4 h-4 text-blue-600 animate-pulse" />
                      {task.status === 'PENDING' ? 'Aguardando Início...' : 'Processando dados...'}
                   </h3>
                   <p className="text-xs text-blue-700/80 italic font-medium">
                     {task.message}
                   </p>
                 </div>
                 <div className="text-right">
                    <span className="text-2xl font-black text-blue-900 tracking-tighter">
                      {task.progress}<span className="text-sm font-bold opacity-50">%</span>
                    </span>
                 </div>
               </div>
               
               <div className="relative w-full bg-blue-900/10 rounded-full h-4 overflow-hidden border border-blue-900/5">
                 <div 
                   className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-blue-500 via-blue-600 to-blue-400 h-full rounded-full transition-all duration-700 ease-out shadow-[0_0_15px_rgba(37,99,235,0.4)]" 
                   style={{ width: `${task.progress}%` }}
                 >
                    <div className="absolute inset-0 bg-[linear-gradient(45deg,rgba(255,255,255,0.2)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.2)_50%,rgba(255,255,255,0.2)_75%,transparent_75%,transparent)] bg-[length:20px_20px] animate-[stripe-move_1s_linear_infinite]"></div>
                 </div>
               </div>
               
               <div className="mt-3 flex justify-between items-center text-[10px] uppercase font-bold text-blue-900/40 tracking-widest">
                  <span>Importação em Segundo Plano</span>
                  <span>Não feche esta aba</span>
               </div>
            </div>
          )}

          <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
             <Checkbox
                label="Continuar processamento anterior"
                checked={continuarProcessamento}
                onChange={setContinuarProcessamento}
                disabled={loading}
             />
             
             {continuarProcessamento && (
                <div className="mt-4">
                    <Select
                        label="ID do Processamento"
                        placeholder={loadingProcessamentos ? "Carregando processamentos..." : "Selecione um processamento..."}
                        value={processamentoId}
                        onChange={(e) => setProcessamentoId(e.target.value)}
                        disabled={loading || loadingProcessamentos}
                        options={processamentos.map(p => ({
                            value: p.id,
                            label: `${p.id} - ${p.data_inicio} (${p.status})`
                        }))}
                    />
                    {loadingProcessamentos && <p className="text-xs text-blue-600 mt-1 animate-pulse">Buscando processamentos recentes...</p>}
                </div>
             )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Select
              label="Cliente"
              value={clienteId}
              onChange={(e) => setClienteId(e.target.value)}
              disabled={loading || (continuarProcessamento && !!processamentoId)}
              placeholder="Selecione um cliente..."
              options={clientes.map(c => ({
                value: c.cliente_id,
                label: `${c.cliente_id} - ${c.nome_fantasia || c.razao_social}`
              }))}
            />

            <Select
              label="Layout / Adquirente"
              placeholder="Selecione o layout (ex: CIELO)..."
              value={layout}
              onChange={(e) => setLayout(e.target.value)}
              disabled={loading}
              options={contextos.map(c => ({
                value: c.nome,
                label: c.nome
              }))}
            />

            {ecs.length > 0 ? (
              <Select
                label="EC (Estabelecimento)"
                placeholder="Selecione o EC..."
                value={ec}
                onChange={(e) => setEc(e.target.value)}
                disabled={loading || !clienteId}
                options={ecs.map(e => ({ value: e, label: e }))}
              />
            ) : (
                <div className="flex flex-col gap-1">
                 <Input
                    label="EC (Estabelecimento)"
                    placeholder="Ex: 123456789"
                    value={ec}
                    onChange={(e) => setEc(e.target.value)}
                    disabled={loading || !clienteId}
                />
                 {clienteId && <span className="text-xs text-gray-500">Nenhum EC cadastrado para este cliente. Informe um novo.</span>}
                </div>
            )}

            <Select
                label="Tipo de Arquivo"
                value={tipoArquivo}
                onChange={(e) => setTipoArquivo(e.target.value)}
                disabled={loading}
                options={[
                    { value: 'V', label: 'Venda (V)' },
                    { value: 'L', label: 'Lançamento (L)' },
                    { value: 'R', label: 'Recebível (R)' },
                ]}
            />
          </div>

          <div className="border-t pt-6">
            <h3 className="text-lg font-medium mb-4">Arquivo de Vendas</h3>
            <FileUpload
              accept=".txt,.csv,.xlsx,.xls,.zip"
              multiple={true}
              onFileSelect={(f) => {
                  setFiles(f);
                  setFileId(null); 
                  setPreviewData([]);
                  setSuccess(null);
                  setError(null);
              }}
              selectedFile={files}
              loading={loading}
              error={null}
            />
            <p className="text-sm text-gray-500 mt-2">
              Formatos aceitos: Texto (EDI), CSV ou Excel.
            </p>
          </div>
          
           {/* Preview Table */}
           {previewData.length > 0 && (
              <div className="mt-8 border rounded-lg overflow-hidden">
                  <div className="bg-gray-100 px-4 py-2 border-b font-medium flex justify-between items-center">
                    <span>Amostra dos Dados ({previewData.length} linhas)</span>
                    <span className="text-xs text-gray-500">
                      Total na amostra: {uploadResult?.total_rows_preview} de {uploadResult?.total_files} arquivos 
                      {uploadResult?.is_partial && " (Lote grande - Preview Parcial)"}
                    </span>
                  </div>
                  <div className="overflow-x-auto max-h-[400px]">
                      <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50 sticky top-0">
                              <tr>
                                  {previewColumns.map((col) => (
                                      <th key={col} className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                                          {col}
                                      </th>
                                  ))}
                              </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                              {previewData.map((row, idx) => (
                                  <tr key={idx}>
                                      {previewColumns.map((col) => (
                                          <td key={`${idx}-${col}`} className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                                              {row[col]}
                                          </td>
                                      ))}
                                  </tr>
                              ))}
                          </tbody>
                      </table>
                  </div>
              </div>
           )}

          <div className="flex justify-end gap-3 pt-4">
            {!fileId && (
                <Button 
                onClick={handleUploadPreview} 
                loading={loading}
                disabled={!files || files.length === 0}
                className="w-full md:w-auto"
                >
                {!loading && 'Processar e Normalizar'}
                {loading && 'Processando...'}
                </Button>
            )}

            {fileId && (
                <Button 
                onClick={handleConfirmar} 
                loading={loading}
                className="w-full md:w-auto bg-green-600 hover:bg-green-700"
                >
                {!loading && 'Gravar no Banco'}
                {loading && 'Gravando...'}
                </Button>
            )}
            
            {fileId && (
                 <Button 
                 onClick={() => {
                     setFileId(null);
                     setPreviewData([]);
                     setSuccess(null);
                 }} 
                 variant="secondary"
                 disabled={loading}
                 className="w-full md:w-auto"
                 >
                 Cancelar
                 </Button>
            )}
          </div>

        </div>
      </Card>
    </div>
  );
}

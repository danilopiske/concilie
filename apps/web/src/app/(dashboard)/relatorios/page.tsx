'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Panel, PanelHeader, PanelBody } from '@/components/ui/Panel';
import { Button } from '@/components/ui/Button';
import { importacaoApi } from '@/lib/api/importacao';
import { relatorioApi, ModeloRelatorio, StatusParquet, OpcaoEmissao } from '@/lib/api/relatorio';
import { calculoApi, CalculoHistoryItem } from '@/lib/api/calculo';
import {
  FileText,
  Download,
  ExternalLink,
  Filter,
  Calendar,
  Settings,
  Tags,
  Zap,
  CheckSquare,
  RefreshCw,
  FileDown,
} from 'lucide-react';

export default function RelatoriosPage() {
  // Cálculos
  const [calculos, setCalculos] = useState<CalculoHistoryItem[]>([]);
  const [selectedProcessamento, setSelectedProcessamento] = useState<string>('');
  const [loadingProc, setLoadingProc] = useState(true);
  const [calcTipo, setCalcTipo] = useState('log_mensal');

  // Filtros de configuração
  const [tipoRelatorio, setTipoRelatorio] = useState<'retroativo' | 'mensal'>('retroativo');
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');

  // Adquirentes (carregados na Etapa 1)
  const [adquirente, setAdquirente] = useState<string>('Todos');
  const [adquirenteOptions, setAdquirenteOptions] = useState<string[]>(['Todos']);
  const [loadingAdquirentes, setLoadingAdquirentes] = useState(false);

  // Cache / parquet — chaveado por (processamento_id + adquirente)
  const [statusParquet, setStatusParquet] = useState<StatusParquet | null>(null);
  const [loadingPreproc, setLoadingPreproc] = useState(false);

  // Modelos
  const [modelos, setModelos] = useState<ModeloRelatorio[]>([]);
  const [selectedModelos, setSelectedModelos] = useState<number[]>([]);

  // Opções de emissão (sem adquirente — vem da Etapa 1)
  const [opcoes, setOpcoes] = useState<OpcaoEmissao>({
    incluir_filtradas: false,
    incluir_recebiveis_filtrados: false,
    apenas_com_perdas: false,
  });

  // Resultados
  const [loadingEmitir, setLoadingEmitir] = useState(false);
  const [arquivosEmitidos, setArquivosEmitidos] = useState<Array<{ modelo_id: number; arquivo: string }>>([]);
  const [errosEmissao, setErrosEmissao] = useState<Array<{ modelo_id: number; erro: string }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [emitirError, setEmitirError] = useState<string | null>(null);
  const [emitirConcluido, setEmitirConcluido] = useState(false);

  useEffect(() => {
    fetchProcessamentos();
    fetchModelos();
  }, []);

  useEffect(() => {
    if (selectedProcessamento) {
      setAdquirente('Todos');
      fetchAdquirentes(selectedProcessamento, calcTipo);
      setSelectedModelos([]);
      setArquivosEmitidos([]);
      setErrosEmissao([]);
    } else {
      setStatusParquet(null);
      setAdquirenteOptions(['Todos']);
    }
  }, [selectedProcessamento]);

  useEffect(() => {
    if (selectedProcessamento) fetchAdquirentes(selectedProcessamento, calcTipo);
  }, [calcTipo]);

  // Re-verifica o status do parquet quando muda o adquirente
  useEffect(() => {
    if (selectedProcessamento) {
      checkStatusParquet(selectedProcessamento, adquirente);
      setSelectedModelos([]);
      setArquivosEmitidos([]);
      setErrosEmissao([]);
      setEmitirConcluido(false);
      setEmitirError(null);
    }
  }, [adquirente, selectedProcessamento]);

  const fetchProcessamentos = async () => {
    try {
      setLoadingProc(true);
      const data = await calculoApi.getHistory();
      setCalculos(data);
    } catch {
      setError('Erro ao carregar cálculos');
    } finally {
      setLoadingProc(false);
    }
  };

  const fetchModelos = async () => {
    try {
      const data = await relatorioApi.getModelos();
      setModelos(data);
    } catch {
      /* silencioso */
    }
  };

  const checkStatusParquet = async (procId: string, adq?: string) => {
    try {
      const s = await relatorioApi.getStatusPreprocessamento(procId, adq);
      setStatusParquet(s);
    } catch {
      setStatusParquet(null);
    }
  };

  const fetchAdquirentes = async (procId: string, tipo?: string) => {
    try {
      setLoadingAdquirentes(true);
      const { adquirentes, periodo } = await relatorioApi.getAdquirentes(procId, tipo);
      setAdquirenteOptions(['Todos', ...(adquirentes?.filter((a: string) => a !== 'Todos') || [])]);
      if (periodo?.data_min && periodo?.data_max) {
        setDataInicio(periodo.data_min.split('T')[0]);
        setDataFim(periodo.data_max.split('T')[0]);
      }
    } catch {
      /* silencioso */
    } finally {
      setLoadingAdquirentes(false);
    }
  };

  const handleProcessar = async () => {
    if (!selectedProcessamento) return;
    setLoadingPreproc(true);
    setError(null);
    setSelectedModelos([]);
    setArquivosEmitidos([]);
    setErrosEmissao([]);
    try {
      await relatorioApi.preprocessar({
        processamento_id: selectedProcessamento,
        calc_tipo: calcTipo,
        data_inicio: dataInicio || undefined,
        data_fim: dataFim || undefined,
        adquirente: adquirente === 'Todos' ? undefined : adquirente,
      });
      await checkStatusParquet(selectedProcessamento, adquirente);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Erro no processamento');
    } finally {
      setLoadingPreproc(false);
    }
  };

  const handleEmitir = async () => {
    if (!selectedProcessamento || selectedModelos.length === 0) return;
    setLoadingEmitir(true);
    setErrosEmissao([]);
    setArquivosEmitidos([]);
    setEmitirError(null);
    setEmitirConcluido(false);
    try {
      const res = await relatorioApi.emitir({
        processamento_id: selectedProcessamento,
        modelo_ids: selectedModelos,
        opcoes: { ...opcoes, adquirente: adquirente === 'Todos' ? undefined : adquirente },
      });
      setArquivosEmitidos(res.arquivos);
      setErrosEmissao(res.erros);
      setEmitirConcluido(true);
    } catch (err: any) {
      const raw = err?.response?.data?.detail;
      const detail = Array.isArray(raw)
        ? raw.map((e: any) => `${e.loc?.join('.')}: ${e.msg}`).join(' | ')
        : raw || err?.message || 'Erro ao emitir relatórios';
      setEmitirError(detail);
    } finally {
      setLoadingEmitir(false);
    }
  };

  const toggleModelo = (id: number) => {
    setSelectedModelos(prev =>
      prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
    );
  };

  const openFile = (path: string) => {
    window.open(relatorioApi.downloadUrl(path), '_blank');
  };

  const cacheExiste = statusParquet?.existe ?? false;
  const podeEmitir = cacheExiste && selectedModelos.length > 0;

  return (
    <div className="max-w-4xl mx-auto pb-10 space-y-4">

      {/* Header */}
      <div className="border-b pb-4 flex justify-between items-end">
        <div>
          <div className="flex items-center gap-2 text-gray-700 mb-1">
            <FileText className="w-6 h-6" />
            <h1 className="text-2xl font-bold">Relatórios de Conciliação</h1>
          </div>
          <p className="text-sm text-gray-500">
            Configure o cálculo, processe os dados e emita os modelos desejados.
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/relatorios/modelos">
            <Button variant="secondary" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Modelos
            </Button>
          </Link>
          <Link href="/relatorios/tags">
            <Button variant="secondary" size="sm">
              <Tags className="h-4 w-4 mr-2" />
              Tags
            </Button>
          </Link>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* ETAPA 1 — Configuração + Processar */}
      <Panel>
        <PanelHeader icon={Settings}>
          Etapa 1 — Configuração
        </PanelHeader>
        <PanelBody className="space-y-4">

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Cálculo */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Cálculo (ID)</label>
              <select
                className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                value={selectedProcessamento}
                onChange={e => {
                  const id = e.target.value;
                  setSelectedProcessamento(id);
                  const calc = calculos.find(c => c.calc_id === id);
                  if (calc) setCalcTipo(calc.calc_tipo);
                }}
                disabled={loadingProc}
              >
                <option value="">{loadingProc ? 'Carregando...' : 'Selecione...'}</option>
                {calculos.map((c, idx) => (
                  <option key={`${c.calc_id}-${idx}`} value={c.calc_id}>
                    {c.calc_id} ({c.calc_tipo}) — {new Date(c.calc_data).toLocaleString('pt-BR')}
                  </option>
                ))}
              </select>
            </div>

            {/* Tipo de Relatório */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">Tipo de Relatório</label>
              <div className="flex gap-4 mt-2">
                {(['retroativo', 'mensal'] as const).map(t => (
                  <label key={t} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="tipoRelatorio"
                      value={t}
                      checked={tipoRelatorio === t}
                      onChange={() => {
                        setTipoRelatorio(t);
                        if (t === 'mensal') {
                          const hoje = new Date();
                          const ano = hoje.getFullYear();
                          const mes = String(hoje.getMonth() + 1).padStart(2, '0');
                          const ultimoDia = new Date(ano, hoje.getMonth() + 1, 0).getDate();
                          setDataInicio(`${ano}-${mes}-01`);
                          setDataFim(`${ano}-${mes}-${ultimoDia}`);
                        } else {
                          setDataInicio('');
                          setDataFim('');
                        }
                      }}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700 capitalize">{t}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Período */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 flex items-center gap-1 block">
                <Calendar className="w-4 h-4" /> Período (opcional)
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input type="date" className="border-gray-300 rounded-md shadow-sm w-full"
                  value={dataInicio} onChange={e => setDataInicio(e.target.value)} />
                <input type="date" className="border-gray-300 rounded-md shadow-sm w-full"
                  value={dataFim} onChange={e => setDataFim(e.target.value)} />
              </div>
            </div>

            {/* Adquirente — define qual slot de parquet processar/verificar */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                Adquirente {loadingAdquirentes && <span className="text-gray-400 font-normal">(carregando...)</span>}
              </label>
              <select
                className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                value={adquirente}
                onChange={e => setAdquirente(e.target.value)}
                disabled={loadingAdquirentes || !selectedProcessamento}
              >
                {adquirenteOptions.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
              <p className="text-xs text-gray-400 mt-1">
                Cada combinação cálculo + adquirente tem seu próprio cache de processamento.
              </p>
            </div>
          </div>

          {/* Status cache + botão processar — integrado na configuração */}
          <div className="flex items-center justify-between gap-4 p-3 rounded-lg bg-gray-50 border border-gray-200 mt-2">
            <div className="text-sm">
              {!selectedProcessamento ? (
                <span className="text-gray-400">Selecione um cálculo para verificar o cache.</span>
              ) : cacheExiste ? (
                <span className="text-green-700 font-medium">
                  ✅ Processado ({adquirente}) em {new Date(statusParquet!.gerado_em!).toLocaleString('pt-BR')}
                </span>
              ) : (
                <span className="text-amber-700 font-medium">
                  ⚠️ Sem cache para "{adquirente}". Clique em "Processar" para continuar.
                </span>
              )}
            </div>
            <Button
              variant={cacheExiste ? 'secondary' : 'primary'}
              size="sm"
              onClick={handleProcessar}
              disabled={!selectedProcessamento || loadingPreproc || loadingAdquirentes}
              className="min-w-[160px]"
            >
              {loadingAdquirentes ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Buscando período...</>
              ) : loadingPreproc ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Processando...</>
              ) : cacheExiste ? (
                <><RefreshCw className="w-4 h-4 mr-2" />Re-processar</>
              ) : (
                'Processar Relatório'
              )}
            </Button>
          </div>

        </PanelBody>
      </Panel>

      {/* ETAPA 2 — Selecionar modelos (só exibe com cache) */}
      {cacheExiste && (
        <Panel>
          <PanelHeader icon={CheckSquare}>
            Etapa 2 — Selecionar Modelos
          </PanelHeader>
          <PanelBody>
            <div className="grid grid-cols-2 gap-3">
              {modelos.map(m => (
                <label
                  key={m.id}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedModelos.includes(m.id)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedModelos.includes(m.id)}
                    onChange={() => toggleModelo(m.id)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-800">{m.nome}</p>
                    <p className="text-xs text-gray-400">{m.tipo.toUpperCase()}</p>
                  </div>
                </label>
              ))}
            </div>
          </PanelBody>
        </Panel>
      )}

      {/* ETAPA 3 — Opções de emissão (só exibe com ≥1 modelo selecionado) */}
      {cacheExiste && selectedModelos.length > 0 && (
        <Panel>
          <PanelHeader icon={Filter}>
            Etapa 3 — Opções de Emissão
          </PanelHeader>
          <PanelBody className="space-y-4">

            <div className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={opcoes.incluir_filtradas}
                  onChange={e => setOpcoes(o => ({ ...o, incluir_filtradas: e.target.checked }))}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Incluir vendas filtradas (removidas)</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={opcoes.incluir_recebiveis_filtrados}
                  onChange={e => setOpcoes(o => ({ ...o, incluir_recebiveis_filtrados: e.target.checked }))}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Incluir recebíveis filtrados</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={opcoes.apenas_com_perdas}
                  onChange={e => setOpcoes(o => ({ ...o, apenas_com_perdas: e.target.checked }))}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">Apenas transações com perdas</span>
              </label>
            </div>

            <div className="pt-2 border-t flex items-center justify-between gap-4">
              {emitirError && (
                <p className="text-sm text-red-600 flex-1">❌ {emitirError}</p>
              )}
              <Button
                onClick={handleEmitir}
                disabled={loadingEmitir}
                className="min-w-[180px] ml-auto"
              >
                {loadingEmitir ? (
                  <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Emitindo...</>
                ) : (
                  `Emitir Relatório (${selectedModelos.length})`
                )}
              </Button>
            </div>

          </PanelBody>
        </Panel>
      )}

      {/* Resultados da emissão — sempre visível após emitir */}
      {emitirConcluido && (
        <Panel>
          <PanelHeader icon={Download}>
            Resultados da Emissão
          </PanelHeader>
          <PanelBody className="space-y-3">
            {arquivosEmitidos.length > 0 ? (
              <>
                <p className="text-sm font-medium text-green-700">✅ {arquivosEmitidos.length} arquivo(s) gerado(s):</p>
                {arquivosEmitidos.map(a => {
                  const modelo = modelos.find(m => m.id === a.modelo_id);
                  const isHtml = a.arquivo.toLowerCase().endsWith('.html');
                  return (
                    <div key={a.modelo_id} className="flex gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        className="flex-1 flex items-center justify-center gap-2"
                        onClick={() => openFile(a.arquivo)}
                      >
                        <ExternalLink className="w-4 h-4" />
                        {modelo?.nome ?? `Modelo ${a.modelo_id}`} — Abrir
                      </Button>
                      {isHtml && (
                        <Button
                          variant="secondary"
                          size="sm"
                          className="flex items-center gap-2 whitespace-nowrap"
                          onClick={() => window.open(relatorioApi.downloadPdfUrl(a.arquivo), '_blank')}
                        >
                          <FileDown className="w-4 h-4" />
                          PDF
                        </Button>
                      )}
                    </div>
                  );
                })}
              </>
            ) : (
              <p className="text-sm text-amber-700">⚠️ Nenhum arquivo gerado.</p>
            )}
            {errosEmissao.length > 0 && (
              <div className="text-sm text-red-600 space-y-1 pt-2 border-t">
                <p className="font-medium">Erros:</p>
                {errosEmissao.map(e => (
                  <p key={e.modelo_id}>❌ {modelos.find(m => m.id === e.modelo_id)?.nome ?? `Modelo ${e.modelo_id}`}: {e.erro}</p>
                ))}
              </div>
            )}
          </PanelBody>
        </Panel>
      )}

    </div>
  );
}

'use client';

import { useState, useEffect, useRef } from 'react';
import { AlertTriangle, Download, FileText, RefreshCw, Save } from 'lucide-react';
import { abusividadeApi, AbusividadeDetalhadaResponse } from '@/lib/api/abusividade';
import { importacaoApi, Processamento } from '@/lib/api/importacao';
import { AbusividadeBox } from '@/components/abusividade';
import RelatorioEditor from '@/components/relatorio/RelatorioEditor';

export default function AbusividadePage() {
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [selectedProcessamento, setSelectedProcessamento] = useState('');
  const [loadingProc, setLoadingProc] = useState(true);

  const [analise, setAnalise] = useState<AbusividadeDetalhadaResponse | null>(null);
  const [loadingAnalise, setLoadingAnalise] = useState(false);

  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<'idle' | 'pending' | 'ready' | 'error'>('idle');
  const [fullHtml, setFullHtml] = useState<string>('');
  const [editorContent, setEditorContent] = useState('');
  const [loadingRelatorio, setLoadingRelatorio] = useState(false);
  const [savingEdit, setSavingEdit] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    importacaoApi.processamentos
      .listar(undefined, undefined, true)
      .then(setProcessamentos)
      .catch(() => {})
      .finally(() => setLoadingProc(false));
  }, []);

  useEffect(() => {
    if (!selectedProcessamento) return;
    setAnalise(null);
    setLoadingAnalise(true);
    abusividadeApi
      .analisarDetalhado(selectedProcessamento)
      .then(setAnalise)
      .catch(() => setMsg('Erro ao carregar análise detalhada.'))
      .finally(() => setLoadingAnalise(false));
  }, [selectedProcessamento]);

  const startPolling = (tid: string) => {
    pollingRef.current = setInterval(async () => {
      try {
        const task = await abusividadeApi.getTask(tid);
        if (task.status === 'ready') {
          clearPolling();
          setTaskStatus('ready');
          const url = abusividadeApi.downloadUrl(tid);
          const res = await fetch(url);
          const html = await res.text();
          setFullHtml(html);
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, 'text/html');
          setEditorContent(doc.querySelector('.editor-appendix')?.innerHTML ?? '');
          setLoadingRelatorio(false);
        } else if (task.status === 'error') {
          clearPolling();
          setTaskStatus('error');
          setMsg(`Erro: ${task.error_message || 'Falha ao gerar relatório.'}`);
          setLoadingRelatorio(false);
        }
      } catch {
        clearPolling();
        setTaskStatus('error');
        setLoadingRelatorio(false);
      }
    }, 2000);
  };

  const clearPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => () => clearPolling(), []);

  const handleGerarRelatorio = async () => {
    if (!selectedProcessamento) return;
    setMsg(null);
    setLoadingRelatorio(true);
    setTaskStatus('pending');
    setTaskId(null);
    try {
      const res = await abusividadeApi.gerarRelatorio(selectedProcessamento);
      setTaskId(res.task_id);
      startPolling(res.task_id);
    } catch {
      setMsg('Erro ao iniciar geração do relatório.');
      setLoadingRelatorio(false);
      setTaskStatus('idle');
    }
  };

  const handleSalvarEdicoes = async () => {
    if (!taskId || !fullHtml) return;
    setSavingEdit(true);
    setMsg(null);
    try {
      const updated = fullHtml.replace(
        /<section class="editor-appendix">[\s\S]*?<\/section>/,
        `<section class="editor-appendix">${editorContent}</section>`
      );
      await abusividadeApi.saveEdit(taskId, updated);
      setMsg('Edições salvas com sucesso!');
    } catch {
      setMsg('Erro ao salvar edições.');
    } finally {
      setSavingEdit(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto pb-10 space-y-6">
      {/* Header */}
      <div className="border-b pb-4 flex items-center gap-2">
        <AlertTriangle className="w-6 h-6 text-yellow-600" />
        <h1 className="text-2xl font-bold text-gray-800">Análise de Abusividade</h1>
      </div>

      {msg && (
        <div className={`p-3 rounded text-sm ${msg.startsWith('Erro') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
          {msg}
        </div>
      )}

      {/* Seletor de processamento */}
      <div className="flex items-end gap-4">
        <div className="flex-1">
          <label className="text-sm font-medium text-gray-700 block mb-1">Processamento</label>
          <select
            value={selectedProcessamento}
            onChange={(e) => setSelectedProcessamento(e.target.value)}
            disabled={loadingProc}
            className="w-full border rounded px-3 py-2 text-sm"
          >
            <option value="">{loadingProc ? 'Carregando...' : 'Selecione um processamento'}</option>
            {processamentos.map((p) => (
              <option key={p.id} value={p.id}>{p.nome_arquivo || p.id}</option>
            ))}
          </select>
        </div>
        {selectedProcessamento && (
          <button
            onClick={handleGerarRelatorio}
            disabled={loadingRelatorio}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 text-sm disabled:opacity-50"
          >
            <FileText className="w-4 h-4" />
            {loadingRelatorio ? 'Gerando...' : 'Gerar Relatório Editável'}
          </button>
        )}
      </div>

      {/* Boxes de análise */}
      {loadingAnalise && (
        <div className="flex items-center gap-2 text-gray-500 text-sm">
          <RefreshCw className="w-4 h-4 animate-spin" /> Carregando análise...
        </div>
      )}

      {analise && analise.grupos.length === 0 && (
        <p className="text-gray-500 text-sm">Nenhuma variação de taxa encontrada para este processamento.</p>
      )}

      {analise && analise.grupos.length > 0 && (
        <div className="space-y-4">
          <p className="text-sm text-gray-500">
            {analise.total_transacoes.toLocaleString('pt-BR')} transações analisadas · {analise.grupos.length} grupo(s) bandeira/forma de pagamento
          </p>
          {analise.grupos.map((grupo, i) => (
            <AbusividadeBox key={`${grupo.bandeira}-${grupo.forma_pagamento}-${i}`} grupo={grupo} />
          ))}
        </div>
      )}

      {/* Editor */}
      {taskStatus === 'ready' && (
        <div className="border rounded-lg overflow-hidden space-y-0">
          <div className="bg-gray-50 border-b px-4 py-3 flex items-center justify-between">
            <h2 className="font-medium text-gray-700">Editor de Relatório</h2>
            <div className="flex gap-2">
              <button
                onClick={handleSalvarEdicoes}
                disabled={savingEdit}
                className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                {savingEdit ? 'Salvando...' : 'Salvar Edições'}
              </button>
              {taskId && (
                <a
                  href={abusividadeApi.downloadUrl(taskId)}
                  className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
                >
                  <Download className="w-3.5 h-3.5" /> Baixar HTML
                </a>
              )}
              {taskId && (
                <a
                  href={`${abusividadeApi.downloadUrl(taskId)}?format=pdf`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 rounded text-sm hover:bg-red-100"
                >
                  <FileText className="w-3.5 h-3.5" /> Baixar PDF
                </a>
              )}
            </div>
          </div>
          <div className="p-4">
            <RelatorioEditor
              initialContent={editorContent}
              onChange={setEditorContent}
            />
          </div>
        </div>
      )}
    </div>
  );
}

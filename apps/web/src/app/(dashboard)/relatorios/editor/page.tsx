'use client';

import React, { Suspense, useEffect, useState, useCallback, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Panel } from '@/components/ui/Panel';
import { RelatorioEditor } from '@/components/relatorio/RelatorioEditor';
import { relatorioApi } from '@/lib/api/relatorio';
import { relatorioTagsApi, RelatorioTag } from '@/lib/api/relatorio-tags';
import { AlertCircle, Loader2, Save, Download, ArrowLeft, FileDown } from 'lucide-react';

/**
 * Extrai o conteúdo do .editor-appendix (adições feitas pelo usuário).
 * Retorna string vazia se o relatório ainda não foi editado.
 */
function extractEditableContent(fullHtml: string): string {
  const parser = new DOMParser();
  const doc = parser.parseFromString(fullHtml, 'text/html');
  const appendix = doc.querySelector('.editor-appendix');
  return appendix ? appendix.innerHTML : '';
}

/**
 * Reconstrói o HTML completo injetando o conteúdo TipTap dentro de um
 * .editor-appendix no final do .main-content. O conteúdo original do
 * relatório (tabelas, gráficos, capa) nunca é tocado.
 */
function reconstructHtml(fullHtml: string, newContent: string): string {
  const parser = new DOMParser();
  const doc = parser.parseFromString(fullHtml, 'text/html');
  const mainContent = doc.querySelector('.main-content');
  if (!mainContent) return fullHtml;

  // Remove appendix anterior para não duplicar
  const existing = mainContent.querySelector('.editor-appendix');
  if (existing) existing.remove();

  const isEmpty = !newContent || newContent.trim() === '' || newContent === '<p></p>';
  if (!isEmpty) {
    const appendix = doc.createElement('div');
    appendix.className = 'editor-appendix';
    appendix.setAttribute(
      'style',
      'border-top: 2px solid #223a6b; margin-top: 2rem; padding-top: 1rem;'
    );
    appendix.innerHTML = newContent;
    mainContent.appendChild(appendix);
  }

  return '<!DOCTYPE html>\n' + doc.documentElement.outerHTML;
}

function RelatorioEditorContent() {
  const searchParams = useSearchParams();
  const taskId = searchParams.get('task_id') ?? '';

  const fullHtmlRef = useRef<string>('');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const blobUrlRef = useRef<string | null>(null);
  const [editableContent, setEditableContent] = useState('');
  const [tags, setTags] = useState<RelatorioTag[]>([]);
  const [loadingContent, setLoadingContent] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedPath, setSavedPath] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!taskId) {
      setError('task_id não informado na URL.');
      setLoadingContent(false);
      return;
    }
    try {
      setLoadingContent(true);
      setError(null);

      const task = await relatorioApi.getTaskStatus(taskId);
      if (task.status !== 'SUCCESS' || !task.result_path) {
        setError('Relatório não disponível para edição. Apenas relatórios concluídos podem ser editados.');
        return;
      }

      const downloadUrl = relatorioApi.downloadUrl(task.result_path);
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const res = await fetch(downloadUrl, {
        credentials: 'include',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('Erro ao baixar arquivo do relatório');
      const html = await res.text();

      fullHtmlRef.current = html;
      // TipTap só edita o .editor-appendix (conteúdo adicionado pelo usuário)
      setEditableContent(extractEditableContent(html));
      setSavedPath(task.result_path);

      // Blob URL para o iframe (não requer auth headers)
      if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current);
      const blob = new Blob([html], { type: 'text/html' });
      blobUrlRef.current = URL.createObjectURL(blob);
      setPreviewUrl(blobUrlRef.current);

      const tagsData = await relatorioTagsApi.listar('true');
      setTags(tagsData);
    } catch (err: unknown) {
      setError((err as Error)?.message ?? 'Erro ao carregar relatório.');
    } finally {
      setLoadingContent(false);
    }
  }, [taskId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleSave = async () => {
    if (!taskId) return;
    try {
      setSaving(true);
      setSuccessMsg(null);
      const fullHtml = reconstructHtml(fullHtmlRef.current, editableContent);
      const result = await relatorioApi.saveEdit(taskId, fullHtml);
      // Atualiza fullHtmlRef e previewUrl com o novo HTML salvo
      fullHtmlRef.current = fullHtml;
      setSavedPath(result.path);

      // Atualiza blob URL do iframe com o novo HTML salvo
      if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current);
      const blob = new Blob([fullHtml], { type: 'text/html' });
      blobUrlRef.current = URL.createObjectURL(blob);
      setPreviewUrl(blobUrlRef.current);
      setSuccessMsg('Relatório salvo com sucesso!');
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Erro ao salvar relatório.');
    } finally {
      setSaving(false);
    }
  };

  const handleExport = () => {
    if (!savedPath) return;
    window.open(relatorioApi.downloadUrl(savedPath), '_blank');
  };

  return (
    <div className="space-y-4 p-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500 flex items-center gap-1">
        <Link href="/relatorios" className="hover:text-primary transition-colors">Relatórios</Link>
        <span>/</span>
        <span className="font-semibold text-gray-800">Editor</span>
      </nav>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/relatorios">
            <Button variant="secondary" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Voltar
            </Button>
          </Link>
          <div>
            <h1 className="text-xl font-bold text-gray-800">Editor de Relatório</h1>
            {taskId && <p className="text-xs text-gray-400 font-mono">Task: {taskId}</p>}
          </div>
        </div>

        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleExport} disabled={!savedPath || loadingContent}>
            <Download className="h-4 w-4 mr-2" />
            Exportar HTML
          </Button>
          <Button
            variant="secondary"
            onClick={() => savedPath && window.open(relatorioApi.downloadPdfUrl(savedPath), '_blank')}
            disabled={!savedPath || loadingContent}
          >
            <FileDown className="h-4 w-4 mr-2" />
            Exportar PDF
          </Button>
          <Button variant="primary" onClick={handleSave} disabled={saving || loadingContent}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            Salvar
          </Button>
        </div>
      </div>

      {/* Mensagens */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}
      {successMsg && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
          ✓ {successMsg}
        </div>
      )}

      {loadingContent ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : !error ? (
        <>
          {/* Preview do relatório original (read-only) */}
          {previewUrl && (
            <Panel>
              <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">
                Visualização do relatório (somente leitura)
              </p>
              <iframe
                src={previewUrl}
                className="w-full border-0 rounded"
                style={{ height: '600px' }}
                title="Pré-visualização do relatório"
              />
            </Panel>
          )}

          {/* Editor — adiciona conteúdo ao final do relatório sem tocar no original */}
          <Panel>
            <p className="text-xs text-gray-400 mb-3 font-medium uppercase tracking-wide">
              Adicionar conteúdo ao relatório — digite <kbd className="px-1 bg-gray-100 rounded border text-gray-600">/</kbd> para inserir uma tag
            </p>
            <RelatorioEditor
              initialContent={editableContent}
              tags={tags}
              onChange={setEditableContent}
            />
          </Panel>
        </>
      ) : null}
    </div>
  );
}

export default function RelatorioEditorPage() {
  return (
    <Suspense fallback={<div className="flex justify-center py-16"><span className="text-gray-400">Carregando...</span></div>}>
      <RelatorioEditorContent />
    </Suspense>
  );
}

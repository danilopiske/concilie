'use client';

import { useEffect, useState } from 'react';
import { FileText, Plus, RefreshCw, Download, ChevronDown } from 'lucide-react';
import dynamic from 'next/dynamic';
import {
  contestacaoApi,
  ContestacaoResponse,
  ContestacaoStatus,
} from '@/lib/api/contestacao';

const RelatorioEditor = dynamic(
  () => import('@/components/relatorio/RelatorioEditor').then((m) => m.RelatorioEditor || m.default),
  { ssr: false }
);

const STATUS_CONFIG: Record<ContestacaoStatus, { label: string; icon: string; css: string }> = {
  rascunho:   { label: 'Rascunho',    icon: '📝', css: 'bg-gray-100 text-gray-700' },
  enviada:    { label: 'Enviada',     icon: '📤', css: 'bg-blue-100 text-blue-700' },
  em_analise: { label: 'Em Análise',  icon: '🔄', css: 'bg-yellow-100 text-yellow-700' },
  deferida:   { label: 'Deferida',    icon: '✅', css: 'bg-green-100 text-green-700' },
  indeferida: { label: 'Indeferida',  icon: '❌', css: 'bg-red-100 text-red-700' },
};

const STATUS_OPTIONS: ContestacaoStatus[] = ['rascunho', 'enviada', 'em_analise', 'deferida', 'indeferida'];

export default function ContestacaoPage() {
  const [contestacoes, setContestacoes] = useState<ContestacaoResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filtros
  const [filtroClienteId, setFiltroClienteId] = useState('');
  const [filtroStatus, setFiltroStatus] = useState('');

  // Nova contestação
  const [showNovaForm, setShowNovaForm] = useState(false);
  const [novaClienteId, setNovaClienteId] = useState('');
  const [novaProcessamentoId, setNovaProcessamentoId] = useState('');
  const [gerando, setGerando] = useState(false);
  const [gerarError, setGerarError] = useState<string | null>(null);

  // Editor
  const [editando, setEditando] = useState<ContestacaoResponse | null>(null);
  const [savingEdit, setSavingEdit] = useState(false);

  const carregar = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await contestacaoApi.listar(
        filtroClienteId ? Number(filtroClienteId) : undefined,
        filtroStatus || undefined
      );
      setContestacoes(data);
    } catch {
      setError('Erro ao carregar contestações.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  const totalRecuperar = contestacoes
    .filter((c) => c.status !== 'indeferida')
    .reduce((acc, c) => acc + c.valor_excesso_total, 0);

  const handleGerar = async () => {
    if (!novaClienteId || !novaProcessamentoId) {
      setGerarError('Informe o cliente e o processamento.');
      return;
    }
    setGerando(true);
    setGerarError(null);
    try {
      const { contestacao_id } = await contestacaoApi.gerar(
        Number(novaClienteId),
        Number(novaProcessamentoId)
      );
      setShowNovaForm(false);
      setNovaClienteId('');
      setNovaProcessamentoId('');
      await carregar();
      // Abre o editor da nova contestação
      const nova = await contestacaoApi.obter(contestacao_id);
      setEditando(nova);
    } catch {
      setGerarError('Erro ao gerar contestação. Verifique se há taxas contratadas cadastradas para este cliente e processamento.');
    } finally {
      setGerando(false);
    }
  };

  const handleAtualizarStatus = async (id: string, status: ContestacaoStatus) => {
    try {
      await contestacaoApi.atualizarStatus(id, status);
      await carregar();
    } catch {
      setError('Erro ao atualizar status.');
    }
  };

  const handleSaveEdit = async (html: string) => {
    if (!editando) return;
    setSavingEdit(true);
    try {
      await contestacaoApi.saveEdit(editando.id, html);
      setEditando(null);
      await carregar();
    } catch {
      setError('Erro ao salvar edição.');
    } finally {
      setSavingEdit(false);
    }
  };

  if (editando) {
    return (
      <div className="max-w-6xl mx-auto pb-10 space-y-4">
        <div className="flex items-center gap-3 border-b pb-4">
          <button
            onClick={() => setEditando(null)}
            className="text-gray-500 hover:text-gray-700 text-sm underline"
          >
            ← Voltar
          </button>
          <h1 className="text-lg font-bold text-gray-800">
            Editando Carta — {editando.adquirente} ({editando.periodo_inicio} a {editando.periodo_fim})
          </h1>
          {savingEdit && <span className="text-sm text-gray-400">Salvando...</span>}
        </div>
        <RelatorioEditor
          initialContent={editando.html_carta || ''}
          onSave={handleSaveEdit}
          saveLabel="Salvar Carta"
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto pb-10 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 border-b pb-4">
        <FileText className="w-6 h-6 text-blue-600" />
        <div>
          <h1 className="text-xl font-bold text-gray-800">Módulo de Contestação</h1>
          <p className="text-sm text-gray-500">Geração e acompanhamento de cartas de contestação de taxas</p>
        </div>
        <button
          onClick={() => setShowNovaForm(!showNovaForm)}
          className="ml-auto flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Nova Contestação
        </button>
      </div>

      {/* KPI */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-xl p-5 flex items-center gap-4">
        <div className="text-3xl">💰</div>
        <div>
          <div className="text-xs text-gray-500 uppercase font-semibold">Total a Recuperar</div>
          <div className="text-2xl font-bold text-red-700">
            {totalRecuperar.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
          </div>
          <div className="text-xs text-gray-400">Contestações não indeferidas</div>
        </div>
      </div>

      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      {/* Formulário nova contestação */}
      {showNovaForm && (
        <div className="bg-gray-50 border rounded-xl p-5 space-y-3">
          <h2 className="font-semibold text-gray-700 text-sm">Nova Contestação</h2>
          {gerarError && (
            <div className="p-2 bg-red-50 text-red-600 text-sm rounded">{gerarError}</div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 block mb-1">ID do Cliente *</label>
              <input
                type="number"
                value={novaClienteId}
                onChange={(e) => setNovaClienteId(e.target.value)}
                className="w-full border rounded px-2 py-1.5 text-sm"
                placeholder="ex: 1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">ID do Processamento *</label>
              <input
                type="number"
                value={novaProcessamentoId}
                onChange={(e) => setNovaProcessamentoId(e.target.value)}
                className="w-full border rounded px-2 py-1.5 text-sm"
                placeholder="ex: 42"
              />
            </div>
          </div>
          <div className="flex gap-2 pt-1">
            <button
              onClick={handleGerar}
              disabled={gerando}
              className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${gerando ? 'animate-spin' : ''}`} />
              {gerando ? 'Gerando...' : 'Gerar Carta'}
            </button>
            <button
              onClick={() => { setShowNovaForm(false); setGerarError(null); }}
              className="px-4 py-1.5 border text-sm rounded hover:bg-gray-100"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="flex gap-3 items-end">
        <div>
          <label className="text-xs text-gray-500 block mb-1">Cliente ID</label>
          <input
            type="number"
            value={filtroClienteId}
            onChange={(e) => setFiltroClienteId(e.target.value)}
            className="border rounded px-2 py-1.5 text-sm w-28"
            placeholder="todos"
          />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Status</label>
          <select
            value={filtroStatus}
            onChange={(e) => setFiltroStatus(e.target.value)}
            className="border rounded px-2 py-1.5 text-sm"
          >
            <option value="">Todos</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>{STATUS_CONFIG[s].label}</option>
            ))}
          </select>
        </div>
        <button
          onClick={carregar}
          className="px-3 py-1.5 text-sm bg-gray-100 border rounded hover:bg-gray-200 flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Filtrar
        </button>
      </div>

      {/* Tabela */}
      <div className="bg-white border rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50">
          <h2 className="font-semibold text-gray-700 text-sm">Contestações</h2>
        </div>
        {loading ? (
          <div className="py-10 text-center text-gray-400 text-sm">Carregando...</div>
        ) : contestacoes.length === 0 ? (
          <div className="py-10 text-center text-gray-400 text-sm">Nenhuma contestação encontrada.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                {['Status', 'Cliente', 'Adquirente', 'Período', 'Valor Excesso', 'Criado em', 'Ações'].map((h) => (
                  <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {contestacoes.map((c) => {
                const sc = STATUS_CONFIG[c.status as ContestacaoStatus] ?? STATUS_CONFIG.rascunho;
                return (
                  <tr key={c.id} className="border-b hover:bg-gray-50">
                    <td className="px-3 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${sc.css}`}>
                        {sc.icon} {sc.label}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-gray-500">#{c.cliente_id}</td>
                    <td className="px-3 py-2 font-medium">{c.adquirente}</td>
                    <td className="px-3 py-2 text-xs">
                      {c.periodo_inicio} → {c.periodo_fim}
                    </td>
                    <td className="px-3 py-2 text-red-600 font-semibold">
                      {c.valor_excesso_total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-400">
                      {new Date(c.created_at).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setEditando(c)}
                          className="px-2 py-1 text-xs border rounded hover:bg-blue-50 text-blue-600 border-blue-200"
                        >
                          Editar
                        </button>
                        <a
                          href={contestacaoApi.downloadUrl(c.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="px-2 py-1 text-xs border rounded hover:bg-gray-50 flex items-center gap-1"
                        >
                          <Download className="w-3 h-3" />
                          Download
                        </a>
                        <StatusDropdown
                          current={c.status as ContestacaoStatus}
                          onSelect={(s) => handleAtualizarStatus(c.id, s)}
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function StatusDropdown({
  current,
  onSelect,
}: {
  current: ContestacaoStatus;
  onSelect: (s: ContestacaoStatus) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="px-2 py-1 text-xs border rounded hover:bg-gray-50 flex items-center gap-1"
      >
        Status <ChevronDown className="w-3 h-3" />
      </button>
      {open && (
        <div className="absolute right-0 z-10 mt-1 bg-white border rounded shadow-lg min-w-[130px]">
          {STATUS_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => { onSelect(s); setOpen(false); }}
              className={`w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 ${s === current ? 'font-bold' : ''}`}
            >
              {STATUS_CONFIG[s].icon} {STATUS_CONFIG[s].label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

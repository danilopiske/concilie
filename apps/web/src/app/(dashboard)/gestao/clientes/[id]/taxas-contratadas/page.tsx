'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Plus, Trash2, BarChart3, RefreshCw } from 'lucide-react';
import {
  taxaContratadaApi,
  TaxaContratadaResponse,
  TaxaContratadaCreate,
  ComparacaoResponse,
  DesvioTaxa,
} from '@/lib/api/taxa_contratada';

const STATUS_BADGE: Record<string, string> = {
  ok: 'bg-green-100 text-green-700',
  atencao: 'bg-yellow-100 text-yellow-700',
  abusivo: 'bg-red-100 text-red-700',
};

const STATUS_ICON: Record<string, string> = {
  ok: '🟢',
  atencao: '🟡',
  abusivo: '🔴',
};

interface FormState {
  bandeira: string;
  modalidade: string;
  taxa_contratada: string;
  vigencia_inicio: string;
  vigencia_fim: string;
  observacao: string;
}

const FORM_VAZIO: FormState = {
  bandeira: '',
  modalidade: '',
  taxa_contratada: '',
  vigencia_inicio: '',
  vigencia_fim: '',
  observacao: '',
};

export default function TaxasContratadas() {
  const params = useParams();
  const clienteId = Number(params.id);

  const [taxas, setTaxas] = useState<TaxaContratadaResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(FORM_VAZIO);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  // Comparação
  const [processoId, setProcessoId] = useState('');
  const [comparacao, setComparacao] = useState<ComparacaoResponse | null>(null);
  const [loadingComparacao, setLoadingComparacao] = useState(false);
  const [comparacaoError, setComparacaoError] = useState<string | null>(null);

  const carregar = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await taxaContratadaApi.listar(clienteId);
      setTaxas(data);
    } catch {
      setError('Erro ao carregar taxas contratadas.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
  }, [clienteId]);

  const handleSalvar = async () => {
    if (!form.bandeira || !form.modalidade || !form.taxa_contratada || !form.vigencia_inicio) {
      setError('Preencha bandeira, modalidade, taxa e vigência início.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload: TaxaContratadaCreate = {
        bandeira: form.bandeira,
        modalidade: form.modalidade,
        taxa_contratada: parseFloat(form.taxa_contratada),
        vigencia_inicio: form.vigencia_inicio,
        vigencia_fim: form.vigencia_fim || null,
        observacao: form.observacao || null,
      };
      await taxaContratadaApi.criar(clienteId, payload);
      setForm(FORM_VAZIO);
      setShowForm(false);
      await carregar();
    } catch {
      setError('Erro ao salvar taxa contratada.');
    } finally {
      setSaving(false);
    }
  };

  const handleRemover = async (id: number) => {
    if (!confirm('Remover esta taxa contratada?')) return;
    try {
      await taxaContratadaApi.remover(clienteId, id);
      await carregar();
    } catch {
      setError('Erro ao remover taxa.');
    }
  };

  const handleComparar = async () => {
    if (!processoId.trim()) return;
    setLoadingComparacao(true);
    setComparacaoError(null);
    try {
      const data = await taxaContratadaApi.comparacao(clienteId, processoId.trim());
      setComparacao(data);
    } catch {
      setComparacaoError('Erro ao carregar comparação. Verifique o ID do processamento.');
    } finally {
      setLoadingComparacao(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto pb-10 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 border-b pb-4">
        <Link href="/gestao/clientes" className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-gray-800">Taxas Contratadas</h1>
          <p className="text-sm text-gray-500">Cliente #{clienteId}</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="ml-auto flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Nova Taxa
        </button>
      </div>

      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      {/* Formulário inline */}
      {showForm && (
        <div className="bg-gray-50 border rounded-lg p-4 space-y-3">
          <h2 className="font-medium text-gray-700 text-sm">Nova Taxa Contratada</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <div>
              <label className="text-xs text-gray-500 block mb-1">Bandeira *</label>
              <input
                value={form.bandeira}
                onChange={(e) => setForm({ ...form, bandeira: e.target.value })}
                className="w-full border rounded px-2 py-1.5 text-sm"
                placeholder="ex: Visa"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Modalidade *</label>
              <input
                value={form.modalidade}
                onChange={(e) => setForm({ ...form, modalidade: e.target.value })}
                className="w-full border rounded px-2 py-1.5 text-sm"
                placeholder="ex: Crédito à Vista"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Taxa % *</label>
              <input
                type="number"
                step="0.01"
                value={form.taxa_contratada}
                onChange={(e) => setForm({ ...form, taxa_contratada: e.target.value })}
                className="w-full border rounded px-2 py-1.5 text-sm"
                placeholder="ex: 2.50"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Vigência Início *</label>
              <input
                type="date"
                value={form.vigencia_inicio}
                onChange={(e) => setForm({ ...form, vigencia_inicio: e.target.value })}
                className="w-full border rounded px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Vigência Fim</label>
              <input
                type="date"
                value={form.vigencia_fim}
                onChange={(e) => setForm({ ...form, vigencia_fim: e.target.value })}
                className="w-full border rounded px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Observação</label>
              <input
                value={form.observacao}
                onChange={(e) => setForm({ ...form, observacao: e.target.value })}
                className="w-full border rounded px-2 py-1.5 text-sm"
              />
            </div>
          </div>
          <div className="flex gap-2 pt-1">
            <button
              onClick={handleSalvar}
              disabled={saving}
              className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
            <button
              onClick={() => { setShowForm(false); setForm(FORM_VAZIO); }}
              className="px-4 py-1.5 border text-sm rounded hover:bg-gray-100"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Tabela de taxas */}
      <div className="bg-white border rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50">
          <h2 className="font-semibold text-gray-700 text-sm">Taxas Cadastradas</h2>
        </div>
        {loading ? (
          <div className="py-8 text-center text-gray-400 text-sm">Carregando...</div>
        ) : taxas.length === 0 ? (
          <div className="py-8 text-center text-gray-400 text-sm">Nenhuma taxa contratada cadastrada.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                {['Bandeira', 'Modalidade', 'Taxa %', 'Vigência Início', 'Vigência Fim', 'Observação', ''].map((h) => (
                  <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {taxas.map((t) => (
                <tr key={t.id} className="border-b hover:bg-gray-50">
                  <td className="px-3 py-2">{t.bandeira}</td>
                  <td className="px-3 py-2">{t.modalidade}</td>
                  <td className="px-3 py-2 font-medium">{t.taxa_contratada.toFixed(2)}%</td>
                  <td className="px-3 py-2">{t.vigencia_inicio}</td>
                  <td className="px-3 py-2">{t.vigencia_fim ?? <span className="text-green-600 text-xs">Vigente</span>}</td>
                  <td className="px-3 py-2 text-gray-500 text-xs">{t.observacao ?? '-'}</td>
                  <td className="px-3 py-2">
                    <button
                      onClick={() => handleRemover(t.id)}
                      className="text-red-400 hover:text-red-600"
                      title="Remover"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Painel de comparação */}
      <div className="bg-white border rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50 flex items-center gap-3">
          <BarChart3 className="w-4 h-4 text-blue-600" />
          <h2 className="font-semibold text-gray-700 text-sm">Comparação Contratado vs Cobrado</h2>
        </div>
        <div className="p-4 space-y-3">
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <label className="text-xs text-gray-500 block mb-1">ID do Processamento</label>
              <input
                value={processoId}
                onChange={(e) => setProcessoId(e.target.value)}
                className="w-full border rounded px-2 py-1.5 text-sm"
                placeholder="ex: 42"
              />
            </div>
            <button
              onClick={handleComparar}
              disabled={loadingComparacao || !processoId}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingComparacao ? 'animate-spin' : ''}`} />
              Ver Comparação
            </button>
          </div>

          {comparacaoError && (
            <div className="p-2 bg-red-50 text-red-600 text-sm rounded">{comparacaoError}</div>
          )}

          {comparacao && (
            <div className="space-y-2">
              {comparacao.desvios.length === 0 ? (
                <p className="text-sm text-gray-400">Nenhuma taxa contratada correspondente ao processamento.</p>
              ) : (
                <>
                  <div className="text-sm text-gray-500">
                    Valor excesso total estimado:{' '}
                    <span className="font-semibold text-red-600">
                      {comparacao.valor_excesso_total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </span>
                  </div>
                  <table className="w-full text-sm border rounded overflow-hidden">
                    <thead className="bg-gray-50 border-b">
                      <tr>
                        {['Status', 'Bandeira', 'Modalidade', 'Contratada %', 'Cobrada %', 'Desvio %', 'Excesso Est.', 'Qtd Transações'].map((h) => (
                          <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-500">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {comparacao.desvios.map((d, i) => (
                        <tr key={i} className="border-b hover:bg-gray-50">
                          <td className="px-3 py-2">
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_BADGE[d.status]}`}>
                              {STATUS_ICON[d.status]} {d.status}
                            </span>
                          </td>
                          <td className="px-3 py-2">{d.bandeira}</td>
                          <td className="px-3 py-2">{d.modalidade}</td>
                          <td className="px-3 py-2">{d.taxa_contratada.toFixed(2)}%</td>
                          <td className="px-3 py-2">{d.taxa_media_cobrada.toFixed(2)}%</td>
                          <td className={`px-3 py-2 font-medium ${d.desvio_percentual > 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {d.desvio_percentual > 0 ? '+' : ''}{d.desvio_percentual.toFixed(2)}%
                          </td>
                          <td className="px-3 py-2 text-red-600">
                            {d.valor_excesso_estimado > 0
                              ? d.valor_excesso_estimado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                              : '-'}
                          </td>
                          <td className="px-3 py-2 text-gray-500">{d.quantidade_transacoes}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


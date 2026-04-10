'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Panel, PanelHeader, PanelBody } from '@/components/ui/Panel';
import { Button } from '@/components/ui/Button';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { apiClient } from '@/lib/api/client';
import { ModeloRelatorio } from '@/lib/api/relatorio';
import { Settings, ArrowLeft, Plus, Pencil, X, Check } from 'lucide-react';

const SECOES_DISPONIVEIS = [
  'vendas_calculos',
  'perdas_semestre',
  'taxas_minmax',
  'contagem_transacoes',
  'recebiveis_sumario',
  'dados_bancarios',
  'evidencias',
];

const TIPOS = ['html', 'xml'] as const;

interface ModeloForm {
  nome: string;
  template_arquivo: string;
  tipo: 'html' | 'xml';
  secoes_necessarias: string[];
  ativo: boolean;
}

const formVazio: ModeloForm = {
  nome: '',
  template_arquivo: '',
  tipo: 'html',
  secoes_necessarias: [],
  ativo: true,
};

export default function ModelosRelatorioPage() {
  const [modelos, setModelos] = useState<ModeloRelatorio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [criando, setCriando] = useState(false);
  const [form, setForm] = useState<ModeloForm>(formVazio);
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    fetchModelos();
  }, []);

  const fetchModelos = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<ModeloRelatorio[]>('/relatorios/modelos', {
        params: { apenas_ativos: false },
      });
      setModelos(res.data);
    } catch (err) {
      setError('Erro ao carregar modelos');
    } finally {
      setLoading(false);
    }
  };

  const handleEditar = (m: ModeloRelatorio) => {
    setCriando(false);
    setEditandoId(m.id);
    setForm({
      nome: m.nome,
      template_arquivo: m.template_arquivo ?? '',
      tipo: m.tipo,
      secoes_necessarias: m.secoes_necessarias,
      ativo: m.ativo,
    });
  };

  const handleNovo = () => {
    setEditandoId(null);
    setCriando(true);
    setForm(formVazio);
  };

  const handleCancelar = () => {
    setEditandoId(null);
    setCriando(false);
    setForm(formVazio);
  };

  const handleSalvar = async () => {
    setSalvando(true);
    setError(null);
    try {
      const payload = {
        ...form,
        template_arquivo: form.template_arquivo || null,
      };
      if (criando) {
        await apiClient.post('/relatorios/modelos', payload);
      } else {
        await apiClient.patch(`/relatorios/modelos/${editandoId}`, payload);
      }
      await fetchModelos();
      handleCancelar();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Erro ao salvar modelo');
    } finally {
      setSalvando(false);
    }
  };

  const handleDesativar = async (id: number) => {
    if (!confirm('Desativar este modelo?')) return;
    try {
      await apiClient.delete(`/relatorios/modelos/${id}`);
      await fetchModelos();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Erro ao desativar');
    }
  };

  const toggleSecao = (secao: string) => {
    setForm(prev => ({
      ...prev,
      secoes_necessarias: prev.secoes_necessarias.includes(secao)
        ? prev.secoes_necessarias.filter(s => s !== secao)
        : [...prev.secoes_necessarias, secao],
    }));
  };

  const formulario = criando || editandoId !== null;

  return (
    <div className="max-w-4xl mx-auto pb-10 space-y-6">
      <div className="border-b pb-4 flex justify-between items-end">
        <div>
          <div className="flex items-center gap-2 text-gray-700 mb-1">
            <Settings className="w-6 h-6" />
            <h1 className="text-2xl font-bold">Modelos de Relatório</h1>
          </div>
          <p className="text-sm text-gray-500">
            Cadastre e configure os modelos disponíveis para emissão.
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/relatorios">
            <Button variant="secondary" size="sm">
              <ArrowLeft className="w-4 h-4 mr-1" /> Voltar
            </Button>
          </Link>
          <Button size="sm" onClick={handleNovo} disabled={formulario}>
            <Plus className="w-4 h-4 mr-1" /> Novo Modelo
          </Button>
        </div>
      </div>

      {error && <ErrorMessage message={error} />}

      {/* Formulário */}
      {formulario && (
        <Panel>
          <PanelHeader icon={criando ? Plus : Pencil}>
            {criando ? 'Novo Modelo' : 'Editar Modelo'}
          </PanelHeader>
          <PanelBody className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Nome</label>
                <input
                  type="text"
                  className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  value={form.nome}
                  onChange={e => setForm(p => ({ ...p, nome: e.target.value }))}
                  placeholder="Ex: Analítico Sem Capa"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Arquivo de Template</label>
                <input
                  type="text"
                  className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  value={form.template_arquivo}
                  onChange={e => setForm(p => ({ ...p, template_arquivo: e.target.value }))}
                  placeholder="Ex: template_relatorio.html"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-1 block">Tipo</label>
                <select
                  className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  value={form.tipo}
                  onChange={e => setForm(p => ({ ...p, tipo: e.target.value as 'html' | 'xml' }))}
                >
                  {TIPOS.map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-2 mt-6">
                <input
                  type="checkbox"
                  id="ativo"
                  checked={form.ativo}
                  onChange={e => setForm(p => ({ ...p, ativo: e.target.checked }))}
                  className="rounded text-blue-600"
                />
                <label htmlFor="ativo" className="text-sm text-gray-700 cursor-pointer">Ativo</label>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">Seções necessárias</label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {SECOES_DISPONIVEIS.map(s => (
                  <label key={s} className="flex items-center gap-2 cursor-pointer p-2 rounded border border-gray-200 hover:bg-blue-50 text-sm">
                    <input
                      type="checkbox"
                      checked={form.secoes_necessarias.includes(s)}
                      onChange={() => toggleSecao(s)}
                      className="rounded text-blue-600"
                    />
                    <span className="text-gray-700 font-mono text-xs">{s}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex gap-2 justify-end pt-2 border-t">
              <Button variant="secondary" onClick={handleCancelar} disabled={salvando}>
                <X className="w-4 h-4 mr-1" /> Cancelar
              </Button>
              <Button onClick={handleSalvar} disabled={salvando || !form.nome}>
                <Check className="w-4 h-4 mr-1" /> {salvando ? 'Salvando...' : 'Salvar'}
              </Button>
            </div>
          </PanelBody>
        </Panel>
      )}

      {/* Lista */}
      <Panel>
        <PanelHeader icon={Settings}>Modelos Cadastrados</PanelHeader>
        <PanelBody>
          {loading ? (
            <p className="text-sm text-gray-500">Carregando...</p>
          ) : modelos.length === 0 ? (
            <p className="text-sm text-gray-500">Nenhum modelo cadastrado. Clique em &quot;Novo Modelo&quot;.</p>
          ) : (
            <div className="divide-y">
              {modelos.map(m => (
                <div key={m.id} className={`py-3 flex items-start justify-between gap-4 ${!m.ativo ? 'opacity-50' : ''}`}>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-800">{m.nome}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${m.tipo === 'xml' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                        {m.tipo.toUpperCase()}
                      </span>
                      {!m.ativo && <span className="text-xs text-gray-400">(inativo)</span>}
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{m.template_arquivo ?? '—'}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {m.secoes_necessarias.map(s => (
                        <span key={s} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono">{s}</span>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <Button variant="secondary" size="sm" onClick={() => handleEditar(m)} disabled={formulario}>
                      <Pencil className="w-3.5 h-3.5" />
                    </Button>
                    {m.ativo && (
                      <Button variant="secondary" size="sm" onClick={() => handleDesativar(m.id)} disabled={formulario}>
                        <X className="w-3.5 h-3.5 text-red-500" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </PanelBody>
      </Panel>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { Bell, Plus, Trash2, CheckCircle2 } from 'lucide-react';
import { AlertaConfig, TIPOS_ALERTA, alertasConfigApi } from '@/lib/api/alertasConfig';

export default function AlertasConfigPage() {
  const [alertas, setAlertas] = useState<AlertaConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  // Form state
  const [tipoSelecionado, setTipoSelecionado] = useState(TIPOS_ALERTA[0].value);
  const [threshold, setThreshold] = useState('');
  const [descricao, setDescricao] = useState('');
  const [salvando, setSalvando] = useState(false);

  const carregar = async () => {
    try {
      setLoading(true);
      setErro(null);
      const data = await alertasConfigApi.listar();
      setAlertas(data);
    } catch {
      setErro('Erro ao carregar configurações de alertas.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { carregar(); }, []);

  const handleCriar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!threshold || isNaN(parseFloat(threshold))) return;
    setSalvando(true);
    try {
      await alertasConfigApi.criar({
        tipo_alerta: tipoSelecionado,
        threshold_valor: parseFloat(threshold),
        descricao: descricao || undefined,
      });
      setThreshold('');
      setDescricao('');
      await carregar();
    } catch {
      setErro('Erro ao criar configuração.');
    } finally {
      setSalvando(false);
    }
  };

  const handleToggle = async (alerta: AlertaConfig) => {
    try {
      await alertasConfigApi.atualizar(alerta.id, { ativo: !alerta.ativo });
      await carregar();
    } catch {
      setErro('Erro ao atualizar configuração.');
    }
  };

  const handleRemover = async (id: string) => {
    try {
      await alertasConfigApi.remover(id);
      await carregar();
    } catch {
      setErro('Erro ao remover configuração.');
    }
  };

  const getTipoLabel = (value: string) =>
    TIPOS_ALERTA.find(t => t.value === value)?.label ?? value;

  const getTipoUnidade = (value: string) =>
    TIPOS_ALERTA.find(t => t.value === value)?.unidade ?? '';

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-[#1e3a8a]/10">
          <Bell className="w-6 h-6 text-[#1e3a8a]" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-[#1e3a8a]">Configuração de Alertas</h1>
          <p className="text-sm text-gray-500">Defina thresholds para disparo de alertas automáticos</p>
        </div>
      </div>

      {erro && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {erro}
        </div>
      )}

      {/* Formulário novo alerta */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Plus className="w-4 h-4 text-[#f59e0b]" />
          Adicionar Novo Alerta
        </h2>
        <form onSubmit={handleCriar} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Tipo de Alerta</label>
              <select
                value={tipoSelecionado}
                onChange={e => setTipoSelecionado(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e3a8a]/30"
              >
                {TIPOS_ALERTA.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Threshold ({getTipoUnidade(tipoSelecionado)})
              </label>
              <input
                type="number"
                step="any"
                min="0"
                value={threshold}
                onChange={e => setThreshold(e.target.value)}
                placeholder="Ex: 5"
                required
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e3a8a]/30"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Descrição (opcional)</label>
            <input
              type="text"
              value={descricao}
              onChange={e => setDescricao(e.target.value)}
              placeholder="Ex: Alerta quando taxa varia mais de 5%"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1e3a8a]/30"
            />
          </div>
          <button
            type="submit"
            disabled={salvando}
            className="flex items-center gap-2 bg-[#1e3a8a] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#1e3a8a]/90 disabled:opacity-50 transition-colors"
          >
            <Plus className="w-4 h-4" />
            {salvando ? 'Salvando...' : 'Adicionar Alerta'}
          </button>
        </form>
      </div>

      {/* Lista de alertas */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">Alertas Configurados</h2>
        </div>

        {loading ? (
          <div className="px-6 py-8 text-center text-sm text-gray-400">Carregando...</div>
        ) : alertas.length === 0 ? (
          <div className="px-6 py-8 text-center text-sm text-gray-400">
            Nenhum alerta configurado ainda.
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {alertas.map(alerta => (
              <li key={alerta.id} className="px-6 py-4 flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-gray-800">
                      {getTipoLabel(alerta.tipo_alerta)}
                    </span>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                        alerta.ativo
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {alerta.ativo ? (
                        <><CheckCircle2 className="w-3 h-3" /> Ativo</>
                      ) : (
                        'Inativo'
                      )}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    Threshold: <span className="font-semibold text-[#f59e0b]">
                      {alerta.threshold_valor} {getTipoUnidade(alerta.tipo_alerta)}
                    </span>
                    {alerta.descricao && (
                      <span className="ml-2 text-gray-400">— {alerta.descricao}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleToggle(alerta)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      alerta.ativo
                        ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    {alerta.ativo ? 'Desativar' : 'Ativar'}
                  </button>
                  <button
                    onClick={() => handleRemover(alerta.id)}
                    className="p-1.5 rounded-lg text-red-400 hover:bg-red-50 hover:text-red-600 transition-colors"
                    title="Remover"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

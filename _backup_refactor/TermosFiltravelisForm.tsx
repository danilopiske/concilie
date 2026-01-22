/**
 * Formulário de Gestão de Termos Filtráveis
 */

'use client';

import { useState } from 'react';
import { useTermos } from '@/lib/hooks/useTermos';

interface TermosFiltravelisFormProps {
  ec: string;
  contexto: string;
  onSuccess?: () => void;
}

const TIPOS_TERMO = [
  { value: 'v', label: 'Venda/Lançamento' },
  { value: 'r', label: 'Recebíveis' },
  { value: 'l', label: 'Lançamento (apenas)' },
  { value: 'status', label: 'Status (filtrar por status)' },
];

export function TermosFiltravelisForm({ ec, contexto, onSuccess }: TermosFiltravelisFormProps) {
  const [novoTermo, setNovoTermo] = useState('');
  const [tipoSelecionado, setTipoSelecionado] = useState('v');
  const [mensagem, setMensagem] = useState<{ tipo: 'success' | 'error'; texto: string } | null>(null);

  const { termos, loading, error, adicionar, excluir } = useTermos({ ec, contexto });

  const handleAdicionar = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!novoTermo.trim()) {
      setMensagem({ tipo: 'error', texto: 'Digite um termo para adicionar' });
      return;
    }

    try {
      await adicionar({
        ec,
        termo: novoTermo.toUpperCase(),
        tipo: tipoSelecionado,
        contexto,
      });
      
      setMensagem({ tipo: 'success', texto: `Termo "${novoTermo}" adicionado com sucesso!` });
      setNovoTermo('');
      onSuccess?.();
      
      // Limpar mensagem após 3 segundos
      setTimeout(() => setMensagem(null), 3000);
    } catch (err: any) {
      setMensagem({ tipo: 'error', texto: err.message });
    }
  };

  const handleExcluir = async (termoId: number, termoNome: string) => {
    if (!confirm(`Deseja realmente excluir o termo "${termoNome}"?`)) {
      return;
    }

    try {
      await excluir(termoId);
      setMensagem({ tipo: 'success', texto: `Termo "${termoNome}" excluído com sucesso!` });
      onSuccess?.();
      
      setTimeout(() => setMensagem(null), 3000);
    } catch (err: any) {
      setMensagem({ tipo: 'error', texto: err.message });
    }
  };

  if (!ec) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
        <p className="text-yellow-800 text-sm">
          Selecione um EC para gerenciar termos filtráveis
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Mensagens */}
      {mensagem && (
        <div
          className={`rounded-md p-4 ${
            mensagem.tipo === 'success'
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}
        >
          <p
            className={`text-sm ${
              mensagem.tipo === 'success' ? 'text-green-800' : 'text-red-800'
            }`}
          >
            {mensagem.texto}
          </p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* Informação sobre Termos */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">
          📋 Sobre Termos Filtráveis
        </h4>
        <p className="text-sm text-blue-700 mb-2">
          Os termos cadastrados aqui (ex: &quot;CANCELADO&quot;, &quot;ESTORNO&quot;) serão usados para mover
          transações para a tabela de filtrados, conforme o tipo:
        </p>
        <ul className="text-sm text-blue-700 list-disc list-inside space-y-1">
          <li><strong>v</strong> (Venda/Lançamento): usado para vendas e lançamentos</li>
          <li><strong>r</strong> (Recebíveis): usado para recebíveis</li>
          <li><strong>l</strong> (Lançamento apenas): casos especiais de lançamento</li>
          <li><strong>status</strong>: filtrar por status da transação</li>
        </ul>
      </div>

      {/* Formulário de Adicionar */}
      <div className="border border-gray-200 rounded-lg p-6 bg-white shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Adicionar Novo Termo</h3>
        
        <form onSubmit={handleAdicionar} className="space-y-4">
          <div>
            <label htmlFor="termo" className="block text-sm font-medium text-gray-700 mb-1">
              Termo para Filtrar
            </label>
            <input
              type="text"
              id="termo"
              value={novoTermo}
              onChange={(e) => setNovoTermo(e.target.value)}
              placeholder="Ex: CANCELADO"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="tipo" className="block text-sm font-medium text-gray-700 mb-1">
              Tipo do Termo
            </label>
            <select
              id="tipo"
              value={tipoSelecionado}
              onChange={(e) => setTipoSelecionado(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              {TIPOS_TERMO.map((tipo) => (
                <option key={tipo.value} value={tipo.value}>
                  {tipo.label}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={loading || !novoTermo.trim()}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Adicionando...' : 'Adicionar Termo'}
          </button>
        </form>
      </div>

      {/* Lista de Termos Existentes */}
      <div className="border border-gray-200 rounded-lg p-6 bg-white shadow-sm">
        <h3 className="text-lg font-semibold mb-4">
          Termos Existentes ({termos.length})
        </h3>

        {loading && termos.length === 0 ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-sm text-gray-500">Carregando termos...</p>
          </div>
        ) : termos.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>Nenhum termo cadastrado</p>
            <p className="text-sm mt-1">Adicione termos usando o formulário acima</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Termo
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tipo
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contexto
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {termos.map((termo) => (
                  <tr key={termo.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                      {termo.termo}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {TIPOS_TERMO.find((t) => t.value === termo.tipo)?.label || termo.tipo}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {termo.contexto}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                      <button
                        onClick={() => handleExcluir(termo.id, termo.termo)}
                        disabled={loading}
                        className="text-red-600 hover:text-red-900 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Excluir
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

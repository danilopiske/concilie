/**
 * Formulário de Gestão de Termos Filtráveis
 */

'use client';

import { useState } from 'react';
import { useTermos } from '@/lib/hooks/useTermos';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { Table, TableColumn } from '@/components/ui/Table';
import { Alert } from '@/components/ui/Alert';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { TermoFiltravel } from '@/lib/types/gestao'; // Assumindo que existe, se não vou usar any ou definir interface

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
  const [termoParaExcluir, setTermoParaExcluir] = useState<{ id: number; nome: string } | null>(null);

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

  const confirmarExclusao = (termoId: number, termoNome: string) => {
    setTermoParaExcluir({ id: termoId, nome: termoNome });
  };

  const handleExcluir = async () => {
    if (!termoParaExcluir) return;

    try {
      await excluir(termoParaExcluir.id);
      setMensagem({ tipo: 'success', texto: `Termo "${termoParaExcluir.nome}" excluído com sucesso!` });
      onSuccess?.();
      setTermoParaExcluir(null);
      
      setTimeout(() => setMensagem(null), 3000);
    } catch (err: any) {
      setMensagem({ tipo: 'error', texto: err.message });
      setTermoParaExcluir(null);
    }
  };

  const columns: TableColumn<any>[] = [
    {
      key: 'termo',
      label: 'Termo',
      render: (valor) => <span className="font-medium text-gray-900">{valor}</span>
    },
    {
      key: 'tipo',
      label: 'Tipo',
      render: (valor) => (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {TIPOS_TERMO.find((t) => t.value === valor)?.label || valor}
        </span>
      )
    },
    {
      key: 'contexto',
      label: 'Contexto',
    },
    {
      key: 'actions',
      label: 'Ações',
      render: (_, termo) => (
        <div className="flex justify-end">
            <Button
                variant="text"
                className="text-red-600 hover:text-red-900"
                onClick={() => confirmarExclusao(termo.id, termo.termo)}
                disabled={loading}
            >
                Excluir
            </Button>
        </div>
      )
    }
  ];

  if (!ec) {
    return (
      <Alert variant="warning">
        Selecione um EC para gerenciar termos filtráveis
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Mensagens */}
      {mensagem && (
        <Alert variant={mensagem.tipo === 'success' ? 'success' : 'error'} onClose={() => setMensagem(null)}>
          {mensagem.texto}
        </Alert>
      )}

      {error && (
        <Alert variant="error">
          {error}
        </Alert>
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
            <Input
              label="Termo para Filtrar"
              value={novoTermo}
              onChange={(e) => setNovoTermo(e.target.value)}
              placeholder="Ex: CANCELADO"
              disabled={loading}
            />
          </div>

          <div>
            <Select
              label="Tipo do Termo"
              value={tipoSelecionado}
              onChange={(e) => setTipoSelecionado(e.target.value)}
              options={TIPOS_TERMO}
              disabled={loading}
            />
          </div>

          <Button
            type="submit"
            disabled={loading || !novoTermo.trim()}
            className="w-full"
          >
            {loading ? 'Adicionando...' : 'Adicionar Termo'}
          </Button>
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
        ) : (
            <Table
                data={termos}
                columns={columns}
                emptyMessage="Nenhum termo cadastrado. Adicione termos usando o formulário acima."
            />
        )}
      </div>

      <ConfirmDialog
        isOpen={!!termoParaExcluir}
        onClose={() => setTermoParaExcluir(null)}
        onConfirm={handleExcluir}
        title="Excluir Termo"
        message={`Deseja realmente excluir o termo "${termoParaExcluir?.nome}"?`}
        confirmText="Excluir"
        variant="danger"
      />
    </div>
  );
}

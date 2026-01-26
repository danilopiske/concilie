'use client';

import { useState, useEffect, useCallback } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Table, TableColumn } from '@/components/ui/Table';
import { Breadcrumb } from '@/components/layout/Breadcrumb';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { importacaoApi } from '@/lib/api/importacao';
import { Processamento } from '@/lib/types/importacao';
import { Modal } from '@/components/ui/Modal';
import { Trash2 } from 'lucide-react';

export default function ProcessamentosPage() {
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchProcessamentos = useCallback(async () => {
    try {
      setLoading(true);
      const data = await importacaoApi.processamentos.listar();
      setProcessamentos(data);
    } catch (err) {
      setError('Erro ao carregar histórico de processamentos');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProcessamentos();
  }, [fetchProcessamentos]);

  const handleDelete = useCallback(async (id: string | number) => {
    if (!window.confirm('Tem certeza que deseja EXCLUIR este processamento? Essa ação não pode ser desfeita e removerá todas as vendas e cálculos associados.')) {
      return;
    }

    try {
      setDeletingId(String(id));
      await importacaoApi.processamentos.deletarMany([String(id)]);
      await fetchProcessamentos();
    } catch (err) {
      console.error(err);
      alert('Erro ao deletar processamento. Verifique o console.');
    } finally {
      setDeletingId(null);
    }
  }, [fetchProcessamentos]);

  const columns: TableColumn<Processamento>[] = [
    { key: 'id', label: 'ID', width: '80px' },
    { key: 'nome_arquivo', label: 'Arquivo' },
    { key: 'tipo_arquivo', label: 'Tipo' },
    { 
      key: 'status', 
      label: 'Status',
      render: (value) => {
        const variants: any = {
          'Sucesso': 'success',
          'Erro': 'error',
          'Processando': 'warning',
          'Pendente': 'default'
        };
        return <Badge variant={variants[value] || 'default'}>{value}</Badge>;
      }
    },
    { key: 'linhas_processadas', label: 'Processadas' },
    { key: 'linhas_erro', label: 'Erros' },
    { key: 'data_inicio', label: 'Início', format: 'date' },
    {
      key: 'actions',
      label: 'Ações',
      width: '100px',
      render: (_, row) => (
        <Button
          variant="secondary" // Changed from 'ghost' which was invalid
          size="sm"
          className="text-red-600 hover:text-red-700 hover:bg-red-50 bg-transparent border-none shadow-none"
          onClick={() => handleDelete(row.id)}
          disabled={!!deletingId}
          title="Excluir"
        >
          {deletingId === String(row.id) ? (
            <span className="text-xs">...</span>
          ) : (
            <Trash2 size={18} />
          )}
        </Button>
      )
    }
  ];

  return (
    <div className="max-w-7xl mx-auto">
      {/* Progress Modal */}
      <Modal
        isOpen={!!deletingId}
        onClose={() => {}} 
        title="Apagando Processamento"
      >
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-200 border-t-red-600 mb-6"></div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Deletando registros...
          </h3>
          <p className="text-gray-600 max-w-md">
            Estamos removendo o processamento e todos os seus dados vinculados (Vendas, Recebíveis, Cálculos).
          </p>
          <div className="mt-4 p-4 bg-yellow-50 rounded-md border border-yellow-200 text-yellow-800 text-sm">
            <strong>Atenção:</strong> Para arquivos grandes (milhões de linhas), isso pode levar alguns minutos. 
            <br/>Por favor, aguarde e <strong>não feche a página</strong>.
          </div>
        </div>
      </Modal>

      <Breadcrumb
        items={[
          { label: 'Importar', href: '/importar/vendas' },
          { label: 'Gestão de Processamentos' },
        ]}
      />

      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Gestão de Processamentos
          </h1>
          <p className="text-gray-600">
            Histórico de arquivos processados e status de importação
          </p>
        </div>
        <Button variant="secondary" onClick={fetchProcessamentos}>
          Atualizar
        </Button>
      </div>

      {error && <ErrorMessage message={error} />}

      <Card>
        {loading ? (
          <Loading message="Carregando histórico..." />
        ) : (
          <Table
            columns={columns}
            data={processamentos}
            emptyMessage="Nenhum processamento encontrado"
          />
        )}
      </Card>
    </div>
  );
}

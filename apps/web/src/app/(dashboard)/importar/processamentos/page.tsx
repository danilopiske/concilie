'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Table, TableColumn } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { Breadcrumb } from '@/components/layout';
import { importacaoApi } from '@/lib/api/importacao';
import { Processamento } from '@/lib/types/importacao';

export default function ProcessamentosPage() {
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProcessamentos = async () => {
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
  };

  useEffect(() => {
    fetchProcessamentos();
  }, []);

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
  ];

  return (
    <div className="max-w-7xl mx-auto">
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

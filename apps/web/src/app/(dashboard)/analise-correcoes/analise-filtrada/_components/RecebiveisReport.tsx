'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Table } from '@/components/ui/Table';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { analistaFiltradaApi, AgregacaoRecebivel } from '@/lib/api/analista';
import { formatCurrency } from '@/lib/utils/formatters';

interface RecebiveisReportProps {
  processamentoId: string;
}

export function RecebiveisReport({ processamentoId }: RecebiveisReportProps) {
  const [data, setData] = useState<AgregacaoRecebivel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!processamentoId) return;
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await analistaFiltradaApi.getRecebiveis(processamentoId);
        setData(result);
      } catch (err) {
        setError('Erro ao carregar recebíveis filtrados');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [processamentoId]);

  if (loading) return <Loading message="Carregando recebíveis..." />;
  if (error) return <ErrorMessage message={error} />;

  if (data.length === 0) {
    return (
      <Card title="Recebíveis — Filtrados">
        <div className="p-4 text-center text-gray-500">Nenhum dado de recebíveis filtrados encontrado.</div>
      </Card>
    );
  }

  return (
    <Card title="Recebíveis — Filtrados">
      <Table
        columns={[
          { key: 'tipo_recebivel', label: 'Lançamento' },
          { key: 'quantidade', label: 'Qtd' },
          { key: 'valor_total', label: 'Valor Total', render: (v) => formatCurrency(v) },
        ]}
        data={data}
        emptyMessage="Nenhum recebível filtrado encontrado"
      />
    </Card>
  );
}

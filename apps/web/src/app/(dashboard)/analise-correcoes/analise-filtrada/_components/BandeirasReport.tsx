'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Table } from '@/components/ui/Table';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { analistaFiltradaApi, AgregacaoBandeira } from '@/lib/api/analista';
import { formatCurrency } from '@/lib/utils/formatters';

interface BandeirasReportProps {
  processamentoId: string;
}

export function BandeirasReport({ processamentoId }: BandeirasReportProps) {
  const [data, setData] = useState<AgregacaoBandeira[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!processamentoId) return;
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await analistaFiltradaApi.getBandeiras(processamentoId);
        setData(result);
      } catch (err) {
        setError('Erro ao carregar bandeiras filtradas');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [processamentoId]);

  if (loading) return <Loading message="Carregando bandeiras..." />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <Card title="Bandeiras — Filtradas">
      <Table
        columns={[
          { key: 'bandeira', label: 'Bandeira' },
          { key: 'quantidade', label: 'Qtd' },
          { key: 'valor_total', label: 'Valor Total', render: (v) => formatCurrency(v) },
          { key: 'valor_medio', label: 'Ticket Médio', render: (v) => formatCurrency(v) },
        ]}
        data={data}
        emptyMessage="Nenhuma bandeira filtrada encontrada"
      />
    </Card>
  );
}

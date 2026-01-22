'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Table } from '@/components/ui/Table';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { analistaApi, AgregacaoBandeira } from '@/lib/api/analista';
import { formatCurrency, formatPercent } from '@/lib/utils/formatters';

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
        const result = await analistaApi.getBandeiras(processamentoId);
        setData(result);
      } catch (err) {
        setError('Erro ao carregar bandeiras');
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
    <Card title="Análise por Bandeira">
      <Table 
        columns={[
          { key: 'bandeira', label: 'Bandeira' },
          { key: 'quantidade', label: 'Qtd' },
          { key: 'valor_total', label: 'Valor Total', render: (v) => formatCurrency(v) },
          { key: 'valor_medio', label: 'Ticket Médio', render: (v) => formatCurrency(v) },
          { key: 'taxa_perc_media', label: 'Taxa Média', render: (v) => formatPercent(v) },
          { key: 'taxa_valor_total', label: 'Total Taxas', render: (v) => formatCurrency(v) },
        ]} 
        data={data}
        emptyMessage="Nenhuma bandeira encontrada"
      />
    </Card>
  );
}

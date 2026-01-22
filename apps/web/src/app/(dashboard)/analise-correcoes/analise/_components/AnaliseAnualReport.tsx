'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Table } from '@/components/ui/Table';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { analistaApi, AgregacaoFormaPagamentoAno } from '@/lib/api/analista';
import { formatCurrency, formatPercent } from '@/lib/utils/formatters';

interface AnaliseAnualReportProps {
  processamentoId: string;
}

export function AnaliseAnualReport({ processamentoId }: AnaliseAnualReportProps) {
  const [data, setData] = useState<AgregacaoFormaPagamentoAno[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!processamentoId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await analistaApi.getFormasPorAno(processamentoId);
        setData(result);
      } catch (err) {
        setError('Erro ao carregar análise anual');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [processamentoId]);

  if (loading) return <Loading message="Carregando análise anual..." />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <Card title="Formas de Pagamento por Ano">
      <Table 
        columns={[
          { key: 'ano', label: 'Ano' },
          { key: 'forma_pagamento', label: 'Forma Pgto' },
          { key: 'quantidade', label: 'Qtd' },
          { key: 'valor_total', label: 'Total', render: (v) => formatCurrency(v) },
          { key: 'valor_medio', label: 'Médio', render: (v) => formatCurrency(v) },
          { key: 'taxa_perc_minima', label: 'Taxa Min', render: (v) => formatPercent(v) },
          { key: 'taxa_perc_maxima', label: 'Taxa Max', render: (v) => formatPercent(v) },
        ]} 
        data={data}
        emptyMessage="Nenhuma informação encontrada"
      />
    </Card>
  );
}

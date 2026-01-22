'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Table } from '@/components/ui/Table';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { analistaApi, AgregacaoPeriodo } from '@/lib/api/analista';
import { formatCurrency } from '@/lib/utils/formatters';

interface PeriodosReportProps {
  processamentoId: string;
  tipo: 'mes' | 'trimestre' | 'semestre' | 'ano';
  titulo: string;
}

export function PeriodosReport({ processamentoId, tipo, titulo }: PeriodosReportProps) {
  const [data, setData] = useState<AgregacaoPeriodo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!processamentoId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await analistaApi.getPeriodos(processamentoId, tipo);
        setData(result);
      } catch (err) {
        setError(`Erro ao carregar por ${tipo}`);
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [processamentoId, tipo]);

  if (loading) return <Loading message={`Carregando ${tipo}...`} />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <Card title={titulo}>
      <Table 
        columns={[
          { key: 'periodo', label: 'Período' },
          { key: 'quantidade', label: 'Qtd' },
          { key: 'valor_total', label: 'Valor Total', render: (v) => formatCurrency(v) },
          { key: 'valor_medio', label: 'Ticket Médio', render: (v) => formatCurrency(v) },
          { key: 'valor_max', label: 'Máximo', render: (v) => formatCurrency(v) },
        ]} 
        data={data}
        emptyMessage={`Nenhum dado por ${tipo} encontrado`}
      />
    </Card>
  );
}

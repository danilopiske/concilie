'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Table } from '@/components/ui/Table';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { analistaApi, AgregacaoRecebivel } from '@/lib/api/analista';
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
        const result = await analistaApi.getRecebiveis(processamentoId);
        setData(result);
      } catch (err) {
        setError('Erro ao carregar recebíveis');
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
          <Card title="Análise de Recebíveis">
              <div className="p-4 text-center text-gray-500">Nenhum dado de recebíveis encontrado para este processamento.</div>
          </Card>
      )
  }

  return (
    <Card title="Análise de Recebíveis">
      <Table 
        columns={[
          { key: 'tipo_recebivel', label: 'Tipo' },
          { key: 'quantidade', label: 'Qtd' },
          { key: 'valor_total', label: 'Valor Total', render: (v) => formatCurrency(v) },
        ]} 
        data={data}
        emptyMessage="Nenhum recebível encontrado"
      />
    </Card>
  );
}

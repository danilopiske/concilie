'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Table } from '@/components/ui/Table';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { analistaFiltradaApi, AgregacaoBandeiraForma } from '@/lib/api/analista';
import { formatCurrency } from '@/lib/utils/formatters';

interface BandeiraFormaReportProps {
  processamentoId: string;
}

export function BandeiraFormaReport({ processamentoId }: BandeiraFormaReportProps) {
  const [data, setData] = useState<AgregacaoBandeiraForma[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!processamentoId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await analistaFiltradaApi.getBandeiraForma(processamentoId);
        setData(result.sort((a, b) => {
          const cmp = String(a.bandeira).localeCompare(String(b.bandeira), 'pt-BR');
          return cmp !== 0 ? cmp : String(a.forma_pagamento).localeCompare(String(b.forma_pagamento), 'pt-BR');
        }));
      } catch (err) {
        setError('Erro ao carregar análise combinada filtrada');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [processamentoId]);

  if (loading) return <Loading message="Carregando análise combinada..." />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <Card title="Análise Combinada — Bandeira × Forma de Pagamento (Filtrada)">
      <Table
        columns={[
          { key: 'bandeira', label: 'Bandeira' },
          { key: 'forma_pagamento', label: 'Forma de Pagamento' },
          { key: 'quantidade', label: 'Qtd' },
          { key: 'valor_total', label: 'Valor Total', render: (v) => formatCurrency(v) },
          { key: 'valor_medio', label: 'Ticket Médio', render: (v) => formatCurrency(v) },
        ]}
        data={data}
        emptyMessage="Nenhum dado filtrado encontrado"
      />
    </Card>
  );
}

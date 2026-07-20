'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Table } from '@/components/ui/Table';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { analistaFiltradaApi, AgregacaoBandeiraFormaAno } from '@/lib/api/analista';
import { formatCurrency } from '@/lib/utils/formatters';

interface BandeiraFormaAnoReportProps {
  processamentoId: string;
}

export function BandeiraFormaAnoReport({ processamentoId }: BandeiraFormaAnoReportProps) {
  const [data, setData] = useState<AgregacaoBandeiraFormaAno[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!processamentoId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await analistaFiltradaApi.getBandeiraFormaPorAno(processamentoId);
        setData(result);
      } catch (err) {
        setError('Erro ao carregar análise combinada filtrada por ano');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [processamentoId]);

  if (loading) return <Loading message="Carregando análise combinada por ano..." />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <Card title="Bandeira × Forma de Pagamento por Ano (Filtrada)">
      <Table
        columns={[
          { key: 'ano', label: 'Ano' },
          { key: 'bandeira', label: 'Bandeira' },
          { key: 'forma_pagamento', label: 'Forma Pgto' },
          { key: 'quantidade', label: 'Qtd' },
          { key: 'valor_total', label: 'Total', render: (v) => formatCurrency(v) },
          { key: 'valor_medio', label: 'Médio', render: (v) => formatCurrency(v) },
        ]}
        data={data}
        emptyMessage="Nenhuma informação filtrada encontrada"
      />
    </Card>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { analistaApi, ConformidadeBandeiraForma } from '@/lib/api/analista';
import { formatCurrency, formatPercent } from '@/lib/utils/formatters';

interface ConformidadeReportProps {
  processamentoId: string;
}

export function ConformidadeReport({ processamentoId }: ConformidadeReportProps) {
  const [data, setData] = useState<ConformidadeBandeiraForma[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!processamentoId) return;
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await analistaApi.getConformidade(processamentoId);
        setData(result.sort((a, b) => {
          const cmp = a.bandeira.localeCompare(b.bandeira, 'pt-BR');
          return cmp !== 0 ? cmp : a.forma_pagamento.localeCompare(b.forma_pagamento, 'pt-BR');
        }));
      } catch (err) {
        setError('Erro ao carregar relatório de conformidade');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [processamentoId]);

  if (loading) return <Loading message="Carregando relatório de conformidade..." />;
  if (error) return <ErrorMessage message={error} />;
  if (data.length === 0) return (
    <Card title="Conformidade — Bandeira × Forma de Pagamento">
      <p className="text-gray-500 text-sm p-4">Nenhum dado calculado. Execute a reconciliação primeiro.</p>
    </Card>
  );

  // Totais
  const totais = data.reduce((acc, row) => ({
    faturamento: acc.faturamento + row.faturamento,
    cielo_retido: acc.cielo_retido + row.cielo_retido,
    cielo_liquido: acc.cielo_liquido + row.cielo_liquido,
    calc_retido: acc.calc_retido + row.calc_retido,
    calc_liquido: acc.calc_liquido + row.calc_liquido,
    nao_conformidade: acc.nao_conformidade + row.nao_conformidade,
    perda_rr: acc.perda_rr + (row.perda_rr ?? 0),
    quantidade: acc.quantidade + row.quantidade,
  }), { faturamento: 0, cielo_retido: 0, cielo_liquido: 0, calc_retido: 0, calc_liquido: 0, nao_conformidade: 0, perda_rr: 0, quantidade: 0 });

  const totalNcPerc = totais.faturamento ? (totais.nao_conformidade / totais.faturamento) * 100 : 0;
  const totalPerda = totais.nao_conformidade + totais.perda_rr;
  const totalPerdaPerc = totais.faturamento ? (totalPerda / totais.faturamento) * 100 : 0;

  const ncClass = (v: number) => v < 0 ? 'text-red-600 font-semibold' : v > 0 ? 'text-green-600' : '';

  return (
    <Card title="Conformidade — Bandeira × Forma de Pagamento">
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-gray-100 border-b border-gray-300">
              <th rowSpan={2} className="border border-gray-300 px-2 py-1 text-left">Bandeira</th>
              <th rowSpan={2} className="border border-gray-300 px-2 py-1 text-left">Forma Pgto</th>
              <th rowSpan={2} className="border border-gray-300 px-2 py-1 text-right">Faturamento</th>
              <th colSpan={2} className="border border-gray-300 px-2 py-1 text-center bg-blue-50">Lançamentos Adquirente</th>
              <th colSpan={2} className="border border-gray-300 px-2 py-1 text-center bg-green-50">Conciliação (Contrato)</th>
              <th colSpan={2} className="border border-gray-300 px-2 py-1 text-center bg-red-50">NC — MDR</th>
              <th className="border border-gray-300 px-2 py-1 text-center bg-orange-50">NC — RR</th>
              <th colSpan={2} className="border border-gray-300 px-2 py-1 text-center bg-red-100">Perda Total</th>
            </tr>
            <tr className="bg-gray-100 border-b border-gray-300 text-xs">
              <th className="border border-gray-300 px-2 py-1 text-right bg-blue-50">Valor Retido</th>
              <th className="border border-gray-300 px-2 py-1 text-right bg-blue-50">%</th>
              <th className="border border-gray-300 px-2 py-1 text-right bg-green-50">Valor Retido</th>
              <th className="border border-gray-300 px-2 py-1 text-right bg-green-50">%</th>
              <th className="border border-gray-300 px-2 py-1 text-right bg-red-50">Valor</th>
              <th className="border border-gray-300 px-2 py-1 text-right bg-red-50">%</th>
              <th className="border border-gray-300 px-2 py-1 text-right bg-orange-50">Valor</th>
              <th className="border border-gray-300 px-2 py-1 text-right bg-red-100">Valor</th>
              <th className="border border-gray-300 px-2 py-1 text-right bg-red-100">%</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i} className="hover:bg-gray-50 border-b border-gray-200">
                <td className="border border-gray-200 px-2 py-1">{row.bandeira}</td>
                <td className="border border-gray-200 px-2 py-1">{row.forma_pagamento}</td>
                <td className="border border-gray-200 px-2 py-1 text-right">{formatCurrency(row.faturamento)}</td>
                <td className="border border-gray-200 px-2 py-1 text-right bg-blue-50">{formatCurrency(row.cielo_retido)}</td>
                <td className="border border-gray-200 px-2 py-1 text-right bg-blue-50">{formatPercent(row.cielo_taxa_media ?? 0)}</td>
                <td className="border border-gray-200 px-2 py-1 text-right bg-green-50">{formatCurrency(row.calc_retido)}</td>
                <td className="border border-gray-200 px-2 py-1 text-right bg-green-50">{formatPercent(row.calc_taxa_media ?? 0)}</td>
                <td className={`border border-gray-200 px-2 py-1 text-right bg-red-50 ${ncClass(row.nao_conformidade)}`}>{formatCurrency(row.nao_conformidade)}</td>
                <td className={`border border-gray-200 px-2 py-1 text-right bg-red-50 ${ncClass(row.nao_conformidade_perc ?? 0)}`}>{formatPercent(row.nao_conformidade_perc ?? 0)}</td>
                <td className={`border border-gray-200 px-2 py-1 text-right bg-orange-50 ${ncClass(row.perda_rr ?? 0)}`}>{(row.perda_rr ?? 0) !== 0 ? formatCurrency(row.perda_rr ?? 0) : '-'}</td>
                {(() => { const t = row.nao_conformidade + (row.perda_rr ?? 0); const p = row.faturamento ? t / row.faturamento * 100 : 0; return (<><td className={`border border-gray-200 px-2 py-1 text-right bg-red-100 font-semibold ${ncClass(t)}`}>{formatCurrency(t)}</td><td className={`border border-gray-200 px-2 py-1 text-right bg-red-100 ${ncClass(p)}`}>{formatPercent(p)}</td></>); })()}
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-gray-200 font-bold border-t-2 border-gray-400 text-xs">
              <td colSpan={2} className="border border-gray-300 px-2 py-1">** TOTAL GERAL **</td>
              <td className="border border-gray-300 px-2 py-1 text-right">{formatCurrency(totais.faturamento)}</td>
              <td className="border border-gray-300 px-2 py-1 text-right bg-blue-100">{formatCurrency(totais.cielo_retido)}</td>
              <td className="border border-gray-300 px-2 py-1 text-right bg-blue-100">
                {formatPercent(totais.faturamento ? (totais.cielo_retido / totais.faturamento) * 100 : 0)}
              </td>
              <td className="border border-gray-300 px-2 py-1 text-right bg-green-100">{formatCurrency(totais.calc_retido)}</td>
              <td className="border border-gray-300 px-2 py-1 text-right bg-green-100">
                {formatPercent(totais.faturamento ? (totais.calc_retido / totais.faturamento) * 100 : 0)}
              </td>
              <td className={`border border-gray-300 px-2 py-1 text-right bg-red-100 ${ncClass(totais.nao_conformidade)}`}>{formatCurrency(totais.nao_conformidade)}</td>
              <td className={`border border-gray-300 px-2 py-1 text-right bg-red-100 ${ncClass(totalNcPerc)}`}>{formatPercent(totalNcPerc)}</td>
              <td className={`border border-gray-300 px-2 py-1 text-right bg-orange-100 ${ncClass(totais.perda_rr)}`}>{totais.perda_rr !== 0 ? formatCurrency(totais.perda_rr) : '-'}</td>
              <td className={`border border-gray-300 px-2 py-1 text-right bg-red-200 font-bold ${ncClass(totalPerda)}`}>{formatCurrency(totalPerda)}</td>
              <td className={`border border-gray-300 px-2 py-1 text-right bg-red-200 ${ncClass(totalPerdaPerc)}`}>{formatPercent(totalPerdaPerc)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </Card>
  );
}

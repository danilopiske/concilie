'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card } from '@/components/ui/Card';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import {
  analistaApi,
  ConformidadeBandeiraForma,
  ConformidadePeriodoRow,
} from '@/lib/api/analista';
import { formatCurrency, formatPercent } from '@/lib/utils/formatters';

interface ConformidadeReportProps {
  processamentoId: string;
}

type TipoPeriodo = 'ano' | 'semestre' | 'mes';

const TIPO_LABELS: Record<TipoPeriodo, string> = {
  ano: 'Anual',
  semestre: 'Semestral',
  mes: 'Mensal',
};

async function exportarExcel(
  resumo: ConformidadeBandeiraForma[],
  periodo: ConformidadePeriodoRow[],
  tipoPeriodo: TipoPeriodo,
) {
  const XLSX = await import('xlsx');

  // ── Aba 1: Resumo Geral ────────────────────────────────────────────────────
  const resumoRows = resumo.map(r => ({
    Bandeira: r.bandeira,
    'Forma Pgto': r.forma_pagamento,
    Faturamento: r.faturamento,
    'Adquirente Retido (R$)': r.cielo_retido,
    'Adquirente Taxa (%)': r.cielo_taxa_media ?? 0,
    'Contrato Retido (R$)': r.calc_retido,
    'Contrato Taxa (%)': r.calc_taxa_media ?? 0,
    'NC-MDR (R$)': r.nao_conformidade,
    'NC-MDR (%)': r.nao_conformidade_perc ?? 0,
    'NC-RR (R$)': r.perda_rr ?? 0,
    'Perda Total (R$)': r.nao_conformidade + (r.perda_rr ?? 0),
    'Perda Total (%)':
      r.faturamento ? ((r.nao_conformidade + (r.perda_rr ?? 0)) / r.faturamento) * 100 : 0,
  }));

  // ── Aba 2: Por Período ────────────────────────────────────────────────────
  const periodoLabel = TIPO_LABELS[tipoPeriodo];
  const periodoRows = periodo.map(r => ({
    [periodoLabel]: r.periodo,
    Bandeira: r.bandeira,
    'Forma Pgto': r.forma_pagamento,
    Qtd: r.quantidade,
    'Faturamento (R$)': r.faturamento,
    'Taxa Adquirente (%)': r.cielo_taxa_media ?? 0,
    'Taxa Contratada (%)': r.calc_taxa_media ?? 0,
    'Adquirente Retido (R$)': r.cielo_retido,
    'Contrato Retido (R$)': r.calc_retido,
    'NC-MDR (R$)': r.nao_conformidade,
    'NC-MDR (%)': r.nao_conformidade_perc ?? 0,
    'NC-RR (R$)': r.perda_rr ?? 0,
    'Perda Total (R$)': r.nao_conformidade + (r.perda_rr ?? 0),
    'Perda Total (%)':
      r.faturamento ? ((r.nao_conformidade + (r.perda_rr ?? 0)) / r.faturamento) * 100 : 0,
  }));

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(resumoRows), 'Conformidade Geral');
  XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(periodoRows), `Por ${periodoLabel}`);
  XLSX.writeFile(wb, `conformidade_${tipoPeriodo}_${new Date().toISOString().slice(0, 10)}.xlsx`);
}

const ncClass = (v: number) => (v < 0 ? 'text-red-600 font-semibold' : v > 0 ? 'text-green-600' : '');

export function ConformidadeReport({ processamentoId }: ConformidadeReportProps) {
  const [resumo, setResumo] = useState<ConformidadeBandeiraForma[]>([]);
  const [periodo, setPeriodo] = useState<ConformidadePeriodoRow[]>([]);
  const [tipoPeriodo, setTipoPeriodo] = useState<TipoPeriodo>('ano');
  const [loading, setLoading] = useState(true);
  const [loadingPeriodo, setLoadingPeriodo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (!processamentoId) return;
    const fetch = async () => {
      try {
        setLoading(true);
        const result = await analistaApi.getConformidade(processamentoId);
        setResumo(
          result.sort((a, b) => {
            const cmp = a.bandeira.localeCompare(b.bandeira, 'pt-BR');
            return cmp !== 0 ? cmp : a.forma_pagamento.localeCompare(b.forma_pagamento, 'pt-BR');
          }),
        );
      } catch {
        setError('Erro ao carregar relatório de conformidade');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [processamentoId]);

  const carregarPeriodo = useCallback(
    async (tipo: TipoPeriodo) => {
      if (!processamentoId) return;
      try {
        setLoadingPeriodo(true);
        const result = await analistaApi.getConformidadePeriodo(processamentoId, tipo);
        setPeriodo(result);
      } catch {
        setPeriodo([]);
      } finally {
        setLoadingPeriodo(false);
      }
    },
    [processamentoId],
  );

  useEffect(() => {
    carregarPeriodo(tipoPeriodo);
  }, [tipoPeriodo, carregarPeriodo]);

  const handleExport = async () => {
    setExporting(true);
    try {
      await exportarExcel(resumo, periodo, tipoPeriodo);
    } finally {
      setExporting(false);
    }
  };

  if (loading) return <Loading message="Carregando relatório de conformidade..." />;
  if (error) return <ErrorMessage message={error} />;
  if (resumo.length === 0)
    return (
      <Card title="Conformidade — Bandeira × Forma de Pagamento">
        <p className="text-gray-500 text-sm p-4">
          Nenhum dado calculado. Execute a reconciliação primeiro.
        </p>
      </Card>
    );

  const totais = resumo.reduce(
    (acc, r) => ({
      faturamento: acc.faturamento + r.faturamento,
      cielo_retido: acc.cielo_retido + r.cielo_retido,
      calc_retido: acc.calc_retido + r.calc_retido,
      nao_conformidade: acc.nao_conformidade + r.nao_conformidade,
      perda_rr: acc.perda_rr + (r.perda_rr ?? 0),
    }),
    { faturamento: 0, cielo_retido: 0, calc_retido: 0, nao_conformidade: 0, perda_rr: 0 },
  );
  const totalPerda = totais.nao_conformidade + totais.perda_rr;
  const totalPerdaPerc = totais.faturamento ? (totalPerda / totais.faturamento) * 100 : 0;
  const totalNcPerc = totais.faturamento ? (totais.nao_conformidade / totais.faturamento) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* ── Botão exportar ── */}
      <div className="flex justify-end">
        <button
          onClick={handleExport}
          disabled={exporting}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-lg shadow transition-colors disabled:opacity-60"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3" />
          </svg>
          {exporting ? 'Exportando...' : 'Exportar Excel'}
        </button>
      </div>

      {/* ── Tabela resumo geral ── */}
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
              {resumo.map((row, i) => {
                const t = row.nao_conformidade + (row.perda_rr ?? 0);
                const p = row.faturamento ? (t / row.faturamento) * 100 : 0;
                return (
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
                    <td className={`border border-gray-200 px-2 py-1 text-right bg-red-100 font-semibold ${ncClass(t)}`}>{formatCurrency(t)}</td>
                    <td className={`border border-gray-200 px-2 py-1 text-right bg-red-100 ${ncClass(p)}`}>{formatPercent(p)}</td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr className="bg-gray-200 font-bold border-t-2 border-gray-400 text-xs">
                <td colSpan={2} className="border border-gray-300 px-2 py-1">** TOTAL GERAL **</td>
                <td className="border border-gray-300 px-2 py-1 text-right">{formatCurrency(totais.faturamento)}</td>
                <td className="border border-gray-300 px-2 py-1 text-right bg-blue-100">{formatCurrency(totais.cielo_retido)}</td>
                <td className="border border-gray-300 px-2 py-1 text-right bg-blue-100">{formatPercent(totais.faturamento ? (totais.cielo_retido / totais.faturamento) * 100 : 0)}</td>
                <td className="border border-gray-300 px-2 py-1 text-right bg-green-100">{formatCurrency(totais.calc_retido)}</td>
                <td className="border border-gray-300 px-2 py-1 text-right bg-green-100">{formatPercent(totais.faturamento ? (totais.calc_retido / totais.faturamento) * 100 : 0)}</td>
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

      {/* ── Taxas por Período ── */}
      <Card title="Taxas Consideradas por Período — Bandeira × Forma de Pagamento">
        {/* Seletor de período */}
        <div className="flex gap-2 mb-4">
          {(Object.keys(TIPO_LABELS) as TipoPeriodo[]).map(t => (
            <button
              key={t}
              onClick={() => setTipoPeriodo(t)}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
                tipoPeriodo === t
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
              }`}
            >
              {TIPO_LABELS[t]}
            </button>
          ))}
        </div>

        {loadingPeriodo ? (
          <div className="py-8 text-center text-sm text-gray-500">Carregando...</div>
        ) : periodo.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-500">Nenhum dado para o período selecionado.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="bg-gray-100 border-b border-gray-300">
                  <th className="border border-gray-300 px-2 py-1 text-left">{TIPO_LABELS[tipoPeriodo]}</th>
                  <th className="border border-gray-300 px-2 py-1 text-left">Bandeira</th>
                  <th className="border border-gray-300 px-2 py-1 text-left">Forma Pgto</th>
                  <th className="border border-gray-300 px-2 py-1 text-right">Qtd</th>
                  <th className="border border-gray-300 px-2 py-1 text-right">Faturamento</th>
                  <th className="border border-gray-300 px-2 py-1 text-right bg-blue-50">Taxa Adquirente (%)</th>
                  <th className="border border-gray-300 px-2 py-1 text-right bg-green-50">Taxa Contratada (%)</th>
                  <th className="border border-gray-300 px-2 py-1 text-right bg-blue-50">Adquirente Retido</th>
                  <th className="border border-gray-300 px-2 py-1 text-right bg-green-50">Contrato Retido</th>
                  <th className="border border-gray-300 px-2 py-1 text-right bg-red-50">NC-MDR</th>
                  <th className="border border-gray-300 px-2 py-1 text-right bg-red-50">NC-MDR %</th>
                  <th className="border border-gray-300 px-2 py-1 text-right bg-orange-50">NC-RR</th>
                  <th className="border border-gray-300 px-2 py-1 text-right bg-red-100">Perda Total</th>
                  <th className="border border-gray-300 px-2 py-1 text-right bg-red-100">Perda %</th>
                </tr>
              </thead>
              <tbody>
                {periodo.map((row, i) => {
                  const t = row.nao_conformidade + (row.perda_rr ?? 0);
                  const p = row.faturamento ? (t / row.faturamento) * 100 : 0;
                  return (
                    <tr key={i} className="hover:bg-gray-50 border-b border-gray-200">
                      <td className="border border-gray-200 px-2 py-1 font-medium">{row.periodo}</td>
                      <td className="border border-gray-200 px-2 py-1">{row.bandeira}</td>
                      <td className="border border-gray-200 px-2 py-1">{row.forma_pagamento}</td>
                      <td className="border border-gray-200 px-2 py-1 text-right">{row.quantidade.toLocaleString('pt-BR')}</td>
                      <td className="border border-gray-200 px-2 py-1 text-right">{formatCurrency(row.faturamento)}</td>
                      <td className="border border-gray-200 px-2 py-1 text-right bg-blue-50">{formatPercent(row.cielo_taxa_media ?? 0)}</td>
                      <td className="border border-gray-200 px-2 py-1 text-right bg-green-50 font-semibold">{formatPercent(row.calc_taxa_media ?? 0)}</td>
                      <td className="border border-gray-200 px-2 py-1 text-right bg-blue-50">{formatCurrency(row.cielo_retido)}</td>
                      <td className="border border-gray-200 px-2 py-1 text-right bg-green-50">{formatCurrency(row.calc_retido)}</td>
                      <td className={`border border-gray-200 px-2 py-1 text-right bg-red-50 ${ncClass(row.nao_conformidade)}`}>{formatCurrency(row.nao_conformidade)}</td>
                      <td className={`border border-gray-200 px-2 py-1 text-right bg-red-50 ${ncClass(row.nao_conformidade_perc ?? 0)}`}>{formatPercent(row.nao_conformidade_perc ?? 0)}</td>
                      <td className={`border border-gray-200 px-2 py-1 text-right bg-orange-50 ${ncClass(row.perda_rr ?? 0)}`}>{(row.perda_rr ?? 0) !== 0 ? formatCurrency(row.perda_rr ?? 0) : '-'}</td>
                      <td className={`border border-gray-200 px-2 py-1 text-right bg-red-100 font-semibold ${ncClass(t)}`}>{formatCurrency(t)}</td>
                      <td className={`border border-gray-200 px-2 py-1 text-right bg-red-100 ${ncClass(p)}`}>{formatPercent(p)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

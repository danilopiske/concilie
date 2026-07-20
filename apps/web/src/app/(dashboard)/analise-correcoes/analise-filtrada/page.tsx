'use client';

import { useState, useEffect } from 'react';
import { Panel, PanelBody } from '@/components/ui/Panel';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import { importacaoApi } from '@/lib/api/importacao';
import { Processamento } from '@/lib/types/importacao';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { Filter } from 'lucide-react';

import { BandeirasReport } from './_components/BandeirasReport';
import { FormasPagamentoReport } from './_components/FormasPagamentoReport';
import { RecebiveisReport } from './_components/RecebiveisReport';
import { PeriodosReport } from './_components/PeriodosReport';
import { AnaliseAnualReport } from './_components/AnaliseAnualReport';
import { BandeiraFormaReport } from './_components/BandeiraFormaReport';
import { BandeiraFormaAnoReport } from './_components/BandeiraFormaAnoReport';

export default function AnaliseFiltradaPage() {
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [selectedProcessamento, setSelectedProcessamento] = useState<string>('');
  const [loadingProc, setLoadingProc] = useState(false);
  const [errorProc, setErrorProc] = useState<string | null>(null);

  useEffect(() => {
    fetchProcessamentos();
  }, []);

  const fetchProcessamentos = async () => {
    try {
      setLoadingProc(true);
      const data = await importacaoApi.processamentos.listar(undefined, undefined, true);
      setProcessamentos(data);
      if (data.length > 0 && !selectedProcessamento) {
        setSelectedProcessamento(String(data[0].id));
      }
    } catch (err) {
      console.error(err);
      setErrorProc('Erro ao carregar processamentos. Verifique a conexão com a API.');
    } finally {
      setLoadingProc(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 text-gray-700 border-b pb-2 mb-4">
        <Filter className="w-6 h-6 text-orange-500" />
        <h1 className="text-xl font-bold uppercase tracking-wide">Analista de Dados — Filtrados</h1>
      </div>

      <div className="bg-orange-50 border border-orange-200 text-orange-800 px-4 py-2 rounded text-sm">
        Exibindo dados provenientes das tabelas <strong>vendas_filtradas</strong> e <strong>recebiveis_filtrados</strong>.
      </div>

      {errorProc && <ErrorMessage message={errorProc} />}

      {/* Seleção de Processamento */}
      <Panel className="bg-gray-50 border-gray-300">
        <PanelBody className="p-3">
          <div className="flex flex-col md:flex-row items-center gap-4">
            <label className="font-bold text-gray-700 whitespace-nowrap">Processamento Importado:</label>
            <select
              className="flex-1 w-full max-w-[600px] border-gray-300 rounded-sm shadow-sm focus:border-orange-500 focus:ring-orange-500 h-9 text-sm truncate pr-8"
              value={selectedProcessamento}
              onChange={(e) => setSelectedProcessamento(e.target.value)}
              disabled={loadingProc}
            >
              <option value="">Selecione...</option>
              {processamentos.map(p => {
                const date = new Date(p.data_inicio).toLocaleDateString();
                const label = `${p.id} - ${p.tipo_arquivo} (${date}) - ${p.nome_arquivo}`;
                const truncated = label.length > 85 ? label.substring(0, 85) + '...' : label;
                return (
                  <option key={p.id} value={String(p.id)} title={label}>
                    {truncated}
                  </option>
                );
              })}
            </select>
            <Button onClick={fetchProcessamentos} size="sm" variant="primary" disabled={loadingProc}>
              {loadingProc ? 'Carregando...' : 'Carregar Processamento'}
            </Button>
          </div>
        </PanelBody>
      </Panel>

      {!selectedProcessamento ? (
        <div className="p-10 text-center border-2 border-dashed border-gray-300 rounded text-gray-500">
          Selecione um processamento acima para iniciar a análise dos filtrados.
        </div>
      ) : (
        <div className="bg-white border border-gray-300 rounded shadow-sm p-4 min-h-[500px]">
          <Tabs defaultValue="geral" className="w-full">
            <TabsList className="mb-4 bg-gray-100 p-1 rounded border border-gray-200">
              <TabsTrigger value="geral">Visão Geral</TabsTrigger>
              <TabsTrigger value="periodos">Períodos</TabsTrigger>
              <TabsTrigger value="anual">Análise Anual</TabsTrigger>
              <TabsTrigger value="recebiveis">Recebíveis</TabsTrigger>
            </TabsList>

            <TabsContent value="geral" className="space-y-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="border border-gray-200 rounded p-2">
                  <BandeirasReport processamentoId={selectedProcessamento} />
                </div>
                <div className="border border-gray-200 rounded p-2">
                  <FormasPagamentoReport processamentoId={selectedProcessamento} />
                </div>
              </div>
              <div className="border border-gray-200 rounded p-2">
                <BandeiraFormaReport processamentoId={selectedProcessamento} />
              </div>
            </TabsContent>

            <TabsContent value="periodos" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <PeriodosReport processamentoId={selectedProcessamento} tipo="mes" titulo="Mensal — Filtrado" />
                <PeriodosReport processamentoId={selectedProcessamento} tipo="trimestre" titulo="Trimestral — Filtrado" />
                <PeriodosReport processamentoId={selectedProcessamento} tipo="semestre" titulo="Semestral — Filtrado" />
                <PeriodosReport processamentoId={selectedProcessamento} tipo="ano" titulo="Anual — Filtrado" />
              </div>
            </TabsContent>

            <TabsContent value="anual" className="space-y-4">
              <AnaliseAnualReport processamentoId={selectedProcessamento} />
              <BandeiraFormaAnoReport processamentoId={selectedProcessamento} />
            </TabsContent>

            <TabsContent value="recebiveis">
              <RecebiveisReport processamentoId={selectedProcessamento} />
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}

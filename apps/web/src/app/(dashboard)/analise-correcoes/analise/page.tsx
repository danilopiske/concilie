/**
 * Página unificada de Análise - Estilo Legacy
 */

'use client';

import { useState, useEffect } from 'react';
import { Panel, PanelHeader, PanelBody } from '@/components/ui/Panel';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import { importacaoApi } from '@/lib/api/importacao';
import { Processamento } from '@/lib/types/importacao';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { BarChart3, Search } from 'lucide-react';

import { BandeirasReport } from './_components/BandeirasReport';
import { FormasPagamentoReport } from './_components/FormasPagamentoReport';
import { RecebiveisReport } from './_components/RecebiveisReport';
import { PeriodosReport } from './_components/PeriodosReport';
import { AnaliseAnualReport } from './_components/AnaliseAnualReport';
import { AbusividadeReport } from './_components/AbusividadeReport';

export default function AnalisePage() {
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
      if (data.length > 0) {
        if (!selectedProcessamento) {
           setSelectedProcessamento(String(data[0].id));
        }
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
      {/* Header Compacto */}
      <div className="flex items-center gap-2 text-gray-700 border-b pb-2 mb-4">
        <BarChart3 className="w-6 h-6" />
        <h1 className="text-xl font-bold uppercase tracking-wide">Analista de Dados</h1>
      </div>

      {errorProc && <ErrorMessage message={errorProc} />}

      {/* Seleção de Processamento - Estilo Legacy */}
      <Panel className="bg-gray-50 border-gray-300">
        <PanelBody className="p-3">
            <div className="flex flex-col md:flex-row items-center gap-4">
                <label className="font-bold text-gray-700 whitespace-nowrap">Processamento Importado:</label>
                <select
                    className="flex-1 w-full max-w-[600px] border-gray-300 rounded-sm shadow-sm focus:border-blue-500 focus:ring-blue-500 h-9 text-sm truncate pr-8"
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
             Selecione um processamento acima para iniciar a análise.
         </div>
      ) : (
          <div className="bg-white border border-gray-300 rounded shadow-sm p-4 min-h-[500px]">
              <Tabs defaultValue="geral" className="w-full">
                <TabsList className="mb-4 bg-gray-100 p-1 rounded border border-gray-200">
                  <TabsTrigger value="geral">Visão Geral</TabsTrigger>
                  <TabsTrigger value="periodos">Períodos</TabsTrigger>
                  <TabsTrigger value="anual">Análise Anual</TabsTrigger>
                  <TabsTrigger value="recebiveis">Recebíveis</TabsTrigger>
                  <TabsTrigger value="abusividade">Abusividade</TabsTrigger>
                </TabsList>

                <TabsContent value="geral" className="space-y-4">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {/* Envolver os reports em containers simples, pois eles já usam Card/Table */}
                      <div className="border border-gray-200 rounded p-2">
                        <BandeirasReport processamentoId={selectedProcessamento} />
                      </div>
                      <div className="border border-gray-200 rounded p-2">
                        <FormasPagamentoReport processamentoId={selectedProcessamento} />
                      </div>
                  </div>
                </TabsContent>

                <TabsContent value="periodos" className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <PeriodosReport processamentoId={selectedProcessamento} tipo="mes" titulo="Mensal" />
                        <PeriodosReport processamentoId={selectedProcessamento} tipo="trimestre" titulo="Trimestral" />
                        <PeriodosReport processamentoId={selectedProcessamento} tipo="semestre" titulo="Semestral" />
                        <PeriodosReport processamentoId={selectedProcessamento} tipo="ano" titulo="Anual" />
                    </div>
                </TabsContent>

                <TabsContent value="anual">
                   <AnaliseAnualReport processamentoId={selectedProcessamento} />
                </TabsContent>

                <TabsContent value="recebiveis">
                  <RecebiveisReport processamentoId={selectedProcessamento} />
                </TabsContent>

                <TabsContent value="abusividade">
                  <AbusividadeReport processamentoId={selectedProcessamento} />
                </TabsContent>
              </Tabs>
          </div>
      )}
    </div>
  );
}

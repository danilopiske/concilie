// ImportarVendasPage.tsx
// Tela principal de importação de vendas e recebíveis (unificados)

"use client";
import React from 'react';
import { Card } from '@/components/ui/Card';
import { Stepper } from '@/components/ui/Stepper';
import { FileUpload } from '@/components/ui/FileUpload';
import { Alert } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { Table } from '@/components/ui/Table';

export default function ImportarVendasPage() {
  // TODO: Implementar lógica de upload, validação, processamento e resultado
  // TODO: Integrar com backend real
  // TODO: Usar Design System corporativo

  // Estados de exemplo
  const [step, setStep] = React.useState(0);

  // Mock dados para selects (substituir por API real)
  const clientes = [
    { value: "5", label: "5 - ESTACIONAMENTO BATEL SHOPPING" },
    { value: "6", label: "6 - ESTACIONAMENTO SÃO JOSÉ" },
  ];
  const ecs = [
    { value: "", label: "" },
    { value: "123456", label: "123456" },
    { value: "654321", label: "654321" },
  ];
  const contextos = [
    { value: "Cielo", label: "Cielo" },
    { value: "Stone", label: "Stone" },
  ];
  const tiposArquivo = [
    { value: "Venda", label: "Venda" },
    { value: "Recebível", label: "Recebível" },
  ];
  const processamentosAnteriores = [
    { value: "96617268_0002", label: "96617268_0002 - 20/12/2025 10:33" },
  ];
  const arquivosProcessados: any[] = [];

  // Estados de UI
  const [cliente, setCliente] = React.useState("");
  const [ec, setEc] = React.useState("");
  const [contexto, setContexto] = React.useState("");
  const [tipoArquivo, setTipoArquivo] = React.useState("Venda");
  const [continuarAnterior, setContinuarAnterior] = React.useState(false);
  const [processamentoAnterior, setProcessamentoAnterior] = React.useState("");
  const [file, setFile] = React.useState<File | null>(null);
  const [processing, setProcessing] = React.useState(false);
  const [result, setResult] = React.useState<any>(null);
  const [error, setError] = React.useState<string | null>(null);

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
      {/* Tabs (apenas visual, navegação é feita pelo layout) */}


      {/* Filtros topo */}
      <Card>
        <div className="flex flex-wrap gap-4 mb-2">
          <div className="flex flex-col min-w-[220px]">
            <label className="font-label mb-1">Cliente</label>
            <select
              className="InputText w-full p-2 border border-gray-300 rounded bg-white text-gray-900"
              value={cliente}
              onChange={e => setCliente(e.target.value)}
              disabled={processing}
            >
              <option value="">Selecione</option>
              {clientes.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col min-w-[120px]">
            <label className="font-label mb-1">EC</label>
            <select
              className="InputText w-full p-2 border border-gray-300 rounded bg-white text-gray-900"
              value={ec}
              onChange={e => setEc(e.target.value)}
              disabled={processing}
            >
              <option value="">Selecione</option>
              {ecs.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col min-w-[180px]">
            <label className="font-label mb-1">Contexto (Layout)</label>
            <select
              className="InputText w-full p-2 border border-gray-300 rounded bg-white text-gray-900"
              value={contexto}
              onChange={e => setContexto(e.target.value)}
              disabled={processing}
            >
              <option value="">Selecione</option>
              {contextos.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col min-w-[140px]">
            <label className="font-label mb-1">Tipo de Arquivo</label>
            <select
              className="InputText w-full p-2 border border-gray-300 rounded bg-white text-gray-900"
              value={tipoArquivo}
              onChange={e => setTipoArquivo(e.target.value)}
              disabled={processing}
            >
              {tiposArquivo.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Opções de Processamento */}
        <div className="flex items-center gap-4 mb-4 mt-2">
          <input
            type="checkbox"
            id="continuarAnterior"
            checked={continuarAnterior}
            onChange={e => setContinuarAnterior(e.target.checked)}
            disabled={processing}
          />
          <label htmlFor="continuarAnterior" className="font-label mr-2">
            Continuar processamento anterior
          </label>
          <select
            className="InputText min-w-[260px] p-2 border border-gray-300 rounded bg-white text-gray-900"
            value={processamentoAnterior}
            onChange={e => setProcessamentoAnterior(e.target.value)}
            disabled={!continuarAnterior || processing}
          >
            <option value="">ProcessamentoID anterior</option>
            {processamentosAnteriores.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <Button variant="secondary" disabled={processing}>
            Atualizar Processamentos
          </Button>
        </div>

        {/* Área de upload e botões principais */}
        <div className="flex items-center gap-4 border rounded-md p-4 mb-4 bg-white">
          <div className="flex-1">
            <FileUpload
              accept=".csv,.xlsx"
              onFileSelect={setFile}
              selectedFile={file}
              loading={processing}
              disabled={processing}
            />
          </div>
          <div className="flex gap-2 flex-1 justify-end">
            <Button
              variant="primary"
              loading={processing}
              disabled={!file || processing}
            >
              Processar e Normalizar
            </Button>
            <Button
              variant="success"
              disabled={!file || processing}
            >
              Gravar no Banco
            </Button>
            <Button
              variant="secondary"
              disabled={processing}
            >
              Limpar Importação
            </Button>
          </div>
        </div>

        {/* Mensagem de erro/sucesso */}
        {error && <Alert variant="error">{error}</Alert>}
        {result && <Alert variant="success">{result}</Alert>}

        {/* Tabela de arquivos processados */}
        <div className="mt-6">
          <div className="font-label mb-2">Arquivos Processados:</div>
          <Table
            variant="simple"
            columns={[
              { key: "index", label: "index" },
              { key: "num", label: "#" },
              { key: "arquivo", label: "Arquivo" },
              { key: "linhas", label: "Linhas" },
              { key: "status", label: "Status" },
            ]}
            data={arquivosProcessados}
          />
          <div className="flex items-center gap-2 mt-2">
            <input type="checkbox" id="atualizarPreview" />
            <label htmlFor="atualizarPreview" className="font-label">Atualizar Preview</label>
          </div>
        </div>
      </Card>
    </div>
  );
}

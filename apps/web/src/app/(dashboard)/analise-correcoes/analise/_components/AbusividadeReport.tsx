
'use client';

import { useState, useEffect } from 'react';
import { abusividadeApi, AbusividadeItem } from '@/lib/api/abusividade';
import { Button, Table, Alert } from '@/components/ui';
import { Loading } from '@/components/shared/Loading';
import { FileDown, AlertTriangle, Image as ImageIcon, Copy, Check } from 'lucide-react';
import { formatCurrency } from '@/lib/utils/formatters';
import { toPng } from 'html-to-image';

interface AbusividadeReportProps {
  processamentoId: string;
}

export function AbusividadeReport({ processamentoId }: AbusividadeReportProps) {
  const [data, setData] = useState<AbusividadeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agrupamento, setAgrupamento] = useState<string>('hierarquico');
  const [tolerancia, setTolerancia] = useState<number>(0.0);

  useEffect(() => {
    if (processamentoId) {
      loadData();
    }
  }, [processamentoId, agrupamento, tolerancia]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await abusividadeApi.getAnalise(processamentoId, agrupamento, tolerancia);
      setData(result);
    } catch (err) {
      console.error(err);
      setError('Erro ao carregar análise de abusividade.');
    } finally {
      setLoading(false);
    }
  };

  // Helper to ensure we show at least one example of each distinct rate in the preview
  const getPreviewItems = (allItems: AbusividadeItem[]) => {
    const limit = 10;
    if (allItems.length <= limit) return allItems;

    const uniqueRates = new Set<number>();
    const preview: AbusividadeItem[] = [];
    const remaining: AbusividadeItem[] = [];

    // First pass: grab representatives for each rate
    for (const item of allItems) {
        if (!uniqueRates.has(item.taxa_aplicada)) {
            uniqueRates.add(item.taxa_aplicada);
            preview.push(item);
        } else {
            remaining.push(item);
        }
    }

    // Fill the rest
    const needed = limit - preview.length;
    if (needed > 0) {
        preview.push(...remaining.slice(0, needed));
    }

    // Re-sort by date to maintain timeline view
    return preview.sort((a, b) => new Date(a.data_venda).getTime() - new Date(b.data_venda).getTime());
  };

  const translateAgrupamento = (val: string) => {
      switch(val) {
          case 'hierarquico': return 'Análise Completa (Hierárquica)';
          case 'dia': return 'Diário';
          case '3dias': return 'A cada 3 dias';
          case 'semana': return 'Semanal';
          case 'mes': return 'Mensal';
          default: return val;
      }
  };

  const handleDownloadPNG = async (elementId: string, filename: string) => {
    const element = document.getElementById(elementId);
    if (!element) return;

    try {
        const dataUrl = await toPng(element, { backgroundColor: '#ffffff' });
        const link = document.createElement('a');
        link.download = `${filename}.png`;
        link.href = dataUrl;
        link.click();
    } catch (err) {
        console.error('Error generating PNG:', err);
        alert('Erro ao gerar imagem PNG.');
    }
  };

  const handleCopyTable = (items: AbusividadeItem[]) => {
    // Create a temporary HTML table for the clipboard
    const tableHTML = `
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Cód. Aut.</th>
                    <th>Valor</th>
                    <th>Taxa Aplicada</th>
                    <th>Máquina</th>
                    <th>Bandeira</th>
                </tr>
            </thead>
            <tbody>
                ${items.map(item => `
                    <tr>
                        <td>${new Date(item.data_venda).toLocaleDateString()}</td>
                        <td>${item.cod_autorizacao}</td>
                        <td>${formatCurrency(item.valor_venda)}</td>
                        <td style="color: red; font-weight: bold;">${item.taxa_aplicada.toFixed(2)}%</td>
                        <td>${item.numero_maquina}</td>
                        <td>${item.bandeira}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    const blob = new Blob([tableHTML], { type: 'text/html' });
    const textBlob = new Blob([items.map(i => `${new Date(i.data_venda).toLocaleDateString()}\\t${i.cod_autorizacao}\\t${formatCurrency(i.valor_venda)}\\t${i.taxa_aplicada.toFixed(2)}%`).join('\\n')], { type: 'text/plain' });

    try {
        const data = [new ClipboardItem({ 
            "text/html": blob,
            "text/plain": textBlob 
        })];
        navigator.clipboard.write(data);
        alert('Tabela copiada! Cole no Word ou Excel.');
    } catch (err) {
        console.error('Clipboard error:', err);
        // Fallback
        navigator.clipboard.writeText(items.map(i => `${new Date(i.data_venda).toLocaleDateString()}\\t${i.cod_autorizacao}\\t${formatCurrency(i.valor_venda)}\\t${i.taxa_aplicada.toFixed(2)}%`).join('\\n'));
        alert('Tabela copiada (texto simples).');
    }
  };

  // Group data by 'chave_agrupamento' to create blocks for UI
  const groupedData = data.reduce((acc, item) => {
    const key = item.chave_agrupamento;
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {} as Record<string, AbusividadeItem[]>);

  if (loading) return <Loading message="Analisando taxas..." />;
  
  if (error) return <Alert variant="error">{error}</Alert>;

  return (
    <div className="space-y-6">
        
        {/* Subtle Toolbar for Tolerance */}
        <div className="flex justify-end items-center gap-2 -mb-4">
             <span className="text-xs text-gray-500 uppercase font-semibold">Filtro de Relevância:</span>
             <label className="flex items-center gap-2 bg-white px-3 py-1 rounded-full border shadow-sm text-sm text-gray-700">
                <span>Ignorar diferenças menores que:</span>
                <div className="relative flex items-center w-20">
                    <input 
                        type="number" 
                        step="0.01" 
                        min="0"
                        value={tolerancia}
                        onChange={(e) => setTolerancia(parseFloat(e.target.value) || 0)}
                        className="w-full text-right bg-transparent border-none focus:ring-0 p-0 font-bold text-blue-600"
                    />
                    <span className="ml-1 text-gray-400">%</span>
                </div>
             </label>
        </div>

        {data.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-green-300 rounded-lg bg-green-50 text-green-700">
                <div className="bg-green-100 p-3 rounded-full mb-4">
                    <FileDown className="w-8 h-8 text-green-600" /> 
                </div>
                <h3 className="text-xl font-bold mb-2">Nenhuma Abusividade Detectada</h3>
                <p className="max-w-md">
                    Não foram encontradas variações de taxa na janela "<strong>{translateAgrupamento(agrupamento)}</strong>" maiores que <strong>{tolerancia}%</strong>.
                </p>
            </div>
        ) : (
            <>
                <div className="flex justify-between items-center bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                    <div className="flex items-center gap-3">
                        <div className="bg-yellow-100 p-2 rounded-full">
                            <AlertTriangle className="text-yellow-600 w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="font-bold text-yellow-800 text-lg">Variações de Taxa Detectadas</h3>
                            <p className="text-sm text-yellow-700">
                                Detectamos {Object.keys(groupedData).length} grupos de transações com divergência &gt; {tolerancia}%.
                            </p>
                        </div>
                    </div>
                </div>
            </>
        )}

        {Object.entries(groupedData).map(([key, items], index) => {
            const first = items[0]; // Reference for header info
            const headerDate = new Date(first.data_venda).toLocaleDateString();
            
            // Get unique rates for this block to display in header
            const uniqueRates = Array.from(new Set(items.map(i => i.taxa_aplicada))).sort().map(r => `${r.toFixed(2)}%`).join(' vs ');
            
            const previewItems = getPreviewItems(items);
            
            
            const elementId = `abusividade-block-${index}`;

            return (
                <div id={elementId} key={key} className="border rounded-lg bg-white shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-500" style={{ animationDelay: `${index * 100}ms` }}>
                    <div className="bg-gray-50 px-4 py-3 border-b flex justify-between items-center">
                        <div className="flex items-center gap-2">
                             <span className="font-mono text-xs bg-gray-200 px-2 py-1 rounded text-gray-600">ID: {index + 1}</span>
                             <h4 className="font-semibold text-gray-800">
                                {headerDate} - <span className="text-blue-600">{first.bandeira}</span> - {first.forma_pagamento}
                             </h4>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="text-sm font-medium text-red-600 bg-red-50 px-3 py-1 rounded-full border border-red-100">
                                Variação: {uniqueRates}
                            </div>
                            <div className="flex gap-1" data-html2canvas-ignore>
                                <Button 
                                    variant="text" 
                                    size="sm" 
                                    onClick={() => handleCopyTable(previewItems)}
                                    title="Copiar tabela para Word/Excel"
                                    className="h-8 px-2 text-gray-500 hover:text-blue-600"
                                >
                                    <Copy className="w-4 h-4" />
                                </Button>
                                <Button 
                                    variant="text" 
                                    size="sm" 
                                    onClick={() => handleDownloadPNG(elementId, `abusividade-${index+1}`)}
                                    title="Baixar imagem PNG"
                                    className="h-8 px-2 text-gray-500 hover:text-green-600"
                                >
                                    <ImageIcon className="w-4 h-4" />
                                </Button>
                            </div>
                        </div>
                    </div>
                    
                    <div className="p-0">
                        <Table 
                            columns={[
                                { key: 'data_venda', label: 'Data', render: (v) => new Date(v).toLocaleDateString() },
                                { key: 'cod_autorizacao', label: 'Cód. Aut.' },
                                { key: 'valor_venda', label: 'Valor', render: (v) => formatCurrency(v) },
                                { 
                                    key: 'taxa_aplicada', 
                                    label: 'Taxa Aplicada', 
                                    render: (v) => <span className="font-bold text-gray-900">{Number(v).toFixed(2)}%</span> 
                                },
                                { key: 'numero_maquina', label: 'Máquina' },
                            ]}
                            data={previewItems}
                            variant="simple"
                        />
                        {items.length > 10 && (
                            <div className="bg-gray-50 px-4 py-2 text-xs text-center text-gray-500 border-t">
                                Exibindo {previewItems.length} de {items.length} ocorrências. (Amostra inclui todas as variações).
                            </div>
                        )}
                    </div>
                </div>
            );
        })}
    </div>
  );
}

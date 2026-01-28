
'use client';

import { useState, useEffect } from 'react';
import { abusividadeApi, AbusividadeItem } from '@/lib/api/abusividade';
import { Button, Table, Alert } from '@/components/ui';
import { Loading } from '@/components/shared/Loading';
import { FileDown, AlertTriangle } from 'lucide-react';
import { formatCurrency } from '@/lib/utils/formatters';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

interface AbusividadeReportProps {
  processamentoId: string;
}

export function AbusividadeReport({ processamentoId }: AbusividadeReportProps) {
  const [data, setData] = useState<AbusividadeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agrupamento, setAgrupamento] = useState<string>('hierarquico');

  useEffect(() => {
    if (processamentoId) {
      loadData();
    }
  }, [processamentoId, agrupamento]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await abusividadeApi.getAnalise(processamentoId, agrupamento);
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

  const generatePDF = () => {
    if (data.length === 0) return;

    const doc = new jsPDF();
    
    // Header
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.text("Demonstrativo de oscilações na aplicação de taxas", 105, 20, { align: 'center' });
    
    // Subinfo
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(`Processamento: ${processamentoId}`, 105, 30, { align: 'center' });
    doc.text(`Janela de Análise: ${translateAgrupamento(agrupamento)}`, 105, 35, { align: 'center' });

    // Body Text
    doc.setFontSize(10);
    const text = "De maneira ainda mais prejudicial, apresentamos demonstração detalhada, fundamentada em informações extraídas diretamente dos extratos, dados identificados por meio de auditoria sistêmica e tecnicamente especializada.";
    const splitText = doc.splitTextToSize(text, 180);
    doc.text(splitText, 15, 50);

    const text2 = "Constatou-se que a Adquirente aplicou taxas diferentes sobre a mesma bandeira e modalidade no mesmo período, evidenciando inconsistência.";
    const splitText2 = doc.splitTextToSize(text2, 180);
    doc.text(splitText2, 15, 65);

    let finalY = 80;

    // Group data for PDF
    const groupedDataPDF = data.reduce((acc, item) => {
        const key = item.chave_agrupamento;
        if (!acc[key]) acc[key] = [];
        acc[key].push(item);
        return acc;
    }, {} as Record<string, AbusividadeItem[]>);

    Object.values(groupedDataPDF).forEach((items, index) => {
        const previewItems = getPreviewItems(items);
        const first = items[0];
        const uniqueRates = Array.from(new Set(items.map(i => i.taxa_aplicada))).sort().map(r => `${r.toFixed(2)}%`).join(' vs ');
        
        // Check for page break
        if (finalY > 250) {
            doc.addPage();
            finalY = 20;
        }

        // Block Header
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(0, 0, 0);
        const title = `${new Date(first.data_venda).toLocaleDateString()} - ${first.bandeira} - ${first.forma_pagamento}`;
        doc.text(title, 15, finalY);
        
        doc.setFontSize(10);
        doc.setTextColor(200, 0, 0);
        doc.text(`Variação: ${uniqueRates}`, 15, finalY + 5);
        
        // Table
        const tableData = previewItems.map(row => [
            new Date(row.data_venda).toLocaleDateString(),
            row.cod_autorizacao,
            formatCurrency(row.valor_venda),
            `${row.taxa_aplicada.toFixed(2)}%`,
            row.numero_maquina,
            row.bandeira
        ]);

        autoTable(doc, {
            startY: finalY + 8,
            head: [['DATA', 'CÓD. AUT.', 'VALOR', 'TAXA', 'Nº MÁQUINA', 'BANDEIRA']],
            body: tableData,
            theme: 'grid',
            headStyles: { fillColor: [240, 240, 240], textColor: [0, 0, 0], fontStyle: 'bold' },
            styles: { fontSize: 8, cellPadding: 2 },
            columnStyles: {
                3: { textColor: [200, 0, 0], fontStyle: 'bold' }
            },
            margin: { top: 20 } // Ensure margin works on new pages
        });

        // Update Y for next block (autotable attaches finalY to the specific call instance but we can access it via lastAutoTable)
        finalY = (doc as any).lastAutoTable.finalY + 15;
    });

    doc.save(`demonstrativo_abusividade_${processamentoId}.pdf`);
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


        {data.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-green-300 rounded-lg bg-green-50 text-green-700">
                <div className="bg-green-100 p-3 rounded-full mb-4">
                    <FileDown className="w-8 h-8 text-green-600" /> 
                </div>
                <h3 className="text-xl font-bold mb-2">Nenhuma Abusividade Detectada</h3>
                <p className="max-w-md">
                    Não foram encontradas variações de taxa na janela "<strong>{translateAgrupamento(agrupamento)}</strong>".
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
                                Detectamos {Object.keys(groupedData).length} grupos de transações com divergência de taxas.
                            </p>
                        </div>
                    </div>
                    <Button onClick={generatePDF} variant="primary" className="flex items-center gap-2">
                        <FileDown className="w-4 h-4" /> Baixar PDF Laudo
                    </Button>
                </div>
            </>
        )}

        {Object.entries(groupedData).map(([key, items], index) => {
            const first = items[0]; // Reference for header info
            const headerDate = new Date(first.data_venda).toLocaleDateString();
            
            // Get unique rates for this block to display in header
            const uniqueRates = Array.from(new Set(items.map(i => i.taxa_aplicada))).sort().map(r => `${r.toFixed(2)}%`).join(' vs ');
            
            const previewItems = getPreviewItems(items);
            
            return (
                <div key={key} className="border rounded-lg bg-white shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-500" style={{ animationDelay: `${index * 100}ms` }}>
                    <div className="bg-gray-50 px-4 py-3 border-b flex justify-between items-center">
                        <div className="flex items-center gap-2">
                             <span className="font-mono text-xs bg-gray-200 px-2 py-1 rounded text-gray-600">ID: {index + 1}</span>
                             <h4 className="font-semibold text-gray-800">
                                {headerDate} - <span className="text-blue-600">{first.bandeira}</span> - {first.forma_pagamento}
                             </h4>
                        </div>
                        <div className="text-sm font-medium text-red-600 bg-red-50 px-3 py-1 rounded-full border border-red-100">
                            Variação: {uniqueRates}
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
                                Exibindo {previewItems.length} de {items.length} ocorrências. (Amostra inclui todas as variações). Baixe o PDF para ver todas.
                            </div>
                        )}
                    </div>
                </div>
            );
        })}
    </div>
  );
}


'use client';

import { useState } from 'react';
import { useClientes } from '@/lib/hooks/useClientes';
import { useECs } from '@/lib/hooks/useECs';
import { abusividadeApi, AbusividadeItem } from '@/lib/api/abusividade';
import { Button, Table, TableColumn, Alert, Card } from '@/components/ui';
import { Select } from '@/components/ui/Select';
import { Input } from '@/components/ui/Input';
import { Loading } from '@/components/shared/Loading';
import { Breadcrumb } from '@/components/layout';
import { formatCurrency } from '@/lib/utils/formatters';
import { FileDown, Search } from 'lucide-react';

export default function RelatorioAbusividadePage() {
  const [clienteId, setClienteId] = useState<number | null>(null);
  const [ecId, setEcId] = useState('');
  const [dataIni, setDataIni] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [agrupamento, setAgrupamento] = useState('dia');
  
  const [reportData, setReportData] = useState<AbusividadeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const { clientes, loading: loadingClientes } = useClientes();
  const { ecs, loading: loadingECs } = useECs(clienteId);

  const handleSearch = async () => {
    if (!clienteId || !dataIni || !dataFim) {
      setError('Selecione Cliente e Período para gerar o relatório.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const data = await abusividadeApi.getRelatorio({
        cliente_id: clienteId,
        ec_id: ecId || undefined,
        data_ini: dataIni,
        data_fim: dataFim,
        agrupamento
      });

      setReportData(data);
      setSearched(true);
    } catch (err: unknown) {
        console.error(err);
        setError('Erro ao gerar relatório. Verifique os filtros e tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const columns: TableColumn<AbusividadeItem>[] = [
    { key: 'data_venda', label: 'Data', render: (v) => new Date(v).toLocaleDateString() },
    { key: 'cod_autorizacao', label: 'Cód. Autorização' },
    { key: 'horario', label: 'Horário' },
    { key: 'valor_venda', label: 'Valor', render: (v) => formatCurrency(v) },
    { 
        key: 'taxa_aplicada', 
        label: 'Taxa Descontada', 
        render: (v) => <span className="font-bold text-red-600">{Number(v).toFixed(2)}%</span> 
    },
    { key: 'numero_maquina', label: 'Nº da Máquina', render: (v) => v || '-' }, // Placeholder
    { key: 'bandeira', label: 'Bandeira' }
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-10">
      <Breadcrumb items={[{ label: 'Relatórios', href: '/relatorios' }, { label: 'Demonstrativo de Abusividade' }]} />
      
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
           <h1 className="text-2xl font-bold text-gray-900">Demonstrativo de Oscilações na Aplicação de Taxas</h1>
           <p className="text-sm text-gray-600">Identifique variações de taxas para a mesma bandeira/modalidade.</p>
        </div>
      </div>

      {error && <Alert variant="error" onClose={() => setError(null)}>{error}</Alert>}

      <Card>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 items-end">
          
          <Select 
            label="Cliente" 
            value={clienteId || ''} 
            onChange={(e) => { setClienteId(Number(e.target.value)); setEcId(''); }} 
            options={clientes.map(c => ({ 
              value: c.cliente_id, 
              label: c.nome_fantasia || `Cliente ${c.cliente_id}` 
            }))}
            disabled={loadingClientes}
            placeholder="Selecione..."
          />
          
          <Select 
            label="Estabelecimento (EC)" 
            value={ecId} 
            onChange={(e) => setEcId(e.target.value)}
            options={ecs.map(e => ({ value: e, label: e }))}
            disabled={!clienteId || loadingECs}
            placeholder="Todos"
          />

          <div className="flex gap-2">
             <div className="flex-1">
                <Input label="Data Início" type="date" value={dataIni} onChange={e => setDataIni(e.target.value)} />
             </div>
             <div className="flex-1">
                <Input label="Data Fim" type="date" value={dataFim} onChange={e => setDataFim(e.target.value)} />
             </div>
          </div>

          <Select
            label="Agrupamento"
            value={agrupamento}
            onChange={(e) => setAgrupamento(e.target.value)}
            options={[
                { value: 'dia', label: 'Diário' },
                // { value: 'semana', label: 'Semanal (TODO)' }, 
                { value: 'mes', label: 'Mensal' },
                { value: 'periodo_total', label: 'Período Total' }
            ]}
          />

          <Button onClick={handleSearch} disabled={loading} className="w-full">
            {loading ? 'Gerando...' : 'Gerar Relatório'}
          </Button>

        </div>
      </Card>

      {searched && (
          <Card>
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Resultados</h3>
                <span className="text-sm text-gray-500">{reportData.length} ocorrências encontradas</span>
            </div>
            
            <div className="overflow-x-auto">
                {reportData.length === 0 ? (
                    <div className="text-center py-10 text-gray-500">
                        Nenhuma variação de taxa encontrada para o período e filtros selecionados.
                    </div>
                ) : (
                    <Table 
                        columns={columns} 
                        data={reportData} 
                        variant="simple"
                    />
                )}
            </div>
          </Card>
      )}
    </div>
  );
}

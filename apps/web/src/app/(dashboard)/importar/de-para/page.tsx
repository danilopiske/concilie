'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Table, TableColumn } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { Breadcrumb } from '@/components/layout';
import { deparaApi } from '@/lib/api/depara';
import { contextosApi, Contexto } from '@/lib/api/contextos';
import { DeParaRule, DeParaCreate } from '@/lib/types/importacao';
import { DeParaFormModal } from '@/components/importar/DeParaFormModal';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';

export default function DeParaPage() {
  const [data, setData] = useState<DeParaRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedRule, setSelectedRule] = useState<DeParaRule | null>(null);
  const [contextos, setContextos] = useState<Contexto[]>([]);
  const [filters, setFilters] = useState({
    search: '',
    contexto: '',
    tipo_origem: '',
    ativo: '1'
  });

  const fetchRules = async () => {
    try {
      setLoading(true);
      const res = await deparaApi.listar({
        search: filters.search,
        contexto: filters.contexto,
        tipo_origem: filters.tipo_origem,
        ativo: filters.ativo !== '' ? parseInt(filters.ativo) : undefined
      });
      setData(res);
    } catch (err) {
      setError('Erro ao carregar regras De-Para');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    contextosApi.listar().then(setContextos).catch(console.error);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
        fetchRules();
    }, 300); // Debounce
    return () => clearTimeout(timer);
  }, [filters]);

  const handleOpenModal = (rule?: DeParaRule) => {
    setSelectedRule(rule || null);
    setIsModalOpen(true);
  };

  const handleSave = async (formData: DeParaCreate) => {
    try {
      if (selectedRule) {
        await deparaApi.atualizar(selectedRule.id, formData);
      } else {
        await deparaApi.criar(formData);
      }
      fetchRules();
    } catch (err: unknown) {
      alert((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao salvar');
      throw err;
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Deseja realmente excluir esta regra?')) return;
    try {
        await deparaApi.deletar(id);
        fetchRules();
    } catch (err) {
        alert('Erro ao excluir');
    }
  };

  const columns: TableColumn<DeParaRule>[] = [
    { key: 'contexto', label: 'Contexto' },
    { key: 'tipo_origem', label: 'Tipo' },
    { key: 'destino_nome', label: 'Destino (Sistema)' },
    { key: 'origem_nome', label: 'Origem (Arquivo)' },
    { key: 'tipo_preenchimento', label: 'Preenchimento' },
    { key: 'ativo', label: 'Ativo', format: 'badge' },
    {
      key: 'actions',
      label: 'Ações',
      render: (_, row) => (
        <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => handleOpenModal(row)}>
              Editar
            </Button>
            <Button size="sm" variant="danger" onClick={() => handleDelete(row.id)}>
              Excluir
            </Button>
        </div>
      )
    }
  ];

  return (
    <div className="max-w-7xl mx-auto pb-10">
      <Breadcrumb
        items={[
          { label: 'Importar', href: '/importar/vendas' },
          { label: 'De-Para de Colunas' },
        ]}
      />
      <div className="flex justify-between items-center mb-6">
        <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">De-Para de Colunas</h1>
            <p className="text-gray-500">Gerencie as regras de mapeamento de importação.</p>
        </div>
        <Button onClick={() => handleOpenModal()}>
          + Nova Regra
        </Button>
      </div>
      
      <Card className="p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Input 
                placeholder="Buscar regra..." 
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            />
            <Select 
                placeholder="Todos os Contextos"
                value={filters.contexto}
                onChange={(e) => setFilters(prev => ({ ...prev, contexto: e.target.value }))}
                options={[
                    { value: '', label: 'Todos os Contextos' },
                    ...contextos.map(ctx => ({ value: ctx.nome, label: ctx.nome }))
                ]}
            />
            <Select 
                placeholder="Todos os Tipos"
                value={filters.tipo_origem}
                onChange={(e) => setFilters(prev => ({ ...prev, tipo_origem: e.target.value }))}
                options={[
                    { value: '', label: 'Todos os Tipos' },
                    { value: 'V', label: '🛒 Vendas' },
                    { value: 'R', label: '💰 Recebíveis' },
                    { value: 'L', label: '📝 Lançamentos' }
                ]}
            />
            <Select 
                placeholder="Status"
                value={filters.ativo}
                onChange={(e) => setFilters(prev => ({ ...prev, ativo: e.target.value }))}
                options={[
                    { value: '', label: 'Todos os Status' },
                    { value: '1', label: '✅ Ativo' },
                    { value: '0', label: '❌ Inativo' }
                ]}
            />
        </div>
      </Card>

      {error && <ErrorMessage message={error} />}

      <Card>
          <Table
            columns={columns}
            data={data}
            loading={loading}
            emptyMessage="Nenhuma regra encontrada."
          />
      </Card>

      <DeParaFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSave}
        initialData={selectedRule}
      />
    </div>
  );
}

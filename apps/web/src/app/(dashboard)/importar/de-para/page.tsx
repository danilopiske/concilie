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
import { DeParaRule, DeParaCreate } from '@/lib/types/importacao';
import { DeParaFormModal } from '@/components/importar/DeParaFormModal';

export default function DeParaPage() {
  const [data, setData] = useState<DeParaRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedRule, setSelectedRule] = useState<DeParaRule | null>(null);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const res = await deparaApi.listar();
      setData(res);
    } catch (err) {
      setError('Erro ao carregar regras De-Para');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

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
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Erro ao salvar');
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
            <Button size="sm" variant="text" onClick={() => handleOpenModal(row)}>
            ✏️ Editar
            </Button>
            <Button size="sm" variant="text" className="text-red-600" onClick={() => handleDelete(row.id)}>
            🗑️ Excluir
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

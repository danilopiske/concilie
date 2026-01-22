/**
 * Tabela de Clientes
 * Conversão do widget tabela do Panel (ui_gestao.py)
 */
'use client';

import { Cliente } from '@/lib/types/gestao';
import { formatCPFCNPJ } from '@/lib/utils/formatters';
import { Button } from '@/components/ui/Button';
import { Table, TableColumn } from '@/components/ui/Table';

interface ClientesTableProps {
  clientes: Cliente[];
  onEdit: (cliente: Cliente) => void;
  onDelete: (clienteId: number) => void;
  onViewECs: (clienteId: number) => void;
}

export function ClientesTable({ clientes, onEdit, onDelete, onViewECs }: ClientesTableProps) {
  const columns: TableColumn<Cliente>[] = [
    {
      key: 'cliente_id',
      label: 'ID',
      width: '80px',
    },
    {
      key: 'nome',
      label: 'Nome/Razão Social',
      render: (_, cliente) => cliente.razao_social || cliente.nome_fantasia || '-',
    },
    {
      key: 'cnpj',
      label: 'CPF/CNPJ',
      render: (cnpj) => formatCPFCNPJ(cnpj),
    },
    {
      key: 'tipo',
      label: 'Tipo',
      render: (_, cliente) => (cliente.cnpj && cliente.cnpj.replace(/\D/g, '').length === 14 ? 'Jurídica' : 'Física'),
    },
    {
      key: 'status',
      label: 'Status',
      render: () => (
        // TODO: Implementar status real quando disponível na API
        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
          Ativo
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Ações',
      width: '250px',
      render: (_, cliente) => (
        <div className="flex justify-end gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => onViewECs(cliente.cliente_id)}
          >
            ECs
          </Button>
          <Button
            size="sm"
            variant="primary"
            onClick={() => onEdit(cliente)}
          >
            Editar
          </Button>
          <Button
            size="sm"
            variant="danger"
            onClick={() => onDelete(cliente.cliente_id)}
          >
            Excluir
          </Button>
        </div>
      ),
    },
  ];

  return (
    <Table
      data={clientes}
      columns={columns}
      emptyMessage="Nenhum cliente cadastrado"
    />
  );
}

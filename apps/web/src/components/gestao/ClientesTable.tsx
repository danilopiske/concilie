/**
 * Tabela de Clientes
 * Conversão do widget tabela do Panel (ui_gestao.py)
 */
'use client';

import Link from 'next/link';
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
      label: 'Nome Fantasia',
      render: (_, cliente) => cliente.nome_fantasia || cliente.razao_social || '-',
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
        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
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
          <Link
            href={`/gestao/clientes/${cliente.cliente_id}/taxas-contratadas`}
            className="inline-flex items-center px-2.5 py-1.5 text-xs font-medium rounded border border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
          >
            Taxas
          </Link>
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

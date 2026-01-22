/**
 * Tabela de Clientes
 * Conversão do widget tabela do Panel (ui_gestao.py)
 */
'use client';

import { Cliente } from '@/lib/types/gestao';
import { formatCPFCNPJ } from '@/lib/utils/formatters';
import { Button } from '@/components/ui/Button';

interface ClientesTableProps {
  clientes: Cliente[];
  onEdit: (cliente: Cliente) => void;
  onDelete: (clienteId: number) => void;
  onViewECs: (clienteId: number) => void;
}

export function ClientesTable({ clientes, onEdit, onDelete, onViewECs }: ClientesTableProps) {
  if (clientes.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        Nenhum cliente cadastrado
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              ID
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Nome/Razão Social
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              CPF/CNPJ
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Tipo
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Status
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Ações
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {clientes.map((cliente) => (
            <tr
              key={cliente.cliente_id}
              className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                {cliente.cliente_id}
              </td>
              <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                {cliente.razao_social || cliente.nome_fantasia || '-'}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                {formatCPFCNPJ(cliente.cnpj)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                {cliente.cnpj && cliente.cnpj.replace(/\D/g, '').length === 14 ? 'Jurídica' : 'Jurídica'}
              </td>
              <td className="px-4 py-3">
                <span
                  className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                >
                  Inativo
                </span>
              </td>
              <td className="px-4 py-3 text-right text-sm space-x-2">
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
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
